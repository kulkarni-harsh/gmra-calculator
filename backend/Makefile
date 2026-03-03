.PHONY: install lock run test lint format typecheck precommit add add-dev
PKG_ARG := $(or $(PKG),$(filter-out add add-dev,$(MAKECMDGOALS)))

install:
	uv sync --dev

lock:
	uv lock

run:
	uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

test:
	uv run pytest

lint:
	uv run ruff check .

format:
	uv run ruff format .

typecheck:
	uv run mypy app

pre-commit:
	uv run pre-commit run --all-files

add:
	uv add $(PKG_ARG)

# Allow `make add pandas` and `make add-dev pytest` without make trying to build those as targets.
%:
	@:
