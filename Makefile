.PHONY: install dev lint format typecheck test run migrate up down frontend frontend-dev

install:
	pip install -r requirements-dev.txt

lint:
	ruff check app tests

format:
	ruff format app tests

typecheck:
	mypy app

test:
	pytest

run:
	uvicorn app.main:app --reload

migrate:
	alembic upgrade head

up:
	docker compose up --build

down:
	docker compose down -v

# 构建前端并启动后端（生产模式）
frontend:
	cd frontend && npm install && npm run build
	uvicorn app.main:app --host 0.0.0.0 --port 8000

# 开发模式：同时启动前端和后端
frontend-dev:
	start /B cmd /C "cd frontend && npm run dev"
	uvicorn app.main:app --reload
