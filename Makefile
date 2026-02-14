SHELL := /bin/bash

PG_BIN := /opt/homebrew/opt/postgresql@15/bin
PG_DATA := /opt/homebrew/var/postgresql@15
PG_LOG := ./postgres.log
VENV := backend/venv/bin

.PHONY: help db-start db-stop db-restart db-status backend frontend migrate migrate-create migrate-downgrade migrate-history

help:
	@echo "Available commands:"
	@echo "  make db-start    - Start the PostgreSQL database in the background"
	@echo "  make db-stop     - Stop the PostgreSQL database"
	@echo "  make db-restart  - Restart the PostgreSQL database"
	@echo "  make db-status   - Check the status of the PostgreSQL database"
	@echo "  make backend     - Run the FastAPI backend server"
	@echo "  make frontend    - Run the Next.js frontend server"
	@echo "  make migrate     - Run all pending Alembic migrations (upgrade head)"
	@echo "  make migrate-create m='description' - Create a new migration"
	@echo "  make migrate-downgrade rev='-1' - Downgrade migration (default: -1)"
	@echo "  make migrate-history - Show migration history"

db-start:
	@echo "Starting PostgreSQL..."
	@$(PG_BIN)/pg_ctl -D $(PG_DATA) -l $(PG_LOG) start

db-stop:
	@echo "Stopping PostgreSQL..."
	@$(PG_BIN)/pg_ctl -D $(PG_DATA) stop

db-restart: db-stop db-start

db-status:
	@$(PG_BIN)/pg_ctl -D $(PG_DATA) status

backend:
	@echo "Starting Backend..."
	@cd backend && $(CURDIR)/$(VENV)/python -m uvicorn app.main:app --reload --port 8000

frontend:
	@echo "Starting Frontend..."
	@cd frontend && npm run dev

migrate:
	@echo "Running migrations..."
	@cd backend && $(CURDIR)/$(VENV)/python -m alembic upgrade head

migrate-create:
	@echo "Creating migration: $(m)"
	@cd backend && $(CURDIR)/$(VENV)/python -m alembic revision --autogenerate -m "$(m)"

migrate-downgrade:
	@echo "Downgrading migration..."
	@cd backend && $(CURDIR)/$(VENV)/python -m alembic downgrade $(or $(rev),-1)

migrate-history:
	@cd backend && $(CURDIR)/$(VENV)/python -m alembic history --verbose
