"""Tests for the jina-reranker-api FastAPI service."""
from __future__ import annotations

from typing import Any

import httpx
import pytest
from fastapi.testclient import TestClient

import config
import main

# Canned backend reply in the Cohere/LiteLLM rerank shape that main.py maps from.
_BACKEND_RESPONSE: dict[str, Any] = {
    "results": [
        {"index": 0, "relevance_score": 0.9},
        {"index": 2, "relevance_score": 0.4},
    ],
    "meta": {"billed_units": {"total_tokens": 42}},
}

_BACKEND_API_KEY = "backend-secret"

_REQUEST = {
    "query": "What is the capital of France?",
    "documents": ["Paris is the capital.", "Berlin is a city.", "Rome is a city."],
    "return_documents": True,
}


@pytest.fixture
def captured() -> dict[str, Any]:
    """Holds the outbound request the service makes to the backend."""
    return {}


def _build_client(
    monkeypatch: pytest.MonkeyPatch,
    captured: dict[str, Any],
    *,
    api_key: str = "",
) -> TestClient:
    monkeypatch.setenv("API_KEY", api_key)
    monkeypatch.setenv("RERANKER_API_KEY", _BACKEND_API_KEY)
    monkeypatch.setenv("RERANKER_BASE_URL", "http://backend:4000")
    monkeypatch.setenv("RERANKER_MODEL", "rerank-english-v3.0")
    # Settings are cached; rebuild them against the env this test just set.
    config.get_settings.cache_clear()

    async def fake_post(
        self: httpx.AsyncClient, url: str, **kwargs: Any
    ) -> httpx.Response:
        captured["url"] = url
        captured["headers"] = kwargs.get("headers")
        captured["json"] = kwargs.get("json")
        return httpx.Response(
            200, json=_BACKEND_RESPONSE, request=httpx.Request("POST", url)
        )

    monkeypatch.setattr(httpx.AsyncClient, "post", fake_post)
    return TestClient(main.app)


def test_health(monkeypatch: pytest.MonkeyPatch, captured: dict[str, Any]) -> None:
    with _build_client(monkeypatch, captured) as client:
        resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_rerank_open_when_no_api_key(
    monkeypatch: pytest.MonkeyPatch, captured: dict[str, Any]
) -> None:
    with _build_client(monkeypatch, captured, api_key="") as client:
        resp = client.post("/rerank", json=_REQUEST)
    assert resp.status_code == 200
    body = resp.json()
    assert body["model"] == "rerank-english-v3.0"
    assert body["object"] == "list"
    assert body["usage"]["total_tokens"] == 42
    assert [r["index"] for r in body["results"]] == [0, 2]
    # return_documents=True → the document is taken from the request at its index.
    assert body["results"][0]["document"] == {"text": "Paris is the capital."}


def test_rerank_requires_key_when_configured(
    monkeypatch: pytest.MonkeyPatch, captured: dict[str, Any]
) -> None:
    with _build_client(monkeypatch, captured, api_key="inbound-secret") as client:
        missing = client.post("/rerank", json=_REQUEST)
        wrong = client.post(
            "/rerank", json=_REQUEST, headers={"Authorization": "Bearer nope"}
        )
        ok = client.post(
            "/rerank",
            json=_REQUEST,
            headers={"Authorization": "Bearer inbound-secret"},
        )
    assert missing.status_code == 401
    assert wrong.status_code == 401
    assert ok.status_code == 200


def test_outbound_uses_backend_key_not_client_token(
    monkeypatch: pytest.MonkeyPatch, captured: dict[str, Any]
) -> None:
    with _build_client(monkeypatch, captured, api_key="inbound-secret") as client:
        resp = client.post(
            "/rerank",
            json=_REQUEST,
            headers={"Authorization": "Bearer inbound-secret"},
        )
    assert resp.status_code == 200
    # The backend is called with the service's own key, never the inbound one.
    assert captured["headers"]["Authorization"] == f"Bearer {_BACKEND_API_KEY}"
    assert captured["url"] == "http://backend:4000/rerank"
    # top_n was not in the request, so it must not be forwarded.
    assert "top_n" not in captured["json"]


def test_document_cap_truncates_excess(
    monkeypatch: pytest.MonkeyPatch, captured: dict[str, Any]
) -> None:
    monkeypatch.setenv("MAX_RERANK_DOCS", "2")
    request_no_return = {**_REQUEST, "return_documents": False}
    with _build_client(monkeypatch, captured) as client:
        resp = client.post("/rerank", json=request_no_return)
    assert resp.status_code == 200
    # Only the first 2 of the 3 documents in _REQUEST must reach the backend.
    assert len(captured["json"]["documents"]) == 2
    assert captured["json"]["documents"] == _REQUEST["documents"][:2]
