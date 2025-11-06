.PHONY: help dev build up down logs clean test lint format migrate seed

# Default target
help:
	@echo "Available commands:"
	@echo "  make dev          - Start development environment"
	@echo "  make build        - Build all Docker images"
	@echo "  make up           - Start all services"
	@echo "  make down         - Stop all services"
	@echo "  make logs         - View logs from all services"
	@echo "  make clean        - Clean up containers, volumes, and caches"
	@echo "  make test         - Run all tests"
	@echo "  make lint         - Run linters"
	@echo "  make format       - Format code"
	@echo "  make migrate      - Run database migrations"
	@echo "  make seed         - Seed database with sample data"
	@echo "  make shell-backend - Open shell in backend container"
	@echo "  make shell-db     - Open PostgreSQL shell"

# Development
dev:
	@echo "Starting development environment..."
	docker-compose up -d postgres redis
	@echo "Waiting for services to be ready..."
	@sleep 5
	@echo "Services are ready! You can now run backend and frontend separately."

# Docker operations
build:
	@echo "Building Docker images..."
	docker-compose build

up:
	@echo "Starting all services..."
	docker-compose up -d

down:
	@echo "Stopping all services..."
	docker-compose down

restart:
	@echo "Restarting all services..."
	docker-compose restart

logs:
	docker-compose logs -f

logs-backend:
	docker-compose logs -f backend

logs-frontend:
	docker-compose logs -f frontend

# Database operations
migrate:
	@echo "Running database migrations..."
	cd backend && poetry run alembic upgrade head

migrate-create:
	@echo "Creating new migration..."
	@read -p "Enter migration message: " msg; \
	cd backend && poetry run alembic revision --autogenerate -m "$$msg"

migrate-down:
	@echo "Rolling back last migration..."
	cd backend && poetry run alembic downgrade -1

seed:
	@echo "Seeding database..."
	cd backend && poetry run python scripts/seed_db.py

# Testing
test:
	@echo "Running backend tests..."
	cd backend && poetry run pytest
	@echo "Running frontend tests..."
	cd frontend && npm test

test-backend:
	cd backend && poetry run pytest -v

test-frontend:
	cd frontend && npm test

test-e2e:
	cd frontend && npm run test:e2e

test-coverage:
	cd backend && poetry run pytest --cov=app --cov-report=html

# Linting and formatting
lint:
	@echo "Linting backend..."
	cd backend && poetry run flake8 app
	cd backend && poetry run mypy app
	@echo "Linting frontend..."
	cd frontend && npm run lint

format:
	@echo "Formatting backend..."
	cd backend && poetry run black app
	cd backend && poetry run isort app
	@echo "Formatting frontend..."
	cd frontend && npm run format

# Shell access
shell-backend:
	docker-compose exec backend /bin/bash

shell-db:
	docker-compose exec postgres psql -U postgres -d app

shell-redis:
	docker-compose exec redis redis-cli

# Cleanup
clean:
	@echo "Cleaning up..."
	docker-compose down -v
	@echo "Removing Python cache..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	@echo "Removing Node modules cache..."
	rm -rf frontend/node_modules/.cache
	@echo "Cleanup complete!"

clean-all: clean
	@echo "Removing all Docker images..."
	docker-compose down -v --rmi all
	@echo "Removing node_modules and virtual environments..."
	rm -rf frontend/node_modules
	rm -rf backend/.venv
	@echo "Deep cleanup complete!"

# Installation
install:
	@echo "Installing dependencies..."
	@echo "Installing backend dependencies..."
	cd backend && poetry install
	@echo "Installing frontend dependencies..."
	cd frontend && npm install
	@echo "Installation complete!"

# Production build
build-prod:
	@echo "Building production images..."
	docker-compose -f docker-compose.prod.yml build

deploy-prod:
	@echo "Deploying to production..."
	docker-compose -f docker-compose.prod.yml up -d

# Health checks
health:
	@echo "Checking service health..."
	@curl -f http://localhost:8000/health && echo "Backend: ✓" || echo "Backend: ✗"
	@curl -f http://localhost/health && echo "Frontend: ✓" || echo "Frontend: ✗"
	@curl -f http://localhost:9090/-/healthy && echo "Prometheus: ✓" || echo "Prometheus: ✗"

# Monitoring
stats:
	docker stats

ps:
	docker-compose ps
