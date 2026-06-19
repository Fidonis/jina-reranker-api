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
  -e RERANKER_BASE_URL=http://your-backend:4000 \
  -e RERANKER_API_KEY=your-key \
  -e RERANKER_MODEL=rerank-english-v3.0 \
  ghcr.io/fidonis/jina-reranker-api:latest
```

### Endpoints

| Endpoint | Method | Description |
|---|---|---|
| `/rerank` | POST | Rerank documents by relevance to a query |
| `/health` | GET | Health check |

### Example request

```bash
curl -s http://localhost:8000/rerank \
  -H "Authorization: Bearer <your-token>" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "rerank-english-v3.0",
    "query": "What is the capital of France?",
    "documents": ["Paris is the capital.", "Berlin is the capital.", "Rome is a city."],
    "top_n": 2
  }'
```

---

## Configuration

All settings are loaded from environment variables.

| Variable | Default | Description |
|---|---|---|
| `RERANKER_BASE_URL` | `http://0.0.0.0:4000` | Base URL of the OpenAI-compatible backend |
| `RERANKER_API_KEY` | — | API key for the backend |
| `RERANKER_MODEL` | `rerank-english-v3.0` | Model identifier forwarded to the backend |

Copy `docker/.env.example` to `.env` and adjust the values before running.

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
