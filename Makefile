# =========================================
# Docker Orchestration
# =========================================
docker-up:
	docker compose up --build

docker-down:
	docker compose down

docker-build:
	docker compose build

docker-restart:
	docker compose down
	docker compose up --build


# =========================================
# Backend
# =========================================
backend-tests:
	docker compose run --rm backend pytest -q

backend-shell:
	docker compose run --rm backend bash

backend-logs:
	docker compose logs -f backend


# =========================================
# Frontend
# =========================================
frontend-shell:
	docker compose run --rm frontend sh

frontend-logs:
	docker compose logs -f frontend


# =========================================
# Project Utils
# =========================================
clean:
	docker compose down --volumes --remove-orphans
