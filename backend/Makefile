# Makefile for Otomeshon Banking Platform
# Banking-grade development and deployment automation

.PHONY: help install install-dev test test-unit test-integration test-banking test-security test-performance lint format type-check security-scan clean build run dev migrate seed deploy docker-build docker-run docker-stop pre-commit setup-dev validate-env backup

# Variables
PYTHON := python3.11
PIP := pip
POETRY := poetry
PROJECT_NAME := otomeshon-banking
DOCKER_IMAGE := $(PROJECT_NAME)
DOCKER_TAG := latest
DB_NAME := otomeshon
TEST_DB_NAME := otomeshon_test

# Colors for output
RED := \033[0;31m
GREEN := \033[0;32m
YELLOW := \033[1;33m
BLUE := \033[0;34m
CYAN := \033[0;36m
NC := \033[0m # No Color

# Default target
help: ## Show this help message
	@echo "$(CYAN)Otomeshon Banking Platform - Development Commands$(NC)"
	@echo "$(CYAN)================================================$(NC)"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "$(GREEN)%-20s$(NC) %s\n", $$1, $$2}'
	@echo ""
	@echo "$(YELLOW)Banking Compliance Notes:$(NC)"
	@echo "  - All tests must pass before deployment"
	@echo "  - Security scans are mandatory"
	@echo "  - Audit logs must be maintained"
	@echo "  - Performance monitoring is required"

# Environment setup
install: ## Install production dependencies
	@echo "$(BLUE)Installing production dependencies...$(NC)"
	$(PIP) install -r requirements-core.txt

install-dev: ## Install development dependencies
	@echo "$(BLUE)Installing development dependencies...$(NC)"
	$(PIP) install -r requirements-dev.txt
	$(PIP) install -r requirements-core.txt
	pre-commit install

install-banking: ## Install banking-specific dependencies
	@echo "$(BLUE)Installing banking dependencies...$(NC)"
	$(PIP) install -r requirements-banking.txt

install-all: ## Install all dependencies
	@echo "$(BLUE)Installing all dependencies...$(NC)"
	$(PIP) install -r requirements-core.txt
	$(PIP) install -r requirements-banking.txt
	$(PIP) install -r requirements-ai.txt
	$(PIP) install -r requirements-infrastructure.txt
	$(PIP) install -r requirements-observability.txt
	$(PIP) install -r requirements-dev.txt

setup-dev: install-dev ## Setup development environment
	@echo "$(BLUE)Setting up development environment...$(NC)"
	pre-commit install
	@if [ ! -f .env ]; then cp .env.example .env; echo "$(YELLOW)Created .env from .env.example$(NC)"; fi
	@echo "$(GREEN)Development environment setup complete!$(NC)"
	@echo "$(YELLOW)Next steps:$(NC)"
	@echo "  1. Update .env with your configuration"
	@echo "  2. Run 'make migrate' to setup database"
	@echo "  3. Run 'make seed' to populate test data"
	@echo "  4. Run 'make dev' to start development server"

# Testing
test: ## Run all tests
	@echo "$(BLUE)Running all tests...$(NC)"
	pytest tests/ -v --cov=app --cov-report=term-missing --cov-report=html

test-unit: ## Run unit tests only
	@echo "$(BLUE)Running unit tests...$(NC)"
	pytest tests/ -v -m "unit" --cov=app --cov-report=term-missing

test-integration: ## Run integration tests only
	@echo "$(BLUE)Running integration tests...$(NC)"
	pytest tests/ -v -m "integration" --cov=app --cov-report=term-missing

test-banking: ## Run banking-specific tests
	@echo "$(BLUE)Running banking tests...$(NC)"
	pytest tests/ -v -m "banking" --cov=app --cov-report=term-missing

test-security: ## Run security tests
	@echo "$(BLUE)Running security tests...$(NC)"
	pytest tests/ -v -m "security" --cov=app --cov-report=term-missing

test-performance: ## Run performance tests
	@echo "$(BLUE)Running performance tests...$(NC)"
	pytest tests/ -v -m "performance" --cov=app --cov-report=term-missing

test-compliance: ## Run compliance tests
	@echo "$(BLUE)Running compliance tests...$(NC)"
	pytest tests/ -v -m "compliance" --cov=app --cov-report=term-missing

test-watch: ## Run tests in watch mode
	@echo "$(BLUE)Running tests in watch mode...$(NC)"
	pytest-watch tests/ --verbose

# Code quality
lint: ## Run all linters
	@echo "$(BLUE)Running linters...$(NC)"
	flake8 app/ scripts/
	pylint app/ scripts/
	@echo "$(GREEN)Linting complete!$(NC)"

format: ## Format code with black and isort
	@echo "$(BLUE)Formatting code...$(NC)"
	black app/ scripts/ tests/
	isort app/ scripts/ tests/
	autoflake --in-place --remove-all-unused-imports --remove-unused-variables app/ scripts/ tests/
	@echo "$(GREEN)Code formatting complete!$(NC)"

type-check: ## Run type checking with mypy
	@echo "$(BLUE)Running type checks...$(NC)"
	mypy app/ scripts/
	@echo "$(GREEN)Type checking complete!$(NC)"

security-scan: ## Run security scanning
	@echo "$(BLUE)Running security scan...$(NC)"
	bandit -r app/ -f json -o security-report.json
	bandit -r app/ -f console
	python scripts/security_scan.py
	@echo "$(GREEN)Security scan complete!$(NC)"

pre-commit: ## Run pre-commit hooks
	@echo "$(BLUE)Running pre-commit hooks...$(NC)"
	pre-commit run --all-files

validate-all: lint type-check security-scan test ## Run all validation checks
	@echo "$(GREEN)All validation checks passed!$(NC)"

# Database operations
migrate: ## Run database migrations
	@echo "$(BLUE)Running database migrations...$(NC)"
	python scripts/migration_utils.py upgrade
	@echo "$(GREEN)Migrations complete!$(NC)"

migrate-create: ## Create new migration
	@echo "$(BLUE)Creating new migration...$(NC)"
	@read -p "Migration message: " message; \
	python scripts/migration_utils.py create "$$message"

migrate-downgrade: ## Downgrade database (WARNING: Banking compliance)
	@echo "$(RED)WARNING: Database downgrade may violate banking compliance!$(NC)"
	@read -p "Are you sure? Type 'yes' to continue: " confirm; \
	if [ "$$confirm" = "yes" ]; then \
		read -p "Target revision: " revision; \
		python scripts/migration_utils.py downgrade "$$revision"; \
	else \
		echo "Operation cancelled"; \
	fi

migrate-history: ## Show migration history
	@echo "$(BLUE)Migration history:$(NC)"
	python scripts/migration_utils.py history

seed: ## Seed database with sample data
	@echo "$(BLUE)Seeding database...$(NC)"
	python scripts/seed_database.py seed
	@echo "$(GREEN)Database seeding complete!$(NC)"

seed-clear: ## Clear seeded data
	@echo "$(YELLOW)Clearing seeded data...$(NC)"
	python scripts/seed_database.py clear
	@echo "$(GREEN)Data cleared!$(NC)"

backup: ## Create database backup
	@echo "$(BLUE)Creating database backup...$(NC)"
	python scripts/migration_utils.py backup
	@echo "$(GREEN)Backup complete!$(NC)"

# Application management
run: ## Run production server
	@echo "$(BLUE)Starting production server...$(NC)"
	uvicorn app.main:app --host 0.0.0.0 --port 8000

dev: ## Run development server
	@echo "$(BLUE)Starting development server...$(NC)"
	uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload --log-level debug

dev-simple: ## Run simple development server
	@echo "$(BLUE)Starting simple development server...$(NC)"
	uvicorn app.main_simple:app --host 0.0.0.0 --port 8000 --reload

validate-env: ## Validate environment configuration
	@echo "$(BLUE)Validating environment configuration...$(NC)"
	python scripts/validate_config.py
	@echo "$(GREEN)Environment validation complete!$(NC)"

# Docker operations
docker-build: ## Build Docker image
	@echo "$(BLUE)Building Docker image...$(NC)"
	docker build -t $(DOCKER_IMAGE):$(DOCKER_TAG) .
	@echo "$(GREEN)Docker image built!$(NC)"

docker-run: ## Run application in Docker
	@echo "$(BLUE)Running application in Docker...$(NC)"
	docker run -p 8000:8000 --env-file .env $(DOCKER_IMAGE):$(DOCKER_TAG)

docker-dev: ## Run development environment in Docker
	@echo "$(BLUE)Running development environment in Docker...$(NC)"
	docker-compose up --build

docker-stop: ## Stop Docker containers
	@echo "$(BLUE)Stopping Docker containers...$(NC)"
	docker-compose down

docker-logs: ## View Docker logs
	@echo "$(BLUE)Viewing Docker logs...$(NC)"
	docker-compose logs -f

# Performance and monitoring
benchmark: ## Run performance benchmarks
	@echo "$(BLUE)Running performance benchmarks...$(NC)"
	python scripts/performance_checker.py benchmark
	@echo "$(GREEN)Benchmarks complete!$(NC)"

profile: ## Profile application performance
	@echo "$(BLUE)Profiling application...$(NC)"
	python scripts/performance_checker.py profile
	@echo "$(GREEN)Profiling complete!$(NC)"

monitor: ## Start monitoring dashboard
	@echo "$(BLUE)Starting monitoring dashboard...$(NC)"
	@echo "$(CYAN)Access monitoring at: http://localhost:8000/monitoring/health$(NC)"

# Banking compliance operations
compliance-check: ## Run banking compliance validation
	@echo "$(BLUE)Running banking compliance checks...$(NC)"
	python scripts/validate_config.py --compliance
	python scripts/audit_validator.py
	python scripts/security_config_checker.py
	@echo "$(GREEN)Compliance checks complete!$(NC)"

audit-report: ## Generate audit report
	@echo "$(BLUE)Generating audit report...$(NC)"
	python scripts/audit_validator.py --report
	@echo "$(GREEN)Audit report generated!$(NC)"

security-report: ## Generate security report
	@echo "$(BLUE)Generating security report...$(NC)"
	python scripts/security_scan.py --report
	@echo "$(GREEN)Security report generated!$(NC)"

# Cleanup
clean: ## Clean up generated files
	@echo "$(BLUE)Cleaning up...$(NC)"
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf build/
	rm -rf dist/
	rm -rf htmlcov/
	rm -rf .coverage
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/
	@echo "$(GREEN)Cleanup complete!$(NC)"

clean-all: clean ## Clean everything including virtual environment
	@echo "$(BLUE)Deep cleaning...$(NC)"
	rm -rf venv/
	rm -rf .venv/
	@echo "$(GREEN)Deep cleanup complete!$(NC)"

# Documentation
docs: ## Generate documentation
	@echo "$(BLUE)Generating documentation...$(NC)"
	@echo "$(YELLOW)Documentation generation not yet implemented$(NC)"

docs-serve: ## Serve documentation locally
	@echo "$(BLUE)Serving documentation...$(NC)"
	@echo "$(YELLOW)Documentation serving not yet implemented$(NC)"

# Deployment
deploy-staging: validate-all ## Deploy to staging environment
	@echo "$(BLUE)Deploying to staging...$(NC)"
	@echo "$(YELLOW)Staging deployment not yet implemented$(NC)"

deploy-production: validate-all ## Deploy to production environment
	@echo "$(BLUE)Deploying to production...$(NC)"
	@echo "$(RED)PRODUCTION DEPLOYMENT - Banking compliance required!$(NC)"
	@echo "$(YELLOW)Production deployment not yet implemented$(NC)"

# CI/CD helpers
ci-test: ## Run CI test suite
	@echo "$(BLUE)Running CI test suite...$(NC)"
	pytest tests/ -v --cov=app --cov-report=xml --cov-report=term-missing
	bandit -r app/ -f json -o bandit-report.json
	mypy app/ --junit-xml=mypy-report.xml

ci-build: ## Build for CI/CD
	@echo "$(BLUE)Building for CI/CD...$(NC)"
	docker build -t $(DOCKER_IMAGE):$(DOCKER_TAG) .

# Database utilities
db-reset: ## Reset database (WARNING: Destructive)
	@echo "$(RED)WARNING: This will destroy all data!$(NC)"
	@read -p "Are you sure? Type 'RESET' to continue: " confirm; \
	if [ "$$confirm" = "RESET" ]; then \
		python scripts/migration_utils.py downgrade base; \
		python scripts/migration_utils.py upgrade; \
		python scripts/seed_database.py seed; \
	else \
		echo "Operation cancelled"; \
	fi

db-status: ## Show database status
	@echo "$(BLUE)Database status:$(NC)"
	python scripts/migration_utils.py current
	python scripts/migration_utils.py validate

# Quick development workflows
quick-setup: setup-dev migrate seed ## Quick setup for new developers
	@echo "$(GREEN)Quick setup complete! Ready for development.$(NC)"

quick-test: format lint test-unit ## Quick test cycle
	@echo "$(GREEN)Quick test cycle complete!$(NC)"

quick-deploy: validate-all docker-build ## Quick deployment preparation
	@echo "$(GREEN)Ready for deployment!$(NC)"

# Banking-specific workflows
banking-validation: compliance-check security-scan audit-report ## Full banking validation
	@echo "$(GREEN)Banking validation complete!$(NC)"

production-ready: banking-validation test backup ## Ensure production readiness
	@echo "$(GREEN)Production readiness validated!$(NC)"