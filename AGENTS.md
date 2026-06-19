# jina-reranker-api — project context

This document provides structural and architectural context for contributors and automated tooling working in this repository.

---

## What this project does

jina-reranker-api is a lightweight FastAPI service that exposes a **Jina AI–compatible `/rerank` endpoint** backed by any OpenAI-compatible reranker backend (LiteLLM, vLLM, or similar). It allows any RAG pipeline or LLM orchestration tool that speaks the Jina AI reranker HTTP API to route reranking requests to any compatible backend, enabling model-agnostic cross-encoder reranking without client-side changes.

Incoming `POST /rerank` requests are optionally authenticated against a configured `API_KEY` (presented as `Authorization: Bearer <API_KEY>`); the request is then forwarded to the configured OpenAI-compatible backend — authenticated separately with `RERANKER_API_KEY` — and the response is mapped back to the Jina AI response schema (relevance scores, optional document return, usage stats).

---

## Repository layout

```
jina-reranker-api/
├── src/                    # FastAPI server (uv project, Python 3.11+)
│   ├── main.py             # Entry point; FastAPI app, /rerank and /health endpoints
│   ├── config.py           # pydantic-settings config (env / .env loading)
│   ├── pyproject.toml      # uv project config; ruff / mypy / pytest settings
│   ├── uv.lock             # Locked dependency set (tracked for reproducible builds)
│   └── .env.example        # Local-dev env vars with placeholder values
├── tests/                  # pytest suite (sibling to src/, excluded from the image)
├── docker/
│   ├── Dockerfile          # Multi-stage build: uv sync → slim runtime image
│   ├── docker-compose.yml  # Compose deployment (build context = repo root)
│   └── .env.example        # All required env vars with placeholder values
└── .github/                # Workflows, issue templates, PR template
```

The production server lives in `src/`. There is **no** virtual environment at the repository root.

---

## Architecture

### Request flow

```
HTTP client
  │  POST /rerank  Authorization: Bearer <API_KEY>   (optional)
  ▼
FastAPI app  (src/main.py)
  │  validates inbound API_KEY if configured
  │  maps Jina AI request schema → OpenAI-compatible rerank request
  │  authenticates to the backend with RERANKER_API_KEY
  ▼
OpenAI-compatible backend  (RERANKER_BASE_URL)
  │  routes to the configured reranker model
  ▼
FastAPI app
  │  maps backend response → Jina AI response schema
  ▼
HTTP client  {model, object, usage, results[]}
```

### Key endpoints

| Endpoint | Method | Purpose |
|---|---|---|
| `/rerank` | POST | Rerank documents by relevance to a query |
| `/health` | GET | Health check (returns `{"status": "ok"}`) |

---

## Engineering conventions

### Branches

| Prefix | Use |
|---|---|
| `feat/<short>` | New user-facing feature |
| `fix/<short>` | Bug fix |
| `docs/<short>` | Documentation only |
| `refactor/<short>` | Refactoring without behaviour change |
| `test/<short>` | Test additions or fixes |
| `ci/<short>` | CI/CD configuration |
| `chore/<short>` | Maintenance |

Never push directly to `main`; always open a pull request.

### PR titles — Conventional Commits

Format: `<type>[(<scope>)][!]: <subject>`

- Subject: lowercase, imperative mood, no trailing period
- `!` suffix marks a breaking change (triggers a major version bump)
- CI enforces this format on every PR via `amannn/action-semantic-pull-request`

Examples: `feat: add top-n parameter`, `fix(rerank): handle empty results from backend`, `docs: document env vars`

### Merge strategy

All PRs are **squash-merged**. The PR title becomes the single commit message on `main`.

Development commits on feature branches may be informal (`wip`, `tmp`, etc.) — they are squashed away.

---

## Code style and local checks

Run all checks locally before pushing:

```bash
# YAML — from the repository root
yamllint .

# Python — from src/
cd src
uv run ruff check .
```

- **Python linting**: ruff; configuration in `src/pyproject.toml`
- **YAML**: yamllint with the project `.yamllint` config
- **Python version**: 3.11 minimum

---

## Configuration reference

All settings are loaded from environment variables. See `docker/.env.example` for the full list. The essential variables:

| Variable | Purpose |
|---|---|
| `API_KEY` | Inbound auth. When set, clients must send `Authorization: Bearer <API_KEY>`; empty ⇒ endpoint open |
| `RERANKER_BASE_URL` | Base URL of the OpenAI-compatible backend (default: `http://0.0.0.0:4000`) |
| `RERANKER_API_KEY` | Outbound auth: key this service uses to call the backend |
| `RERANKER_MODEL` | Model identifier forwarded to the backend (default: `rerank-english-v3.0`) |
| `PORT` | Port the service listens on (default: `8000`) |
| `LOG_LEVEL` | Logging level (default: `INFO`) |

---

## Security boundaries

- **Never log** the inbound `API_KEY`, Bearer tokens, or `RERANKER_API_KEY` values.
- The inbound `API_KEY` is compared in **constant time** (`secrets.compare_digest`).
- Inbound and outbound credentials are **independent**: the client's Bearer token is
  never forwarded to the backend; the backend always receives `RERANKER_API_KEY`.
- **Copyleft dependencies are not accepted.** The CI license-check workflow rejects GPL, LGPL, AGPL, EUPL, and similar licences. See `CONTRIBUTING.md` for the full list.
