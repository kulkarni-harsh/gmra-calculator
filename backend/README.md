# FastAPI Professional Backend Template

Production-focused FastAPI starter with clean structure, typed settings, SQLAlchemy async setup, and quality tooling.

## Features

- App factory pattern and versioned API routing
- Health endpoint: `GET /api/v1/health`
- Environment-based configuration with Pydantic Settings
- Async SQLAlchemy session management scaffold
- Pytest setup with API test example
- uv for dependency and environment management
- Ruff + MyPy + pre-commit
- Dockerfile + docker-compose (API + Postgres)

## Project Structure

```text
backend/
  app/
    api/v1/endpoints/
    core/
    db/
    models/
    schemas/
    services/
    main.py
  tests/
  pyproject.toml
  Dockerfile
  docker-compose.yml
```

## Quick Start

```bash
# install uv once (macOS): brew install uv
cd backend
cp .env.example .env
uv sync --dev
make run
```

Open: http://127.0.0.1:8000/docs

## Testing & Quality

```bash
make install
make test
make lint
make typecheck
```

## Add Dependencies

```bash
# runtime dependency
make add PKG="pandas"

# development-only dependency
make add-dev PKG="ipython"
```

## Docker

```bash
cd backend
cp .env.example .env
docker compose up --build
```
