SHELL := /bin/bash

PG_BIN := /opt/homebrew/opt/postgresql@15/bin
PG_DATA := /opt/homebrew/var/postgresql@15
PG_LOG := ./postgres.log
VENV := backend/venv/bin

.PHONY: help db-start db-stop db-restart db-status backend frontend phoenix migrate migrate-create migrate-downgrade migrate-history test test-verbose test-coverage test-coverage-html test-watch test-file test-failed install-test-deps

help:
	@echo "Available commands:"
	@echo ""
	@echo "Database:"
	@echo "  make db-start    - Start the PostgreSQL database in the background"
	@echo "  make db-stop     - Stop the PostgreSQL database"
	@echo "  make db-restart  - Restart the PostgreSQL database"
	@echo "  make db-status   - Check the status of the PostgreSQL database"
	@echo ""
	@echo "Servers:"
	@echo "  make phoenix     - Run the Phoenix tracing server"
	@echo "  make backend     - Run the FastAPI backend server"
	@echo "  make frontend    - Run the Next.js frontend server"
	@echo ""
	@echo "Migrations:"
	@echo "  make migrate     - Run all pending Alembic migrations (upgrade head)"
	@echo "  make migrate-create m='description' - Create a new migration"
	@echo "  make migrate-downgrade rev='-1' - Downgrade migration (default: -1)"
	@echo "  make migrate-history - Show migration history"
	@echo ""
	@echo "Testing:"
	@echo "  make test        - Run all tests"
	@echo "  make test-verbose - Run all tests with verbose output"
	@echo "  make test-coverage - Run tests with coverage report"
	@echo "  make test-coverage-html - Run tests and generate HTML coverage report"
	@echo "  make test-watch  - Run tests in watch mode (re-run on file changes)"
	@echo "  make test-file file='path/to/test.py' - Run specific test file"
	@echo "  make test-failed - Re-run only failed tests from last run"
	@echo "  make install-test-deps - Install testing dependencies"

db-start:
	@echo "Starting PostgreSQL..."
	@$(PG_BIN)/pg_ctl -D $(PG_DATA) -l $(PG_LOG) start

db-stop:
	@echo "Stopping PostgreSQL..."
	@$(PG_BIN)/pg_ctl -D $(PG_DATA) stop

db-restart: db-stop db-start

db-status:
	@$(PG_BIN)/pg_ctl -D $(PG_DATA) status

phoenix:
	@echo "Starting Phoenix tracing server..."
	@$(CURDIR)/$(VENV)/python -m phoenix.server.main serve

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

# Testing targets
install-test-deps:
	@echo "Installing test dependencies..."
	@cd backend && $(CURDIR)/$(VENV)/pip install -r requirements-dev.txt

test:
	@echo "Running all tests..."
	@cd backend && $(CURDIR)/$(VENV)/python -m pytest tests/ -v

test-verbose:
	@echo "Running all tests with verbose output..."
	@cd backend && $(CURDIR)/$(VENV)/python -m pytest tests/ -vv --tb=short

test-coverage:
	@echo "Running tests with coverage report..."
	@cd backend && $(CURDIR)/$(VENV)/python -m pytest tests/ -v --cov=app --cov-report=term-missing

test-coverage-html:
	@echo "Running tests and generating HTML coverage report..."
	@cd backend && $(CURDIR)/$(VENV)/python -m pytest tests/ -v --cov=app --cov-report=html
	@echo "Coverage report generated at backend/htmlcov/index.html"
	@echo "Open with: open backend/htmlcov/index.html"

test-watch:
	@echo "Running tests in watch mode..."
	@cd backend && $(CURDIR)/$(VENV)/python -m pytest tests/ -v --looponfail

test-file:
	@echo "Running test file: $(file)"
	@cd backend && $(CURDIR)/$(VENV)/python -m pytest $(file) -v

test-failed:
	@echo "Re-running failed tests..."
	@cd backend && $(CURDIR)/$(VENV)/python -m pytest tests/ -v --lf
