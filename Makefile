.PHONY: help setup install add runserver migrate makemigrations shell createsuperuser test test-cov lint format audit check clean messages compilemessages

MANAGE := uv run python manage.py

help:
	@echo "Available commands:"
	@echo "  make setup               - Create virtualenv and install all dependencies"
	@echo "  make install             - Install/sync project dependencies"
	@echo "  make add pkg=<name>      - Add a new dependency (e.g., make add pkg=requests)"
	@echo "  make runserver           - Run the Django development server"
	@echo "  make migrate             - Apply database migrations"
	@echo "  make makemigrations      - Create new migrations from model changes"
	@echo "  make shell               - Open the Django shell"
	@echo "  make createsuperuser     - Create a Django superuser"
	@echo "  make test                - Run tests with pytest"
	@echo "  make test-cov            - Run tests with coverage report"
	@echo "  make lint                - Run ruff linter"
	@echo "  make format              - Format code with ruff"
	@echo "  make audit               - Check dependencies for vulnerabilities"
	@echo "  make check               - Run all checks (lint + audit + test)"
	@echo "  make messages            - Extract translation strings for ru/en"
	@echo "  make compilemessages     - Compile .po files into .mo"
	@echo "  make clean               - Remove Python cache files"

setup:
	uv venv
	uv sync --extra dev

install:
	uv sync --extra dev

add:
	@if [ -z "$(pkg)" ]; then echo "Usage: make add pkg=<package-name>"; exit 1; fi
	uv add $(pkg)

runserver:
	$(MANAGE) runserver

migrate:
	$(MANAGE) migrate

makemigrations:
	$(MANAGE) makemigrations

shell:
	$(MANAGE) shell

createsuperuser:
	$(MANAGE) createsuperuser

test:
	uv run pytest

test-cov:
	uv run pytest --cov --cov-report=html --cov-report=term-missing

lint:
	uv run ruff check .

format:
	uv run ruff format .
	uv run ruff check --fix .

audit:
	uv run pip-audit

check: lint audit test

clean:
	find . -name "__pycache__" -type d -prune -exec rm -rf {} +
	find . -name "*.pyc" -delete
	rm -rf .pytest_cache htmlcov .coverage coverage.xml

messages:
	$(MANAGE) makemessages -l ru
	$(MANAGE) makemessages -l en

compilemessages:
	$(MANAGE) compilemessages
