FROM python:3.12-slim AS base
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY pyproject.toml ./
COPY app ./app
COPY alembic.ini ./
COPY alembic ./alembic

FROM base AS test
RUN pip install --no-cache-dir ".[dev]"
COPY tests ./tests
CMD ["pytest", "-q"]

FROM base AS runtime
RUN pip install --no-cache-dir . && useradd --create-home --uid 10001 appuser && mkdir -p /data/uploads && chown -R appuser:appuser /data
USER appuser
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
