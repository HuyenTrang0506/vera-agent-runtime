# SafeFlow Research And MVP Scaffold

This repository contains research, evaluation design, MVP planning, and the initial implementation scaffold for:

**SafeFlow - a Qwen-powered enterprise Autopilot Agent with State-Transition-Aware Action Control.**

The project focuses on safe enterprise workflow automation where agents execute real business actions through tools, validate resulting state, prevent duplicate side effects, and route risky actions to human approval.

## Current Structure

```text
.
+-- app/
|   +-- api/
|   +-- core/
|   +-- domains/
|   |   `-- support/
|   +-- eval/
|   +-- models/
|   +-- registries/
|   +-- services/
|   `-- main.py
+-- data/
|   +-- fixtures/
|   |   `-- support/
|   +-- benchmark/
|   +-- results/
|   +-- phase1/
|   |   `-- framework_database.csv
|   `-- analysis/
|       +-- gap_ranking.csv
|       +-- industrial_problem_matrix.csv
|       +-- issues_database.csv
|       `-- micro_gap_database.csv
+-- docs/
|   +-- development/
|   |   `-- project_conventions.md
|   +-- evaluation/
|   |   `-- state_transition_evaluation_metrics.md
|   +-- product/
|   |   `-- mvp_product_requirements.md
|   +-- research/
|   |   +-- failure_patterns.md
|   |   +-- framework_summary.md
|   |   +-- industrial_problem_brief.md
|   |   `-- qwen_hackathon_topic_fit.md
|   `-- scripts/
|       +-- collect_phase1_frameworks.py
|       `-- run_research_analysis.py
+-- scripts/
|   +-- run_demo.py
|   +-- run_eval.py
|   `-- seed_fixtures.py
+-- tests/
|   +-- eval/
|   +-- integration/
|   `-- unit/
+-- ui/
|   +-- package.json
|   `-- src/
+-- AGENTS.md
+-- hackathon_plan.md
+-- pyproject.toml
`-- README.md
```

## Key Docs

- [MVP Product Requirements](docs/product/mvp_product_requirements.md)
- [Development Conventions](docs/development/project_conventions.md)
- [Setup Decisions](docs/development/setup_decisions.md)
- [Evaluation Metrics Framework](docs/evaluation/state_transition_evaluation_metrics.md)
- [Industrial Problem Brief](docs/research/industrial_problem_brief.md)
- [Qwen Hackathon Topic Fit](docs/research/qwen_hackathon_topic_fit.md)
- [Failure Patterns](docs/research/failure_patterns.md)
- [Framework Summary](docs/research/framework_summary.md)

## Selected Direction

The selected problem is unsafe autonomous tool execution in enterprise workflows.

The product framing is:

> A Qwen-powered Autopilot Agent for safe end-to-end business workflow automation, using state-transition-aware action control.

The P0 MVP domain is:

- Customer support: duplicate charge, refund, ticket update, customer response.

Finance operations are P1 and should not block the P0 support workflow.

## Development Scaffold

The codebase now follows the project convention in [AGENTS.md](AGENTS.md) and [docs/development/project_conventions.md](docs/development/project_conventions.md).

Core scaffold:

- `app/models/` - Pydantic contracts and enums.
- `app/services/` - Qwen, state, transition, policy, action control, approval, audit, idempotency, recovery.
- `app/domains/support/` - P0 support domain schema, tools, policies, workflows.
- `app/eval/` - benchmark runner, metrics, baseline, reports.
- `app/registries/support_tools.yaml` - P0 tool metadata contract example.
- `data/fixtures/support/` - deterministic support fixtures.
- `data/benchmark/support_demo.jsonl` - starter benchmark file.
- `ui/` - React/Vite operator console scaffold.
- `scripts/run_demo.py` and `scripts/run_eval.py` - CLI entrypoints.

## Setup

P0 does not require Stripe, Redis, or an external database. It uses deterministic JSON fixtures, in-memory runtime state, and JSON result snapshots. See [docs/development/setup_decisions.md](docs/development/setup_decisions.md).

Use a virtualenv for local development. Docker is available for reproducible API/UI/eval runs, but P0 intentionally avoids external infrastructure.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env
```

## Run Scaffold

```bash
python scripts/check_setup.py
python scripts/run_demo.py --fixture support_refund_happy_001
python scripts/run_eval.py --benchmark data/benchmark/support_demo.jsonl
npm --prefix ui install
npm --prefix ui run dev
pytest
```

With `make`:

```bash
make setup
make check-setup
make test
make demo
make eval
make ui
```

## Docker

```bash
cp .env.example .env
docker compose build
docker compose up api
docker compose up ui
docker compose run --rm eval
```

## Generate Larger Synthetic Data

```bash
python scripts/generate_synthetic_support_data.py --count 120 --seed 42
python scripts/build_demo_benchmark.py
python scripts/audit_test_data.py --benchmark data/benchmark/support_large_120.jsonl
```

This writes:

- `data/fixtures/support_generated/`
- `data/benchmark/support_large_120.jsonl`
- balanced 20-case `data/benchmark/support_demo.jsonl`

See [docs/development/test_data_criteria.md](docs/development/test_data_criteria.md) for data quality criteria and current dataset assessment.

## Regenerate Research Artifacts

```bash
python3 docs/scripts/collect_phase1_frameworks.py
python3 docs/scripts/run_research_analysis.py
```

## MVP Delivery Framework

The MVP plan uses Scrum-lite with Kanban execution inside each sprint:

- Sprint 0: setup and scope lock.
- Sprint 1: end-to-end happy path.
- Sprint 2: safety, policy, approval, and recovery.
- Sprint 3: evaluation and demo polish.

See [docs/product/mvp_product_requirements.md](docs/product/mvp_product_requirements.md) for backlog, use cases, acceptance criteria, architecture, and definition of done.
