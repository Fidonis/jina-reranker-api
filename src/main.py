"""Jina AI–compatible reranker API in front of an OpenAI-compatible backend."""
from __future__ import annotations

import logging
import secrets
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Annotated, Any

import httpx
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel

from config import get_settings

logger = logging.getLogger(__name__)

logging.basicConfig(level=get_settings().log_level.upper())


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    # One shared async client so connections are pooled across requests; closed
    # on shutdown to avoid leaking sockets.
    settings = get_settings()
    app.state.http_client = httpx.AsyncClient(timeout=settings.backend_timeout)
    try:
        yield
    finally:
        await app.state.http_client.aclose()


app = FastAPI(
    title="Jina AI Reranker Compatible API",
    description="A FastAPI implementation compatible with the Jina AI Reranker API",
    version="1.0.0",
    lifespan=lifespan,
)

# auto_error=False so a missing Authorization header does not 403 before we
# decide whether auth is required at all (it is optional — see require_api_key).
_bearer = HTTPBearer(auto_error=False)


def require_api_key(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
) -> None:
    """Enforce the inbound API key when one is configured.

    With ``api_key`` unset the endpoint is open. The comparison is constant-time
    so a wrong key cannot be recovered through response timing.
    """
    expected = get_settings().api_key
    if not expected:
        return
    if credentials is None or not secrets.compare_digest(
        credentials.credentials, expected
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key",
            headers={"WWW-Authenticate": "Bearer"},
        )


class RerankRequest(BaseModel):
    # The caller's ``model`` is accepted for Jina API compatibility but ignored:
    # the served model is fixed by configuration (see RerankResponse.model).
    model: str | None = None
    query: str
    documents: list[str]
    top_n: int | None = None
    return_documents: bool = False


class RerankResult(BaseModel):
    index: int
    relevance_score: float
    document: dict[str, Any] | None = None


class RerankResponse(BaseModel):
    model: str
    object: str
    usage: dict[str, int]
    results: list[RerankResult]


@app.post("/rerank", response_model=RerankResponse)
async def rerank_documents(
    request: RerankRequest,
    _: Annotated[None, Depends(require_api_key)],
) -> RerankResponse:
    """Rerank documents by relevance to a query (Jina AI–compatible)."""
    settings = get_settings()
    documents = request.documents[: settings.max_rerank_docs]

    payload: dict[str, Any] = {
        "model": settings.reranker_model,
        "query": request.query,
        "documents": documents,
    }
    if request.top_n is not None:
        payload["top_n"] = request.top_n

    headers = {"Content-Type": "application/json"}
    # Authenticate *this service* to the backend with its own configured key —
    # never the inbound client's credentials.
    if settings.reranker_api_key:
        headers["Authorization"] = f"Bearer {settings.reranker_api_key}"

    try:
        response = await app.state.http_client.post(
            f"{settings.reranker_base_url}/rerank",
            json=payload,
            headers=headers,
        )
        response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        # Surface the backend's status, but log the body server-side rather than
        # echoing it — it may contain internal detail or the backend's own errors.
        logger.warning("Backend rerank call failed: status=%s", exc.response.status_code)
        raise HTTPException(
            status_code=exc.response.status_code,
            detail="Rerank backend returned an error",
        ) from exc
    except httpx.HTTPError as exc:
        logger.warning("Backend rerank call errored: %s", type(exc).__name__)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Could not reach rerank backend",
        ) from exc

    result = response.json()
    total_tokens = result.get("meta", {}).get("billed_units", {}).get("total_tokens", 0)

    results: list[RerankResult] = []
    for i, item in enumerate(result.get("results", [])):
        index = item.get("index", i)
        rerank_result = RerankResult(
            index=index,
            relevance_score=item.get("relevance_score", 0.0),
        )
        if request.return_documents:
            rerank_result.document = {"text": documents[index]}
        results.append(rerank_result)

    return RerankResponse(
        model=settings.reranker_model,
        object="list",
        usage={"total_tokens": total_tokens},
        results=results,
    )


@app.get("/health")
async def health_check() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn

    _settings = get_settings()
    uvicorn.run(app, host=_settings.host, port=_settings.port)
