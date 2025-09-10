.PHONY: help build up down logs test clean deploy

# Variables
COMPOSE = podman-compose
PODMAN = podman
PROJECT_NAME = sdc
ENV_FILE = .env

# Colors for output
RED = \033[0;31m
GREEN = \033[0;32m
YELLOW = \033[1;33m
NC = \033[0m # No Color

help: ## Show this help message
	@echo '${GREEN}SDC - Smart Document Companion${NC}'
	@echo ''
	@echo 'Usage:'
	@echo '  ${YELLOW}make${NC} ${GREEN}<target>${NC}'
	@echo ''
	@echo 'Targets:'
	@awk 'BEGIN {FS = ":.*?## "} { \
		if (/^[a-zA-Z_-]+:.*?##/) \
			printf "  ${YELLOW}%-15s${NC} %s\n", $$1, $$2 \
		}' $(MAKEFILE_LIST)

# Development commands
install: ## Install all dependencies
	@echo "${GREEN}Installing frontend dependencies...${NC}"
	cd frontend && npm install
	@echo "${GREEN}Installing backend dependencies...${NC}"
	cd backend && pip install -r requirements.txt -r requirements-dev.txt

dev: ## Start development environment
	@echo "${GREEN}Starting development environment...${NC}"
	$(COMPOSE) up -d postgres redis
	@echo "${GREEN}Waiting for services...${NC}"
	sleep 5
	@echo "${GREEN}Starting backend...${NC}"
	cd backend && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 &
	@echo "${GREEN}Starting frontend...${NC}"
	cd frontend && npm run dev

build: ## Build all containers
	@echo "${GREEN}Building containers...${NC}"
	$(COMPOSE) build --no-cache

build-backend: ## Build backend container
	@echo "${GREEN}Building backend container...${NC}"
	$(PODMAN) build -f Containerfile --target backend-builder -t $(PROJECT_NAME)-backend:latest .

build-frontend: ## Build frontend container
	@echo "${GREEN}Building frontend container...${NC}"
	$(PODMAN) build -f Containerfile --target frontend-builder -t $(PROJECT_NAME)-frontend:latest .

up: ## Start all services
	@echo "${GREEN}Starting all services...${NC}"
	$(COMPOSE) up -d
	@echo "${GREEN}Services started. Checking health...${NC}"
	@sleep 10
	@make health

down: ## Stop all services
	@echo "${YELLOW}Stopping all services...${NC}"
	$(COMPOSE) down

restart: down up ## Restart all services

logs: ## Show logs
	$(COMPOSE) logs -f

logs-backend: ## Show backend logs
	$(COMPOSE) logs -f backend

logs-frontend: ## Show frontend logs
	$(COMPOSE) logs -f frontend

# Testing commands
test: ## Run all tests
	@echo "${GREEN}Running tests...${NC}"
	@make test-backend
	@make test-frontend

test-backend: ## Run backend tests
	@echo "${GREEN}Running backend tests...${NC}"
	@if [ ! -d backend/venv ]; then \
		echo "${YELLOW}Creating virtual environment...${NC}"; \
		cd backend && python -m venv venv; \
		echo "${YELLOW}Installing dependencies...${NC}"; \
		cd backend && bash -c "source venv/bin/activate && pip install pytest pytest-asyncio pytest-cov"; \
	fi
	cd backend && bash -c "source venv/bin/activate && python -m pytest simple_tests/ -v"

test-frontend: ## Run frontend tests
	@echo "${GREEN}Running frontend tests...${NC}"
	cd frontend && npm run test

test-integration: ## Run integration tests
	@echo "${GREEN}Running integration tests...${NC}"
	$(COMPOSE) up -d
	sleep 15
	cd backend && python -m pytest tests/integration/ -v
	$(COMPOSE) down

lint: ## Run linters
	@echo "${GREEN}Running linters...${NC}"
	@make lint-backend
	@make lint-frontend

lint-backend: ## Run backend linters
	@echo "${GREEN}Running backend linters...${NC}"
	cd backend && black app/ tests/ --check
	cd backend && ruff check app/ tests/
	cd backend && mypy app/

lint-frontend: ## Run frontend linters
	@echo "${GREEN}Running frontend linters...${NC}"
	cd frontend && npm run lint

format: ## Format code
	@echo "${GREEN}Formatting code...${NC}"
	cd backend && black app/ tests/
	cd frontend && npm run format

# Database commands
db-migrate: ## Run database migrations
	@echo "${GREEN}Running database migrations...${NC}"
	cd backend && alembic upgrade head

db-rollback: ## Rollback database migration
	@echo "${YELLOW}Rolling back database migration...${NC}"
	cd backend && alembic downgrade -1

db-reset: ## Reset database
	@echo "${RED}Resetting database...${NC}"
	$(COMPOSE) stop postgres
	$(COMPOSE) rm -f postgres
	docker volume rm $(PROJECT_NAME)_postgres_data || true
	$(COMPOSE) up -d postgres
	sleep 5
	@make db-migrate

# Monitoring commands
health: ## Check service health
	@echo "${GREEN}Checking service health...${NC}"
	@curl -f http://localhost:8000/health || echo "${RED}Backend is not healthy${NC}"
	@curl -f http://localhost:3000 || echo "${RED}Frontend is not healthy${NC}"
	@curl -f http://localhost:9200/_cluster/health || echo "${YELLOW}Elasticsearch is not ready${NC}"
	@curl -f http://localhost:19530/health || echo "${YELLOW}Milvus is not ready${NC}"

metrics: ## Show metrics
	@echo "${GREEN}Fetching metrics...${NC}"
	@curl -s http://localhost:8000/metrics | python -m json.tool

# Security commands
security-scan: ## Run security scan
	@echo "${GREEN}Running security scan...${NC}"
	cd backend && bandit -r app/
	cd backend && safety check
	trivy fs --security-checks vuln,config .

# Deployment commands
deploy-staging: ## Deploy to staging
	@echo "${GREEN}Deploying to staging...${NC}"
	./scripts/deploy.sh staging

deploy-production: ## Deploy to production
	@echo "${GREEN}Deploying to production...${NC}"
	@echo "${RED}Are you sure? [y/N]${NC}"
	@read ans && [ $$ans = y ]
	./scripts/deploy.sh production

# Cleanup commands
clean: ## Clean build artifacts
	@echo "${YELLOW}Cleaning build artifacts...${NC}"
	rm -rf frontend/.next frontend/out frontend/node_modules
	rm -rf backend/__pycache__ backend/.pytest_cache backend/.coverage
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete

clean-all: clean ## Clean everything including volumes
	@echo "${RED}Cleaning everything including volumes...${NC}"
	$(COMPOSE) down -v
	docker volume rm $(PROJECT_NAME)_postgres_data || true
	docker volume rm $(PROJECT_NAME)_redis_data || true
	docker volume rm $(PROJECT_NAME)_milvus_data || true
	docker volume rm $(PROJECT_NAME)_elasticsearch_data || true

reset: clean-all ## Full reset of the development environment
	@echo "${RED}Full reset of development environment...${NC}"
	@make install
	@make build
	@make up
	@make db-migrate

# Documentation commands
docs: ## Generate documentation
	@echo "${GREEN}Generating documentation...${NC}"
	cd backend && python -m pdoc --html --output-dir docs app
	cd frontend && npm run docs

# Backup commands
backup: ## Create backup
	@echo "${GREEN}Creating backup...${NC}"
	mkdir -p backups
	$(COMPOSE) exec postgres pg_dump -U sdc_user sdc_db > backups/db_$(shell date +%Y%m%d_%H%M%S).sql
	@echo "${GREEN}Backup created in backups/ directory${NC}"

restore: ## Restore from latest backup
	@echo "${YELLOW}Restoring from latest backup...${NC}"
	@latest=$$(ls -t backups/*.sql | head -1); \
	if [ -z "$$latest" ]; then \
		echo "${RED}No backup found${NC}"; \
		exit 1; \
	fi; \
	echo "Restoring from $$latest"; \
	$(COMPOSE) exec -T postgres psql -U sdc_user sdc_db < $$latest

# Utility commands
shell-backend: ## Open backend shell
	$(COMPOSE) exec backend /bin/bash

shell-frontend: ## Open frontend shell
	$(COMPOSE) exec frontend /bin/sh

shell-db: ## Open database shell
	$(COMPOSE) exec postgres psql -U sdc_user sdc_db

redis-cli: ## Open Redis CLI
	$(COMPOSE) exec redis redis-cli

# Development setup
setup: ## Initial project setup
	@echo "${GREEN}Setting up SDC project...${NC}"
	@cp .env.example .env 2>/dev/null || echo "${YELLOW}.env file already exists${NC}"
	@make install
	@make build
	@echo "${GREEN}Setup complete! Run 'make up' to start services${NC}"