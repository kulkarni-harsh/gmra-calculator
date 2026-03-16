FROM python:3.12-slim

RUN apt-get update && \
    apt-get install -y gcc libpq-dev \
    libcairo2 libcairo2-dev libpangocairo-1.0-0 weasyprint && \
    apt clean && \
    rm -rf /var/cache/apt/*


COPY --from=ghcr.io/astral-sh/uv:0.8.15 /uv /uvx /bin/

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never

WORKDIR /app

COPY pyproject.toml /app/
RUN uv sync --no-dev

COPY . /app

EXPOSE 8000
CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
