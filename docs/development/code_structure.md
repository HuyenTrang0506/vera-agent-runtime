# SafeFlow Code Structure

Generated on: 2026-07-02

Purpose: define the actual codebase structure developers must follow. This is not only a docs layout; it is the implementation structure for the project.

## Root Structure

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
|   `-- services/
+-- data/
|   +-- benchmark/
|   +-- fixtures/
|   |   +-- support/
|   |   `-- support_generated/
|   `-- results/
+-- docs/
|   +-- development/
|   +-- evaluation/
|   +-- product/
|   `-- research/
+-- scripts/
+-- tests/
|   +-- eval/
|   +-- integration/
|   `-- unit/
+-- ui/
|   +-- src/
|   `-- package.json
+-- AGENTS.md
+-- Dockerfile
+-- Makefile
+-- docker-compose.yml
`-- pyproject.toml
```

## Application Package

### `app/api/`

HTTP boundary only.

Allowed:

- FastAPI routers.
- Request/response models.
- Calling services.

Not allowed:

- Business policy.
- Tool internals.
- State mutation outside services.

### `app/core/`

Cross-cutting runtime utilities.

Files:

- `config.py`: all env-backed settings.
- `ids.py`: stable ID helpers.
- `logging.py`: logging setup.

Rule: do not call `os.getenv` outside `app/core/config.py`.

### `app/models/`

Typed contracts.

Owns:

- workflow request/response schemas,
- extraction schemas,
- domain state schemas,
- policy results,
- approval models,
- audit receipts,
- evaluation task schemas,
- enums.

Rule: if a model changes, update fixtures, tests, API callers, and docs in the same task.

### `app/services/`

Shared business services.

Owns:

- Qwen extraction,
- state loading/snapshot/hash,
- transition validation,
- policy decisions,
- action control,
- approvals,
- audit,
- idempotency,
- recovery/safe stop.

Rule: services may coordinate domain tools, but domain tools should not call services.

### `app/domains/support/`

P0 customer support domain.

Owns:

- support-specific schema aliases,
- mock support tools,
- policy IDs,
- workflow entrypoints.

Rule: support tools are deterministic functions. They do not call Qwen, policy services, or external APIs.

### `app/registries/`

Tool metadata.

P0:

- `support_tools.yaml`

Rule: registry metadata must match actual tool behavior and transition validators.

### `app/eval/`

Evaluation harness.

Owns:

- metrics,
- benchmark runner,
- baselines,
- reports.

Rule: eval reads logs/state; it does not control production workflow behavior.

## Data Structure

### `data/fixtures/`

Deterministic state fixtures.

- `support/`: hand-authored canonical fixtures.
- `support_generated/`: generated synthetic fixtures.

### `data/benchmark/`

JSONL benchmark tasks.

- `support_demo.jsonl`: balanced demo benchmark.
- `support_large_120.jsonl`: larger synthetic benchmark.

### `data/results/`

Generated outputs only. Do not commit run artifacts except `.gitkeep`.

## Scripts

Scripts are CLI entrypoints and development utilities.

Current scripts:

- `check_setup.py`: validates scaffold readiness.
- `generate_synthetic_support_data.py`: creates synthetic fixtures/benchmark tasks.
- `build_demo_benchmark.py`: builds balanced demo subset.
- `audit_test_data.py`: audits dataset quality and coverage.
- `run_demo.py`: demo runner.
- `run_eval.py`: evaluation runner.
- `seed_fixtures.py`: fixture seeding placeholder.

Rule: scripts should call app modules where possible. Do not duplicate business logic in scripts.

## Tests

### `tests/unit/`

Fast isolated tests for pure functions, schemas, policies, metrics, and validators.

### `tests/integration/`

Use case tests for UC1-UC6.

### `tests/eval/`

Benchmark/evaluation runner tests.

Rule: every completed task needs at least one relevant test or fixture-backed verification.

## UI

React/Vite app under `ui/`.

Allowed:

- operator console,
- fixture selector,
- workflow timeline,
- state diff,
- approval buttons,
- audit/metrics display.

Not allowed:

- core safety logic,
- policy decisions,
- direct fixture mutation.

## Adding New Code

Before adding a file, decide its layer:

| New Code | Put It In |
| --- | --- |
| API route | `app/api/` |
| Typed contract | `app/models/` |
| Cross-cutting business logic | `app/services/` |
| Support-domain tool | `app/domains/support/tools.py` |
| Tool metadata | `app/registries/` |
| Evaluation metric/runner | `app/eval/` |
| Benchmark/data utility | `scripts/` |
| React UI | `ui/src/` |
| Unit test | `tests/unit/` |
| Use-case test | `tests/integration/` |
| Eval test | `tests/eval/` |

If a new file does not fit this table, update this document before adding it.
