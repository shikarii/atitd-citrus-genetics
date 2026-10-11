.PHONY: sync format-python format-check-python lint-python loc-check test-python \
       format format-check lint test quality openapi \
       run-all run-all-fast run-compare run-simchecks dashboard \
       export-data build-web deploy \
       docker-build docker-up docker-down clean

# Python-only targets
sync:
	uv sync --group dev

format-python:
	uv run ruff format python/

format-check-python:
	uv run ruff format --check python/

loc-check:
	uv run python -m citrus_genetics.scripts.check_loc

lint-python:
	uv run python -m citrus_genetics.scripts.check_loc
	uv run ruff check python/
	uv run mypy
	uv run lint-imports

test-python:
	uv run pytest

# Aggregate targets (Python-only for Phase 1)
format: format-python

format-check: format-check-python

lint: lint-python

test: test-python

quality: format-check lint test

# OpenAPI
openapi:
	uv run python -c "from citrus_genetics.api.app import create_app; import json; app = create_app(); print(json.dumps(app.openapi(), indent=2))" > openapi.json

# Pipeline targets
run-all:
	uv run python -m citrus_genetics.cli.run_all --allow-dirty

run-all-fast:
	uv run python -m citrus_genetics.cli.run_all --allow-dirty --fast

run-compare:
	uv run python -m citrus_genetics.cli.run_compare

run-simchecks:
	uv run python -m citrus_genetics.cli.run_simchecks

# Dashboard
dashboard:
	uv run streamlit run python/citrus_genetics/dashboard/app.py

# Web dashboard
export-data:
	uv run python -m citrus_genetics.cli.export_web_data

build-web: export-data
	cd web && npm install && npm run build

deploy: run-all-fast build-web

# Docker targets
docker-build:
	docker compose build

docker-up:
	docker compose up -d --wait --wait-timeout 30

docker-down:
	docker compose down

# Cleanup
clean:
	rm -rf .mypy_cache .pytest_cache .ruff_cache coverage.xml htmlcov __pycache__
	find python -name __pycache__ -type d -exec rm -rf {} + 2>/dev/null || true
	find python -name "*.pyc" -delete 2>/dev/null || true
