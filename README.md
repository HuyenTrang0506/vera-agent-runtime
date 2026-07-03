# SafeFlow (VERA)

> **Rename recommendation for submission: VERA — Verified Execution Runtime for Agents**
>
> "SafeFlow" reads as generic middleware. "VERA" names the mechanism, sounds like a product, and is memorable in a 3-minute demo.

## The Problem

AI agents duplicate financial actions.

Standard tool-using agents call a refund API. The API times out. The agent retries. The customer gets refunded twice.

This happens because agents treat tool execution as successful/failed based on the API response code — not the actual business state. A timeout after commit looks identical to a timeout before commit. The agent cannot tell the difference.

## VERA's Solution

**Every tool in VERA's registry declares the state transition it produces.**

Before execution, VERA validates preconditions and policy. After execution, VERA reads actual business state and compares it to the declared transition effect. API timed out? VERA checks whether the refund committed. Already committed? Stop. Zero duplicate refunds.

This single mechanism also handles: unauthorized action prevention, approval gating for high-value transactions, policy enforcement, state mismatch escalation, and complete audit trails.

## Benchmark Results

Evaluated on 120 support cases, 5 repeated runs each:

| Metric | VERA | Baseline |
|---|---|---|
| Business Task Success Rate | **94.4%** | lower |
| Final State Exact Match | **100%** | — |
| Desired Transition Match | **100%** | — |
| Forbidden Transitions | **0** | non-zero |
| Duplicate Refunds | **0** | non-zero on timeout cases |
| Approval Recall | **100%** | — |
| Audit Completeness | **100%** | — |

Baseline is the same Qwen model using tool names, descriptions, and schemas only — no transition metadata.

## What It Does

- Extract intent and desired state transition from customer emails using Qwen.
- Inspect customer, order, payment, refund, and ticket state.
- Select tools by declared transition affordance, not description alone.
- Enforce preconditions, policy, and approval gates.
- Validate observed state change matches declared transition effect.
- Detect timeout-after-commit and prevent duplicate refunds on retry.
- Route high-value refunds to human approval; block after rejection.
- Escalate on state mismatch; stop consequential actions immediately.
- Produce complete audit receipts for every consequential decision.

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
