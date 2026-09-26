# RAGNAR Ω OMNI v33.0 — the production gate
.PHONY: install lint fmt type test ci docker up down health clean

install:
	pip install -e ".[dev,api]"

lint:
	ruff check src tests
	ruff format --check src tests

fmt:
	ruff check src tests --fix
	ruff format src tests

type:
	mypy src

test:
	pytest -q
	ragnar --test

ci: lint type test
	@echo "ALL GATES PASSED"

docker:
	docker compose build

up:
	docker compose up --build -d
	@echo "API on http://127.0.0.1:8000 — check .env first!"

down:
	docker compose down

health:
	curl -s http://127.0.0.1:8000/health | python3 -m json.tool

clean:
	rm -rf .pytest_cache .mypy_cache .ruff_cache build dist *.egg-info
	find . -name __pycache__ -type d -exec rm -rf {} + 2>/dev/null || true
