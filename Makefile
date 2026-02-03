.PHONY: help install dev build start stop logs clean test lint

# Default target
help:
	@echo "mikroKSeF - Available commands:"
	@echo ""
	@echo "  make install    - Install all dependencies"
	@echo "  make dev        - Start development servers"
	@echo "  make build      - Build Docker images"
	@echo "  make start      - Start production containers"
	@echo "  make stop       - Stop all containers"
	@echo "  make logs       - View container logs"
	@echo "  make clean      - Remove containers and volumes"
	@echo "  make test       - Run all tests"
	@echo "  make lint       - Run linters"
	@echo ""

# Install dependencies
install:
	@echo "Installing backend dependencies..."
	cd backend && python -m venv venv && . venv/bin/activate && pip install -r requirements.txt -r requirements-dev.txt
	@echo "Installing frontend dependencies..."
	cd frontend && npm ci
	@echo "Done! Copy .env.example to .env and configure your credentials."

# Development mode (local)
dev:
	@echo "Starting development servers..."
	@echo "Backend: http://localhost:8000"
	@echo "Frontend: http://localhost:3000"
	@echo ""
	@trap 'kill 0' SIGINT; \
	(cd backend && . venv/bin/activate && uvicorn app.main:app --reload --port 8000) & \
	(cd frontend && npm run dev) & \
	wait

# Development mode (Docker)
dev-docker:
	docker-compose -f docker-compose.dev.yml up --build

# Build Docker images
build:
	docker-compose build

# Start production containers
start:
	docker-compose up -d
	@echo "Services started:"
	@echo "  Backend:  http://localhost:8000"
	@echo "  Frontend: http://localhost:3000"
	@echo "  API Docs: http://localhost:8000/docs"

# Stop containers
stop:
	docker-compose down

# View logs
logs:
	docker-compose logs -f

# Clean up
clean:
	docker-compose down -v --remove-orphans
	rm -rf backend/data/*.db
	rm -rf frontend/.next
	rm -rf frontend/node_modules/.cache
	@echo "Cleanup complete"

# Run all tests
test: test-backend test-frontend

# Backend tests
test-backend:
	cd backend && . venv/bin/activate && pytest tests/ -v --cov=app

# Frontend tests
test-frontend:
	cd frontend && npm run test

# Lint code
lint: lint-backend lint-frontend

lint-backend:
	cd backend && . venv/bin/activate && ruff check app/ && mypy app/

lint-frontend:
	cd frontend && npm run lint

# Format code
format:
	cd backend && . venv/bin/activate && black app/ tests/
	cd frontend && npm run lint -- --fix

# Database operations
db-reset:
	rm -f backend/data/*.db
	@echo "Database reset complete"

# Generate requirements.txt from pyproject.toml
requirements:
	cd backend && pip-compile pyproject.toml -o requirements.txt
