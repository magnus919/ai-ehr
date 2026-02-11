# ===========================================================================
# OpenMedRecord -- Makefile
#
# Common commands for development, testing, building, and deployment.
#
# Usage:
#   make help       Show available targets
#   make dev        Start local development environment
#   make test       Run all tests
#   make lint       Run linters
#   make build      Build Docker images
# ===========================================================================

.DEFAULT_GOAL := help
.PHONY: help dev dev-down test test-unit test-integration test-e2e test-frontend \
        lint lint-backend lint-frontend format build deploy-staging deploy-prod \
        migrate seed clean setup

# ---------------------------------------------------------------------------
# Variables
# ---------------------------------------------------------------------------

PROJECT_ROOT := $(shell pwd)
BACKEND_DIR := $(PROJECT_ROOT)/src/backend
FRONTEND_DIR := $(PROJECT_ROOT)/src/frontend
DOCKER_DIR := $(PROJECT_ROOT)/infrastructure/docker
CDK_DIR := $(PROJECT_ROOT)/infrastructure/cdk
VENV := $(BACKEND_DIR)/.venv/bin

DOCKER_COMPOSE := docker compose -f $(DOCKER_DIR)/docker-compose.yml
DOCKER_COMPOSE_TEST := docker compose -f $(DOCKER_DIR)/docker-compose.test.yml

# ---------------------------------------------------------------------------
# Help
# ---------------------------------------------------------------------------

help: ## Show this help message
	@echo ""
	@echo "OpenMedRecord - Available Commands"
	@echo "=================================="
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'
	@echo ""

# ---------------------------------------------------------------------------
# Setup
# ---------------------------------------------------------------------------

setup: ## Run full development environment setup
	@bash scripts/setup-dev.sh

# ---------------------------------------------------------------------------
# Development
# ---------------------------------------------------------------------------

dev: ## Start local development environment (Docker services + API + frontend)
	$(DOCKER_COMPOSE) up -d postgres redis mailpit
	@echo ""
	@echo "Services started. Run the following in separate terminals:"
	@echo ""
	@echo "  Backend:  cd src/backend && source .venv/bin/activate && uvicorn app.main:app --reload --port 8000"
	@echo "  Frontend: cd src/frontend && npm run dev"
	@echo ""

dev-up: ## Start all Docker services including app containers
	$(DOCKER_COMPOSE) up -d

dev-down: ## Stop all Docker services
	$(DOCKER_COMPOSE) down

dev-logs: ## Tail logs from all Docker services
	$(DOCKER_COMPOSE) logs -f

dev-restart: ## Restart all Docker services
	$(DOCKER_COMPOSE) restart

# ---------------------------------------------------------------------------
# Database
# ---------------------------------------------------------------------------

migrate: ## Run database migrations
	cd $(BACKEND_DIR) && $(VENV)/python -m alembic upgrade head

migrate-create: ## Create a new migration (usage: make migrate-create MSG="add users table")
	cd $(BACKEND_DIR) && $(VENV)/python -m alembic revision --autogenerate -m "$(MSG)"

migrate-rollback: ## Rollback the last migration
	cd $(BACKEND_DIR) && $(VENV)/python -m alembic downgrade -1

seed: ## Seed the database with sample data
	$(VENV)/python scripts/seed-data.py

db-shell: ## Open a psql shell to the local database
	docker exec -it omr-postgres psql -U openmed -d openmedrecord

# ---------------------------------------------------------------------------
# Testing
# ---------------------------------------------------------------------------

test: ## Run all tests (backend + frontend) with coverage
	@bash scripts/run-tests.sh

test-unit: ## Run backend unit tests
	@bash scripts/run-tests.sh --unit

test-integration: ## Run backend integration tests
	@bash scripts/run-tests.sh --integration

test-e2e: ## Run end-to-end tests
	@bash scripts/run-tests.sh --e2e

test-frontend: ## Run frontend tests
	@bash scripts/run-tests.sh --frontend

test-backend: ## Run all backend tests
	@bash scripts/run-tests.sh --backend

test-docker: ## Run tests in Docker containers
	$(DOCKER_COMPOSE_TEST) up --build --abort-on-container-exit test-runner
	$(DOCKER_COMPOSE_TEST) down -v

test-watch: ## Run backend tests in watch mode
	cd $(BACKEND_DIR) && $(VENV)/python -m pytest tests/unit/ -v --tb=short -f

test-watch-frontend: ## Run frontend tests in watch mode
	cd $(FRONTEND_DIR) && npx vitest

# ---------------------------------------------------------------------------
# Linting & Formatting
# ---------------------------------------------------------------------------

lint: lint-backend lint-frontend ## Run all linters

lint-backend: ## Run Python linters (ruff)
	cd $(BACKEND_DIR) && $(VENV)/ruff check . --output-format=full
	cd $(BACKEND_DIR) && $(VENV)/ruff format --check .

lint-frontend: ## Run TypeScript linters (eslint)
	cd $(FRONTEND_DIR) && npx eslint . --ext ts,tsx --report-unused-disable-directives --max-warnings 0

format: ## Auto-format all code
	cd $(BACKEND_DIR) && $(VENV)/ruff format .
	cd $(BACKEND_DIR) && $(VENV)/ruff check --fix .
	cd $(FRONTEND_DIR) && npx eslint . --ext ts,tsx --fix

type-check: ## Run type checking (mypy + tsc)
	cd $(FRONTEND_DIR) && npx tsc --noEmit

# ---------------------------------------------------------------------------
# Security
# ---------------------------------------------------------------------------

security-scan: ## Run security scans locally
	cd $(BACKEND_DIR) && $(VENV)/bandit -r app/ --severity-level medium
	cd $(BACKEND_DIR) && $(VENV)/pip-audit -r requirements.txt
	cd $(FRONTEND_DIR) && npm audit

# ---------------------------------------------------------------------------
# Build
# ---------------------------------------------------------------------------

build: ## Build Docker images for all services
	docker build -t openmedrecord/api-gateway:local \
		--target production \
		--build-arg SERVICE_NAME=api-gateway \
		-f $(BACKEND_DIR)/Dockerfile $(BACKEND_DIR)
	@echo "Build complete: openmedrecord/api-gateway:local"

build-frontend: ## Build frontend for production
	cd $(FRONTEND_DIR) && npm run build

# ---------------------------------------------------------------------------
# Deployment
# ---------------------------------------------------------------------------

deploy-staging: ## Deploy to staging environment
	cd $(CDK_DIR) && STAGE=staging cdk deploy --all --require-approval broadening

deploy-prod: ## Deploy to production environment (requires approval)
	@echo "WARNING: Deploying to PRODUCTION."
	@read -p "Are you sure? [y/N] " confirm && [ "$$confirm" = "y" ]
	cd $(CDK_DIR) && STAGE=production cdk deploy --all --require-approval broadening

cdk-synth: ## Synthesize CDK stacks (dry run)
	cd $(CDK_DIR) && STAGE=staging cdk synth

cdk-diff: ## Show CDK diff against deployed stacks
	cd $(CDK_DIR) && STAGE=staging cdk diff

# ---------------------------------------------------------------------------
# Cleanup
# ---------------------------------------------------------------------------

clean: ## Remove build artifacts, caches, and temporary files
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .ruff_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .mypy_cache -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyc" -delete 2>/dev/null || true
	rm -rf $(FRONTEND_DIR)/dist $(FRONTEND_DIR)/coverage
	rm -rf coverage-*.xml test-results-*.xml
	rm -rf cdk.out/
	@echo "Clean complete."

clean-all: clean ## Remove everything including node_modules and venv
	rm -rf $(BACKEND_DIR)/.venv
	rm -rf $(FRONTEND_DIR)/node_modules
	$(DOCKER_COMPOSE) down -v --rmi local
	@echo "Full clean complete."
