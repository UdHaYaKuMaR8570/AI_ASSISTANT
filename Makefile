COMPOSE = docker compose -f deploy/docker-compose.yml

.PHONY: help up down ps logs ingest test dev-api dev-web

help:
	@echo "The Lenny Growth Assistant"
	@echo ""
	@echo "  Setup & Run:"
	@echo "    make up          Build and start full stack (db, litellm, api, web)"
	@echo "    make down        Stop all containers"
	@echo "    make ps          Show container status"
	@echo "    make logs        Tail service logs"
	@echo "    make ingest      Run transcript ingestion pipeline"
	@echo "    make test        Run backend test suite"
	@echo "    make dev-api     Run FastAPI locally on :8000 with hot reload"
	@echo "    make dev-web     Run Vite frontend locally on :3000"
	@echo ""

up:
	$(COMPOSE) up -d --build

down:
	$(COMPOSE) down

ps:
	$(COMPOSE) ps

logs:
	$(COMPOSE) logs -f

ingest:
	$(COMPOSE) run --rm ingest

test:
	cd backend && .\.venv\Scripts\python -m pytest

dev-api:
	cd backend && .\.venv\Scripts\uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

dev-web:
	cd frontend && npx vite --port 3000
