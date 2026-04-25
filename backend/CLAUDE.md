# Backend — Claude / Agent Notes

This file is for Claude Code and other AI agents working specifically inside `backend/`. The repo-root `.claude/CLAUDE.md` covers product context; this file covers backend conventions only.

## Stack

- Python 3.11, FastAPI, Pydantic v2, pandas, SQLAlchemy (async)
- Job runner: SQS-driven worker (`app/worker.py`), state in DynamoDB (`app/services/job_store.py`)
- Storage: S3 for reports + debug artifacts (`app/services/s3.py`)
- LLM: AWS Bedrock via langchain-aws (`app/services/bedrock_llm.py`)
- Payments: Stripe (`app/services/payment.py`), webhooks at `/api/payments/webhook/stripe`
- Email: Resend (`app/services/email.py`)
- External data: AlphaSophia (provider data), Census API, Mapbox, Google Places

## Layout

```
app/
  api/endpoints/     # FastAPI route handlers — keep thin, delegate to services
  core/              # config, logging, shared types
  schemas/           # Pydantic request/response models
  services/          # business logic + IO
  types/             # internal Pydantic domain models
  utils/             # pure helpers (no IO)
```

## Quality gates

```bash
make install      # uv sync --dev
make test         # pytest
make lint         # ruff check
make format       # ruff format
make pre-commit   # full ruff + mypy pass
```

Always run `make pre-commit` and `make test` before committing.

## Conventions

- **No `print()` in app code.** Use the standard `logging` module. Tests may use `print()` for debug, but prefer assertions.
- **No bare `except Exception` for business logic.** Catch the narrowest exception you can; if you must use a broad catch (e.g. webhook side effects), log with `exc_info=True`.
- **Schemas are immutable from the caller's perspective.** Build new objects rather than mutating Pydantic models in place.
- **All public functions have a docstring.** Module docstrings describe the file's responsibility in 1–3 sentences.
- **All async IO calls have timeouts.** httpx clients use explicit `httpx.Timeout`; boto3 calls inherit ECS task timeouts but should still log on failure.
- **Idempotency is non-negotiable for jobs.** `job_id` is the dedupe key. Webhooks and the synchronous `/generate` path race; `claim_job_for_generation` resolves the race.

## Where to put new code

| Kind of code | Location |
|---|---|
| New REST endpoint | `app/api/endpoints/<resource>.py`, register in `app/api/router.py` |
| New external API call | `app/services/<vendor>.py` |
| Pure data transform | `app/utils/<topic>.py` |
| New domain model | `app/types/<topic>.py` |
| New request/response schema | `app/schemas/<topic>.py` |
| New env var | `app/core/config.py`, also add to `.env.example` |

## Living docs to update on major changes

- `backend/docs/CHANGELOG.md` — one line per change
- `backend/docs/ARCHITECTURE.md` — when a new module/external dep/route is added
- `backend/docs/MODULES.md` — when a module's purpose or test coverage shifts

## Testing

- All public functions in `app/utils/` and `app/services/` should have unit tests.
- API endpoints get integration tests via `TestClient` from `app.main:app`.
- Mock boto3, stripe, resend, httpx at the module attribute level — see `tests/test_debug_artifacts.py` for the pattern.
- Pure-function tests (no IO) live in `tests/test_<topic>.py`. Service tests with mocks live in `tests/test_<service>.py`.
