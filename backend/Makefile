.PHONY: install run test lint format typecheck precommit

install:
	python -m pip install .[dev]

run:
	uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

test:
	pytest

lint:
	ruff check .

format:
	ruff format .

typecheck:
	mypy app

pre-commit:
	pre-commit run --all-files
