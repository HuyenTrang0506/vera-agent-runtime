PYTHON ?= python3.11

.PHONY: setup test lint demo eval ui check-setup audit-data generate-data docker-build docker-api docker-ui docker-eval

setup:
	$(PYTHON) -m venv .venv
	. .venv/bin/activate && python -m pip install --upgrade pip setuptools wheel
	. .venv/bin/activate && python -m pip install -e ".[dev]"

test:
	pytest

lint:
	ruff check app scripts tests ui

demo:
	python scripts/run_demo.py --fixture support_refund_happy_001

eval:
	python scripts/run_eval.py --benchmark data/benchmark/support_demo.jsonl

ui:
	npm --prefix ui run dev

check-setup:
	python scripts/check_setup.py

audit-data:
	python scripts/audit_test_data.py --benchmark data/benchmark/support_demo.jsonl
	python scripts/audit_test_data.py --benchmark data/benchmark/support_large_120.jsonl

generate-data:
	python scripts/generate_synthetic_support_data.py --count 120 --seed 42
	python scripts/build_demo_benchmark.py

docker-build:
	docker compose build

docker-api:
	docker compose up api

docker-ui:
	docker compose up ui

docker-eval:
	docker compose run --rm eval
