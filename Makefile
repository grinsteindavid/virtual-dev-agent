.PHONY: help setup dev prod down logs test test-unit test-integration test-coverage test-local run clean

# Default target
help:
	@echo "Available commands:"
	@echo ""
	@echo "  First-time setup:"
	@echo "    make setup       - Build and start containers"
	@echo ""
	@echo "  Development:"
	@echo "    make dev         - Start development environment (hot-reload)"
	@echo "    make down        - Stop all containers"
	@echo "    make logs        - View container logs"
	@echo ""
	@echo "  Testing (Docker):"
	@echo "    make test        - Run unit tests in container"
	@echo "    make test-unit   - Run unit tests in container"
	@echo "    make test-integration - Run integration tests in container"
	@echo "    make test-coverage - Run tests with coverage in container"
	@echo ""
	@echo "  Testing (Local):"
	@echo "    make test-local  - Run unit tests locally"
	@echo ""
	@echo "  Production:"
	@echo "    make prod        - Start production environment"
	@echo "    make clean       - Remove containers, volumes, and cache"
	@echo ""
	@echo "  Run workflow:"
	@echo "    make run TICKET=DP-123 - Run workflow for a ticket"

# First-time setup
setup:
	@echo "Building and starting containers..."
	docker compose -f compose/docker-compose.yml -f compose/docker-compose.dev.yml up -d --build
	@echo "Setup complete! Run 'make logs' to view logs or 'make dev' for foreground mode."

# Development environment with hot-reload
dev:
	docker compose -f compose/docker-compose.yml -f compose/docker-compose.dev.yml up --build

# Production environment
prod:
	docker compose -f compose/docker-compose.yml up --build -d

# Stop all containers
down:
	docker compose -f compose/docker-compose.yml -f compose/docker-compose.dev.yml down
	docker compose -f compose/docker-compose.yml down

# View logs
logs:
	docker compose -f compose/docker-compose.yml logs -f

# Run unit tests in container
test:
	docker compose -f compose/docker-compose.yml -f compose/docker-compose.dev.yml run --rm api pytest tests/unit -v

# Run unit tests in container (alias)
test-unit:
	docker compose -f compose/docker-compose.yml -f compose/docker-compose.dev.yml run --rm api pytest tests/unit -v

# Run integration tests in container
test-integration:
	docker compose -f compose/docker-compose.yml -f compose/docker-compose.dev.yml run --rm -e RUN_INTEGRATION_TESTS=1 api pytest tests/integration -v

# Run tests with coverage in container
test-coverage:
	docker compose -f compose/docker-compose.yml -f compose/docker-compose.dev.yml run --rm api pytest tests/unit --cov=src --cov-report=term-missing

# Run tests locally (without Docker)
test-local:
	uv run pytest tests/unit -v

# Run workflow for a ticket (in container)
run:
	docker compose -f compose/docker-compose.yml -f compose/docker-compose.dev.yml run --rm api python scripts/run_task.py $(if $(TICKET),--ticket $(TICKET),)

# Clean up everything
clean:
	docker compose -f compose/docker-compose.yml -f compose/docker-compose.dev.yml down -v --remove-orphans
	docker compose -f compose/docker-compose.yml down -v --remove-orphans
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	rm -rf .coverage htmlcov
