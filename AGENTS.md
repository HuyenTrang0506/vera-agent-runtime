# SafeFlow Development Conventions

These conventions apply to the whole repository.

## Product Scope

- Build toward the P0 MVP in `docs/product/mvp_product_requirements.md`.
- P0 is customer-support duplicate-charge refund automation only.
- Finance, LangGraph baseline, larger benchmark exports, policy conflict tests, and concurrency tests are P1/P2 unless explicitly requested.
- Do not add production integrations, real payment/refund APIs, real customer data, tenant management, RBAC, long-term memory, or model fine-tuning for MVP work.

## Architecture

- Use a Python modular monolith for MVP.
- Keep domain tools as typed Python functions.
- Keep shared behavior in services: Qwen calls, state, transitions, policy, action control, approval, audit, idempotency, recovery, and evaluation.
- Do not introduce microservices, background queues, external databases, or new frameworks unless the user explicitly asks.
- P0 state storage is deterministic JSON fixtures plus in-memory runtime state and JSON result snapshots.

## Configuration

- Do not hardcode environment-specific values in application code.
- Read configurable values through `app/core/config.py` and `.env`.
- Keep `.env.example` updated whenever a new setting is introduced.
- Hardcoded constants are allowed only for stable domain semantics, such as enum values, policy IDs, transition IDs, and test fixture IDs.
- Do not hardcode secrets, API keys, model names, paths, hostnames, ports, thresholds, or feature flags inside business logic.
- Use explicit defaults only in `app/core/config.py`, docs, or test fixtures.

## Implementation Order

Prefer this order when building:

1. Domain models and fixtures.
2. Qwen extraction schema and fixture fallback.
3. Tool registry schema.
4. State service and mock tools.
5. Policy and action controller.
6. Audit and idempotency.
7. Evaluation runner and baseline.
8. React/Vite demo UI.

If a feature cannot be tested through a fixture or metric, keep it out of P0.

## State And Safety

- Every consequential action must have a pre-state snapshot, post-state snapshot, state hash, and audit receipt.
- `create_refund` must require an idempotency key.
- Never execute `create_refund` after approval rejection.
- Never execute another consequential action after `escalated_state_mismatch`.
- Timeout-after-commit must recheck state before retry.
- Financial rollback is out of scope for P0; use safe stop and escalation instead.

## Models And LLM Calls

- Qwen output must be validated against a typed schema.
- Invalid JSON gets at most one repair attempt.
- If Qwen is unavailable, use fixture fallback only when the run explicitly enables fallback mode.
- Audit whether the run used live Qwen or fixture fallback.
- Keep prompts and output schemas versioned in code or registry files.

## Evaluation

- Evaluation is part of P0, not final polish.
- Baseline must use the same Qwen model and same tool execution environment.
- Baseline sees tool names, descriptions, and schemas only.
- SafeFlow may use transition metadata, preconditions, policy, idempotency, and post-state validation.
- Required P0 benchmark size is 20 support cases with 5 repeated runs per case.
- Metrics must be computed from structured logs and final state, not human preference.

## Code Style

- Use Python 3.11+.
- Use Pydantic for external contracts, LLM outputs, API payloads, and benchmark task schemas.
- Keep functions small and deterministic where possible.
- Avoid hidden global state except configuration constants.
- Prefer explicit enums for statuses, policy decisions, risk levels, and workflow states.
- Do not use ad hoc string parsing when structured models or validators are available.

## Tests

- Add unit tests for policies, preconditions, idempotency, state validation, and metrics.
- Add integration tests for UC1 through UC5 in the PRD.
- Every bug fix for a workflow failure should add or update a fixture/test.
- Tests must run offline without Qwen by using fixture fallback.
- Every completed task must have its relevant tests run before being marked done.
- Once a task is marked done, treat its implementation and tests as protected.
- New code must adapt to existing project structure, schemas, fixtures, and tests.
- Change shared contracts only with a clear reason, updated docs, and regression tests.

## Task Completion Discipline

- Do not mark a task done until its acceptance criteria pass.
- Do not mark a task done if it only works manually but has no repeatable test or fixture.
- Prefer additive changes for new tasks.
- Avoid refactoring completed code while implementing unrelated tasks.
- Keep old behavior passing unless the PRD explicitly changes it.
- A task completion note should include commands run and any skipped checks.

## Documentation

- Update `docs/product/mvp_product_requirements.md` if scope, ACs, schemas, or sprint commitments change.
- Update `docs/development/project_conventions.md` if team conventions change.
- Keep docs ASCII unless quoting source material.

## Commands

When implementation exists, expected commands are:

```bash
python scripts/run_demo.py --fixture support_refund_happy_001
python scripts/run_eval.py --benchmark data/benchmark/support_demo.jsonl
npm --prefix ui run dev
pytest
```
