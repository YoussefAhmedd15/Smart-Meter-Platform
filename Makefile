.PHONY: install seed test run-backend run-frontend docker-up docker-down help

help:
	@echo "Smart Meter Intelligence Platform Commands:"
	@echo "  make install        Install Python backend & Node frontend dependencies"
	@echo "  make seed           Populate demo dataset into PostgreSQL / SQLite"
	@echo "  make test           Run unit test suites across meter engine and API"
	@echo "  make run-backend    Start FastAPI server on port 8000"
	@echo "  make run-frontend   Start Vite React dashboard on port 3000"
	@echo "  make docker-up      Launch full stack with Docker Compose"
	@echo "  make docker-down    Stop Docker Compose containers"

install:
	pip install -r requirements.txt
	cd frontend && npm install

seed:
	python scripts/seed_demo.py

test:
	python -m unittest meter/tests/test_meter.py

run-backend:
	uvicorn backend.app.main:app --reload --port 8000

run-frontend:
	cd frontend && npm run dev

docker-up:
	docker-compose up --build -d

docker-down:
	docker-compose down
