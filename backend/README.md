# MREC Backend

FastAPI service that powers the MREC (Medical Estate Real Calculator) report pipeline.

## What it does

Two processes in one Docker image:

- **API** (`uvicorn app.main:app`) — accepts payment + report-job requests, lists specialties, returns job status.
- **Worker** (`python -m app.worker`) — long-polls SQS, generates HTML/PDF reports, uploads to S3, emails the customer.

For the request lifecycle and module map, see `docs/ARCHITECTURE.md` and `docs/MODULES.md`.

## Quick start

```bash
cd backend
cp .env.example .env       # fill in API keys (Census, Mapbox, AlphaSophia, Google, Stripe, Resend, AWS)
make install                # uv sync --dev
make run                    # uvicorn on :8000 — http://127.0.0.1:8000/docs
```

## Common commands

```bash
make test          # pytest
make lint          # ruff check
make format        # ruff format
make typecheck     # mypy app
make pre-commit    # full lint + format + mypy pass (run before every commit)
```

## Adding dependencies

```bash
make add PKG="<package>"        # runtime
make add-dev PKG="<package>"    # dev/test only
```

## Tests

`tests/` mirrors `app/` — one test file per module under test. Boto3, Stripe, Resend, and httpx are mocked at the module-attribute layer (see `tests/test_debug_artifacts.py` for the canonical pattern).

```bash
uv run pytest                                    # all
uv run pytest tests/test_payment_service.py -v   # one file
uv run pytest -k "fee_schedule"                  # by keyword
```

## Living documentation

- `CLAUDE.md` — guidance for AI agents working in this directory
- `docs/ARCHITECTURE.md` — system design + request flow
- `docs/MODULES.md` — per-module purpose + test coverage
- `docs/CHANGELOG.md` — append a one-liner whenever a meaningful change lands

## Local AWS (LocalStack)

Point `AWS_ENDPOINT_URL=http://localhost:4566` in `.env`. The init script in `../localstack-init/` provisions the bucket, table, and queue.

## Production

Deployed via `../deploy.sh` (ECS Fargate). See `../infra/` for CDK / Terraform once that lands.