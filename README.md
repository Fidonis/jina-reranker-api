# jina-reranker-api

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

A lightweight REST API that exposes a **Jina AI–compatible `/rerank` endpoint** backed by any OpenAI-compatible reranker backend. Drop it in front of LiteLLM, vLLM, or any other OpenAI-API-compatible service and your existing Jina AI reranker clients work without modification.

---

## How it works

```
RAG pipeline / LLM client
  │  POST /rerank  (Jina AI schema)
  ▼
jina-reranker-api  (FastAPI)
  │  token validation → backend request mapping
  ▼
OpenAI-compatible backend  (LiteLLM, vLLM, …)
  │  routes to configured reranker model
  ▼
jina-reranker-api
  │  maps response → Jina AI response schema
  ▼
RAG pipeline  {model, object, usage, results[]}
```

---

## Quick start

```bash
docker run -d \
  -p 8000:8000 \
  -e API_KEY=your-inbound-key \
  -e RERANKER_BASE_URL=http://your-backend:4000 \
  -e RERANKER_API_KEY=your-backend-key \
  -e RERANKER_MODEL=rerank-english-v3.0 \
  ghcr.io/fidonis/jina-reranker-api:latest
```

`API_KEY` is optional — omit it to run the endpoint unprotected (e.g. behind a
reverse proxy that already handles auth).

### Endpoints

| Endpoint | Method | Description |
|---|---|---|
| `/rerank` | POST | Rerank documents by relevance to a query |
| `/health` | GET | Health check |

### Example request

When `API_KEY` is set, pass it as the Bearer token (the same way LibreChat or any
Jina client sends its key); when unset, the `Authorization` header is optional.

```bash
curl -s http://localhost:8000/rerank \
  -H "Authorization: Bearer <your-API_KEY>" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "rerank-english-v3.0",
    "query": "What is the capital of France?",
    "documents": ["Paris is the capital.", "Berlin is the capital.", "Rome is a city."],
    "top_n": 2
  }'
```

---

## Authentication

The service has two independent credentials:

- **Inbound** (`API_KEY`) — protects this API. When set, clients must present it as
  `Authorization: Bearer <API_KEY>`; the value is compared in constant time. Leave it
  empty to run the endpoint open.
- **Outbound** (`RERANKER_API_KEY`) — the key this service uses to authenticate itself
  to the backend. It is never derived from the inbound request.

---

## Configuration

All settings are loaded from environment variables.

| Variable | Default | Description |
|---|---|---|
| `API_KEY` | — | **Inbound** auth. When set, clients must send `Authorization: Bearer <API_KEY>`. Empty ⇒ endpoint open. |
| `RERANKER_BASE_URL` | `http://0.0.0.0:4000` | Base URL of the OpenAI-compatible backend |
| `RERANKER_API_KEY` | — | **Outbound** auth: key this service uses to call the backend |
| `RERANKER_MODEL` | `rerank-english-v3.0` | Model identifier forwarded to the backend |
| `PORT` | `8000` | Port the service listens on |
| `LOG_LEVEL` | `INFO` | Logging level |

Copy `docker/.env.example` to `docker/.env` and adjust the values before running.

---

## Local development

```bash
cd src
uv sync
cp .env.example .env   # adjust as needed
uv run python main.py
```

---

## About Fidonis

[Fidonis](https://fidonis.de) builds and operates the **papAIa** self-hosted AI stack and maintains open-source companion services for it. `jina-reranker-api` is one of those companion services — designed to sit in front of any OpenAI-compatible reranker backend and expose a Jina AI–compatible interface.

---

## License

MIT — see [`LICENSE`](LICENSE).

Third-party dependency licenses are listed in [`THIRD_PARTY_LICENSES.md`](THIRD_PARTY_LICENSES.md) (auto-generated on every push to `main`).

"Fidonis" and "jina-reranker-api" are trademarks of Fidonis GmbH (in Gründung) — see [`TRADEMARK.md`](TRADEMARK.md).
