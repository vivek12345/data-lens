.PHONY: help install dev sync clean test test-cov lint format type-check run-stdio run-http docker-db setup check all

# Default target
.DEFAULT_GOAL := help

# Colors for output
BLUE := \033[0;34m
GREEN := \033[0;32m
YELLOW := \033[0;33m
RED := \033[0;31m
NC := \033[0m # No Color

##@ General

help: ## Display this help message
	@echo "$(BLUE)MCP Data Lens - Available Commands$(NC)"
	@echo ""
	@awk 'BEGIN {FS = ":.*##"; printf "Usage:\n  make $(GREEN)<target>$(NC)\n"} /^[a-zA-Z_-]+:.*?##/ { printf "  $(GREEN)%-20s$(NC) %s\n", $$1, $$2 } /^##@/ { printf "\n$(YELLOW)%s$(NC)\n", substr($$0, 5) } ' $(MAKEFILE_LIST)

##@ Setup & Installation

install: ## Install production dependencies
	@echo "$(BLUE)Installing production dependencies...$(NC)"
	uv sync --no-dev

dev: ## Install all dependencies including dev tools
	@echo "$(BLUE)Installing all dependencies...$(NC)"
	uv sync

sync: ## Sync dependencies with lock file
	@echo "$(BLUE)Syncing dependencies...$(NC)"
	uv sync

setup: dev .env ## Complete setup (install deps + create .env)
	@echo "$(GREEN)✓ Setup complete!$(NC)"
	@echo "$(YELLOW)Don't forget to configure your .env file$(NC)"

.env: ## Create .env from example
	@if [ ! -f .env ]; then \
		echo "$(BLUE)Creating .env from .env.example...$(NC)"; \
		cp .env.example .env; \
		echo "$(GREEN)✓ .env created$(NC)"; \
		echo "$(YELLOW)⚠ Please edit .env with your configuration$(NC)"; \
	else \
		echo "$(YELLOW).env already exists, skipping...$(NC)"; \
	fi

##@ Development

run-stdio: ## Run server in stdio mode (for Claude Desktop)
	@echo "$(BLUE)Starting server in stdio mode...$(NC)"
	TRANSPORT_MODE=stdio uv run server.py

run-http: ## Run server in HTTP mode
	@echo "$(BLUE)Starting server in HTTP mode...$(NC)"
	TRANSPORT_MODE=http uv run server.py

run: run-stdio ## Alias for run-stdio

##@ Testing

test: ## Run tests
	@echo "$(BLUE)Running tests...$(NC)"
	uv run pytest

test-cov: ## Run tests with coverage
	@echo "$(BLUE)Running tests with coverage...$(NC)"
	uv run pytest --cov=data_lens --cov-report=html --cov-report=term
	@echo "$(GREEN)✓ Coverage report generated in htmlcov/index.html$(NC)"

test-verbose: ## Run tests with verbose output
	@echo "$(BLUE)Running tests (verbose)...$(NC)"
	uv run pytest -v

test-watch: ## Run tests in watch mode
	@echo "$(BLUE)Running tests in watch mode...$(NC)"
	uv run pytest-watch

##@ Code Quality

lint: ## Run linting checks
	@echo "$(BLUE)Running linting checks...$(NC)"
	uv run ruff check data_lens/

lint-fix: ## Run linting with auto-fix
	@echo "$(BLUE)Running linting with auto-fix...$(NC)"
	uv run ruff check data_lens/ --fix

format: ## Format code with black and isort
	@echo "$(BLUE)Formatting code...$(NC)"
	uv run black data_lens/
	uv run isort data_lens/
	@echo "$(GREEN)✓ Code formatted$(NC)"

format-check: ## Check code formatting without making changes
	@echo "$(BLUE)Checking code formatting...$(NC)"
	uv run black --check data_lens/
	uv run isort --check-only data_lens/

type-check: ## Run type checking with mypy
	@echo "$(BLUE)Running type checks...$(NC)"
	uv run mypy data_lens/

check: lint format-check type-check ## Run all checks (lint, format, type)
	@echo "$(GREEN)✓ All checks passed$(NC)"

fix: lint-fix format ## Fix linting issues and format code
	@echo "$(GREEN)✓ Code fixed and formatted$(NC)"

##@ Database

docker-db: ## Start MySQL test database in Docker
	@echo "$(BLUE)Starting MySQL test database...$(NC)"
	docker run -d \
		--name mcp-data-lens-db \
		-e MYSQL_ROOT_PASSWORD=testpassword \
		-e MYSQL_DATABASE=testdb \
		-p 3306:3306 \
		mysql:8.0
	@echo "$(GREEN)✓ MySQL database started$(NC)"
	@echo "$(YELLOW)Connection details:$(NC)"
	@echo "  Host: localhost"
	@echo "  Port: 3306"
	@echo "  User: root"
	@echo "  Password: testpassword"
	@echo "  Database: testdb"

docker-db-stop: ## Stop MySQL test database
	@echo "$(BLUE)Stopping MySQL test database...$(NC)"
	docker stop mcp-data-lens-db
	docker rm mcp-data-lens-db
	@echo "$(GREEN)✓ Database stopped and removed$(NC)"

docker-db-logs: ## View MySQL database logs
	docker logs -f mcp-data-lens-db

##@ Cleanup

clean: ## Remove build artifacts and cache files
	@echo "$(BLUE)Cleaning up...$(NC)"
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.log" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "htmlcov" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name ".coverage" -delete 2>/dev/null || true
	rm -rf build/ dist/ 2>/dev/null || true
	@echo "$(GREEN)✓ Cleanup complete$(NC)"

clean-all: clean ## Remove everything including venv
	@echo "$(BLUE)Removing virtual environment...$(NC)"
	rm -rf .venv/
	@echo "$(GREEN)✓ All cleaned$(NC)"

##@ Build & Distribution

build: ## Build distribution packages
	@echo "$(BLUE)Building distribution packages...$(NC)"
	uv build

##@ Utilities

info: ## Display project information
	@echo "$(BLUE)Project Information$(NC)"
	@echo ""
	@echo "$(YELLOW)Name:$(NC)        MCP Data Lens"
	@echo "$(YELLOW)Python:$(NC)      $$(python --version 2>&1)"
	@echo "$(YELLOW)uv:$(NC)          $$(uv --version 2>&1)"
	@echo "$(YELLOW)Location:$(NC)    $$(pwd)"
	@echo ""
	@echo "$(YELLOW)Dependencies:$(NC)"
	@uv pip list 2>/dev/null || echo "  Run 'make install' first"

version: ## Show version information
	@echo "$(BLUE)Version Information$(NC)"
	@python -c "import tomli; print('Version:', tomli.load(open('pyproject.toml', 'rb'))['project']['version'])" 2>/dev/null || \
		grep '^version' pyproject.toml | cut -d'"' -f2

update: ## Update dependencies
	@echo "$(BLUE)Updating dependencies...$(NC)"
	uv sync --upgrade

lock: ## Update lock file
	@echo "$(BLUE)Updating lock file...$(NC)"
	uv lock

##@ All-in-One Commands

all: clean install check test ## Clean, install, check, and test everything
	@echo "$(GREEN)✓ All tasks completed successfully!$(NC)"

ci: check test ## Run CI checks (for continuous integration)
	@echo "$(GREEN)✓ CI checks passed$(NC)"

pre-commit: format lint test ## Run pre-commit checks
	@echo "$(GREEN)✓ Pre-commit checks passed$(NC)"

