# RAG Evaluation Services Makefile

.PHONY: help build up down logs health test clean rebuild

# Colors for output
GREEN=\033[0;32m
YELLOW=\033[1;33m
RED=\033[0;31m
NC=\033[0m # No Color

# Default target
help:
	@echo "$(GREEN)RAG Evaluation Services Management$(NC)"
	@echo ""
	@echo "$(YELLOW)Available targets:$(NC)"
	@echo "  build       - Build all RAG evaluation containers"
	@echo "  up          - Start RAG evaluation services"
	@echo "  down        - Stop RAG evaluation services"
	@echo "  logs        - View logs from all services"
	@echo "  logs-eval   - View logs from RAG evaluator service"
	@echo "  logs-dash   - View logs from RAG dashboard service"
	@echo "  logs-db     - View logs from metrics database"
	@echo "  health      - Check health of all services"
	@echo "  test        - Run tests against the services"
	@echo "  clean       - Remove containers and volumes"
	@echo "  rebuild     - Clean and rebuild everything"
	@echo "  shell-eval  - Open shell in RAG evaluator container"
	@echo "  shell-dash  - Open shell in RAG dashboard container"
	@echo "  shell-db    - Open shell in metrics database container"

# Build all containers
build:
	@echo "$(GREEN)Building RAG evaluation containers...$(NC)"
	docker-compose -f docker-compose.rag-eval.yml build --no-cache

# Start services
up:
	@echo "$(GREEN)Starting RAG evaluation services...$(NC)"
	docker-compose -f docker-compose.rag-eval.yml up -d
	@echo "$(YELLOW)Waiting for services to be ready...$(NC)"
	@sleep 10
	@$(MAKE) health

# Start services with logs
up-logs:
	@echo "$(GREEN)Starting RAG evaluation services with logs...$(NC)"
	docker-compose -f docker-compose.rag-eval.yml up

# Stop services
down:
	@echo "$(GREEN)Stopping RAG evaluation services...$(NC)"
	docker-compose -f docker-compose.rag-eval.yml down

# View logs from all services
logs:
	docker-compose -f docker-compose.rag-eval.yml logs -f

# View logs from specific services
logs-eval:
	docker-compose -f docker-compose.rag-eval.yml logs -f rag-evaluator

logs-dash:
	docker-compose -f docker-compose.rag-eval.yml logs -f rag-dashboard

logs-db:
	docker-compose -f docker-compose.rag-eval.yml logs -f rag-metrics-db

logs-proxy:
	docker-compose -f docker-compose.rag-eval.yml logs -f rag-proxy

# Health checks
health:
	@echo "$(GREEN)Checking RAG evaluation services health...$(NC)"
	@echo "$(YELLOW)Checking database...$(NC)"
	@docker-compose -f docker-compose.rag-eval.yml exec -T rag-metrics-db pg_isready -U rag_metrics_user -d rag_metrics || echo "$(RED)Database not ready$(NC)"
	@echo "$(YELLOW)Checking RAG evaluator...$(NC)"
	@curl -s -f http://localhost:8002/health > /dev/null && echo "$(GREEN)RAG Evaluator: OK$(NC)" || echo "$(RED)RAG Evaluator: FAIL$(NC)"
	@echo "$(YELLOW)Checking RAG dashboard...$(NC)"
	@curl -s -f http://localhost:3002/health > /dev/null && echo "$(GREEN)RAG Dashboard: OK$(NC)" || echo "$(RED)RAG Dashboard: FAIL$(NC)"
	@echo "$(YELLOW)Checking proxy...$(NC)"
	@curl -s -f http://localhost:8080/health > /dev/null && echo "$(GREEN)RAG Proxy: OK$(NC)" || echo "$(RED)RAG Proxy: FAIL$(NC)"

# Test the services
test:
	@echo "$(GREEN)Testing RAG evaluation services...$(NC)"
	@echo "$(YELLOW)Testing evaluator API...$(NC)"
	@curl -s -X POST http://localhost:8002/api/v1/rag/evaluate \
		-H "Content-Type: application/json" \
		-d '{"session_id": "test-session", "query": "test query", "retrieval_stage": {"stage": "retrieval", "start_time": 1, "end_time": 2, "latency_ms": 100}, "generation_stage": {"stage": "generation", "start_time": 2, "end_time": 3, "latency_ms": 200}}' \
		| python3 -m json.tool || echo "$(RED)Evaluator API test failed$(NC)"
	@echo "$(YELLOW)Testing dashboard...$(NC)"
	@curl -s -f http://localhost:3002 > /dev/null && echo "$(GREEN)Dashboard accessible$(NC)" || echo "$(RED)Dashboard not accessible$(NC)"

# Clean up containers and volumes
clean:
	@echo "$(GREEN)Cleaning up RAG evaluation services...$(NC)"
	docker-compose -f docker-compose.rag-eval.yml down -v --remove-orphans
	docker system prune -f
	@echo "$(YELLOW)Removing unused images...$(NC)"
	docker image prune -f

# Rebuild everything
rebuild: clean build up

# Shell access
shell-eval:
	docker-compose -f docker-compose.rag-eval.yml exec rag-evaluator /bin/bash

shell-dash:
	docker-compose -f docker-compose.rag-eval.yml exec rag-dashboard /bin/bash

shell-db:
	docker-compose -f docker-compose.rag-eval.yml exec rag-metrics-db psql -U rag_metrics_user -d rag_metrics

# Database operations
db-reset:
	@echo "$(YELLOW)Warning: This will reset the RAG metrics database!$(NC)"
	@read -p "Are you sure? [y/N] " -n 1 -r; \
	echo ""; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		docker-compose -f docker-compose.rag-eval.yml exec rag-metrics-db psql -U rag_metrics_user -d rag_metrics -c "TRUNCATE rag_sessions, rag_evaluations, rag_performance_aggregations RESTART IDENTITY CASCADE;"; \
		echo "$(GREEN)Database reset completed$(NC)"; \
	else \
		echo "$(YELLOW)Database reset cancelled$(NC)"; \
	fi

# Quick status check
status:
	@echo "$(GREEN)RAG Evaluation Services Status:$(NC)"
	docker-compose -f docker-compose.rag-eval.yml ps

# View running containers
ps:
	docker-compose -f docker-compose.rag-eval.yml ps

# Show resource usage
stats:
	docker stats --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}\t{{.PIDs}}" --no-stream