.PHONY: install install-dev test test-cov lint type-check format run-dev run-worker reset-test-db clean help

# Install dependencies (runtime only)
install:
	uv sync

# Install dependencies (including dev packages) and the pre-commit hooks
install-dev:
	uv sync --dev
	uv run pre-commit install

# Run tests
test:
	uv run pytest -n auto

# Run tests with coverage and enforce the minimum threshold
test-cov:
	uv run pytest -n auto --cov=app --cov-report=term-missing --cov-report=xml:coverage.xml --cov-fail-under=98

# Lint and format-check the code, then type-check
lint:
	uv run ruff check .
	uv run ruff format --check .
	uv run ty check .

# Type check the code
type-check:
	uv run ty check .

# Auto-fix lint issues and format the code
format:
	uv run ruff check --fix .
	uv run ruff format .

# Run the development server
run-dev:
	uv run uvicorn app.main:app --reload

# Run the Celery worker
run-worker:
	uv run celery -A app.worker worker -l info

# Reset the test database (drop and recreate)
reset-test-db:
	psql -h localhost -U postgres -c "DROP DATABASE IF EXISTS starter_test"
	psql -h localhost -U postgres -c "CREATE DATABASE starter_test"

# Clean up cache files
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name ".coverage" -delete

help:
	@echo "Available commands:"
	@echo "  install        - Install runtime dependencies"
	@echo "  install-dev    - Install dev dependencies and pre-commit hooks"
	@echo "  test           - Run tests"
	@echo "  test-cov       - Run tests with coverage (fails under 98%)"
	@echo "  lint           - Run ruff check + ruff format --check + ty"
	@echo "  type-check     - Type check code with ty"
	@echo "  format         - Auto-fix lint issues and format code"
	@echo "  run-dev        - Run the development server"
	@echo "  run-worker     - Run the Celery worker"
	@echo "  reset-test-db  - Drop and recreate the test database"
	@echo "  clean          - Clean up cache files"
