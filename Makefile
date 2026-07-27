.PHONY: dev up down test lint format migrate revision frontend-test

dev: up

up:
	docker compose up --build -d

down:
	docker compose down

test:
	docker build --target test -t freshman-day-backend-test ./backend
	docker run --rm freshman-day-backend-test pytest -q
	cd frontend && npm run test

lint:
	docker run --rm freshman-day-backend-test ruff check app tests alembic
	docker run --rm freshman-day-backend-test mypy app
	cd frontend && npm run lint
	cd frontend && npm run typecheck

format:
	docker run --rm -v "$(CURDIR)/backend:/app" -w /app freshman-day-backend-test ruff format app tests alembic
	docker run --rm -v "$(CURDIR)/backend:/app" -w /app freshman-day-backend-test ruff check --fix app tests alembic

migrate:
	docker compose run --rm backend alembic upgrade head

revision:
	docker compose run --rm backend alembic revision --autogenerate -m "$(m)"

frontend-test:
	cd frontend && npm run test:e2e
