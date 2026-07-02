# SafeFlow Setup Decisions

Generated on: 2026-07-02

Purpose: decide what infrastructure, services, data, and setup are required before implementing MVP tasks.

## 1. Short Answer

For the P0 MVP:

- Stripe: **No**.
- Redis: **No**.
- External database: **No**.
- SQLite: **No for P0**, optional P1 if runtime persistence becomes painful.
- Public online database: **No as source-of-truth**.
- Required data: **synthetic deterministic fixtures with oracle final predicates**.
- Python virtualenv: **Yes for local development**.
- Docker: **Yes as optional reproducible runtime**, but not as a reason to add Redis/DB.

The MVP should run offline in fixture fallback mode. Qwen live calls are useful for demo realism, but the system must still run without network or model access.

## 2. Why No Stripe?

SafeFlow must not execute real financial actions. The MVP only needs a mock `create_refund` tool that mutates local fixture state.

Stripe would add:

- account setup,
- secrets,
- real API behavior,
- payment/refund semantics,
- network instability,
- compliance concerns,
- demo risk.

None of that strengthens the core research claim. The claim is about controlling state-changing actions, not integrating with a real payment provider.

Decision: use `app/domains/support/tools.py` mock tools and deterministic state fixtures.

## 3. Why No Redis?

Redis is usually useful for queues, locks, cache, rate limits, pub/sub, and distributed session state. P0 is a modular monolith with one local process and deterministic fixtures.

Redis would add operational overhead without proving the transition-aware action-control mechanism.

Decision: use in-memory runtime state and JSON result snapshots for P0.

Possible P1 use:

- concurrency/race-condition experiments,
- cross-process workflow state,
- distributed locks.

## 4. Why No External DB For P0?

The benchmark needs:

- exact initial state,
- expected final predicates,
- forbidden predicates,
- deterministic failure modes,
- repeatable runs,
- state hashes,
- audit receipts.

JSON fixtures are simpler, inspectable, and reproducible. A database is only useful after the state model stabilizes.

Decision:

- Fixtures: `data/fixtures/support/*.json`.
- Benchmark tasks: `data/benchmark/support_demo.jsonl`.
- Runtime state: in memory.
- Output snapshots: `data/results/`.

Optional P1:

- SQLite for workflow history if React/API state becomes annoying.

## 5. Can We Use A Public Online DB?

Not as the benchmark source-of-truth.

Public datasets may contain support tickets, invoice examples, or ecommerce records, but they usually do not include:

- tool preconditions,
- exact business state transitions,
- side-effect labels,
- approval requirements,
- idempotency keys,
- final-state oracle predicates,
- failure injections,
- forbidden transition labels.

Using a public DB would make evaluation weaker, not stronger, unless we manually wrap it with synthetic state and oracle labels.

Allowed use later:

- Use public text-only samples for more realistic customer-request wording.
- Keep all state, policies, tools, and expected outcomes synthetic and deterministic.
- Never use real personal data in fixtures.

## 6. Required Data Before Coding

P0 requires these support fixtures:

| Fixture ID | Purpose | Required State |
| --- | --- | --- |
| `support_refund_happy_001` | Happy-path duplicate refund | duplicate captured payment, no refund, below threshold |
| `support_refund_timeout_after_commit_001` | Duplicate prevention | same as happy path, `failure_mode=timeout_after_commit` |
| `support_refund_high_value_approve_001` | Approval allow path | duplicate payment amount >= 500, approval script approves |
| `support_refund_high_value_reject_001` | Approval rejection | duplicate payment amount >= 500, approval script rejects |
| `support_refund_no_duplicate_001` | Safe denial | one captured payment, no duplicate |
| `support_tool_mismatch_001` | State mismatch escalation | tool returns success but state delta is wrong |

Each fixture must include:

- `fixture_id`
- initial `state`
- `expected_extraction`
- optional `failure_mode`
- optional `approval_script`

Each benchmark task must include:

- `task_id`
- `domain`
- `fixture_id`
- `request_text`
- `failure_mode`
- `expected_final_predicates`
- `forbidden_predicates`
- optional `approval_script`

## 7. Setup Commands

### Local Development

Use a virtualenv locally. It keeps hackathon dependencies isolated and avoids global Python issues.

```bash
make setup
make check-setup
make test
make demo
make eval
make ui
```

Without `make`:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
python scripts/check_setup.py
pytest
python scripts/run_demo.py --fixture support_refund_happy_001
python scripts/run_eval.py --benchmark data/benchmark/support_demo.jsonl
npm --prefix ui install
npm --prefix ui run dev
```

### Docker

Docker is useful for demo reproducibility and "production-shaped" packaging.

Docker does not mean P0 needs Redis, Stripe, Postgres, or other services.

```bash
cp .env.example .env
docker compose build
docker compose up api
docker compose up ui
docker compose run --rm eval
```

Services:

- `api`: FastAPI app on `SAFEFLOW_API_PORT`, default `8000`.
- `ui`: React/Vite console on `SAFEFLOW_UI_PORT`, default `5173`.
- `eval`: one-shot benchmark runner.

## 8. Large Synthetic Data

SafeFlow can generate a large synthetic support dataset with deterministic oracle predicates.

Use:

```bash
python scripts/generate_synthetic_support_data.py --count 120 --seed 42
```

Default output:

```text
data/fixtures/support_generated/
data/benchmark/support_large_120.jsonl
```

For larger runs:

```bash
python scripts/generate_synthetic_support_data.py \
  --count 1000 \
  --seed 42 \
  --fixtures-dir data/fixtures/support_generated_1000 \
  --benchmark-path data/benchmark/support_large_1000.jsonl
```

Generated data is synthetic. It is appropriate for benchmark scale tests because it includes:

- initial state,
- expected extraction,
- failure mode,
- approval script,
- expected final predicates,
- forbidden predicates.

## 9. Setup Readiness Checklist

- `pyproject.toml` exists.
- `.env.example` exists.
- `AGENTS.md` exists.
- `app/` package imports.
- `data/fixtures/support/` exists.
- `data/benchmark/support_demo.jsonl` exists.
- `data/results/.gitkeep` exists.
- `scripts/run_demo.py` exists.
- `scripts/run_eval.py` exists.
- `scripts/check_setup.py` exists.
- `scripts/generate_synthetic_support_data.py` exists.
- `Dockerfile` exists.
- `docker-compose.yml` exists.
- `ui/package.json` exists.
- `tests/` exists.
