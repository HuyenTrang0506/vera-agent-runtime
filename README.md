# SafeFlow

**SafeFlow** is a Qwen-powered enterprise Autopilot Agent with **State-Transition-Aware Action Control**.

It automates support workflows through external tools while checking intended business state transitions, validating observed state, preventing duplicate side effects, routing risky actions to approval, and producing audit receipts.

## What It Does

P0 focuses on customer-support refund automation:

- Understand refund requests with Qwen or fixture fallback.
- Inspect customer, order, payment, refund, and ticket state.
- Select tools by expected state transition, not only tool description.
- Enforce policy and approval gates.
- Prevent duplicate refunds after retry or timeout.
- Validate final business state.
- Emit audit receipts and evaluation metrics.

## Quick Start

Use Python 3.11+.

```bash
make setup
source .venv/bin/activate
cp .env.example .env
make check-setup
make test
```

If `make setup` cannot find Python 3.11, run:

```bash
make setup PYTHON=/opt/homebrew/bin/python3.11
```

## Run

API:

```bash
source .venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

UI:

```bash
npm --prefix ui install
npm --prefix ui run dev
```

Demo CLI:

```bash
python scripts/run_demo.py --fixture support_refund_happy_001
```

Evaluation CLI:

```bash
python scripts/run_eval.py --benchmark data/benchmark/support_demo.jsonl
```

## Docker

```bash
cp .env.example .env
docker compose build
docker compose up api
docker compose up ui
docker compose run --rm eval
```

## Test And Quality Checks

```bash
make test
make lint
make audit-data
npm --prefix ui run build
npm --prefix ui run lint
```

## Data

SafeFlow uses deterministic synthetic fixtures for reproducible evaluation.

Main benchmark files:

- `data/benchmark/support_demo.jsonl` - balanced 32-case P0 demo benchmark.
- `data/benchmark/support_large_120.jsonl` - larger 120-case synthetic benchmark.

Regenerate and audit data:

```bash
make generate-data
make audit-data
```

## Project Structure

```text
app/        FastAPI backend, models, services, domain tools, evaluation code
ui/         React/Vite operator console
scripts/    setup, data generation, demo, and evaluation commands
data/       fixtures, benchmark tasks, generated results
tests/      unit, integration, and evaluation tests
docs/       product, development, evaluation, and research documentation
```

## Configuration

Copy `.env.example` to `.env`.

Important settings:

```text
QWEN_API_KEY=
QWEN_MODEL=qwen3.7-plus
SAFEFLOW_MODEL_MODE=fixture_fallback
SAFEFLOW_API_PORT=8000
SAFEFLOW_UI_PORT=5173
```

Other account quota options can be copied from `.env.example` if the default model expires or becomes unavailable.

For offline/local testing, keep:

```text
SAFEFLOW_MODEL_MODE=fixture_fallback
```

## Project Docs

- Product requirements: `docs/product/mvp_product_requirements.md`
- Development conventions: `docs/development/project_conventions.md`
- Code structure: `docs/development/code_structure.md`
- Setup decisions: `docs/development/setup_decisions.md`
- Test data criteria: `docs/development/test_data_criteria.md`
