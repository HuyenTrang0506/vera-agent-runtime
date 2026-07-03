# SafeFlow Project Conventions

Generated on: 2026-07-01

Purpose: define development rules for the SafeFlow MVP so product, engineering, research, and demo work stay aligned during the 10-12 day Qwen Hackathon build.

Primary source of product truth: `docs/product/mvp_product_requirements.md`.

Setup and infrastructure decisions live in `docs/development/setup_decisions.md`.

## 1. Scope Rules

### P0 Means Customer Support Only

P0 implementation must focus on:

- Duplicate-charge refund.
- High-value refund approval.
- Approval rejection.
- Timeout-after-commit duplicate prevention.
- No-duplicate-charge denial.
- State mismatch escalation.
- Audit receipt.
- Baseline comparison.
- 20-case support benchmark.

Finance is P1. Do not let finance work block customer-support P0.

### No Production Integrations In MVP

Do not implement:

- Real payment/refund APIs.
- Real CRM/ERP/HRIS/ITSM integrations.
- Real customer data.
- Production auth, tenant management, or RBAC.
- Long-term memory.
- Full policy DSL.
- Model fine-tuning.
- Financial rollback.

MVP should prove the control mechanism, not simulate an entire enterprise stack.

## 2. Architecture Rules

Use a modular monolith.

Required boundaries:

| Layer | Owns | Must Not Own |
| --- | --- | --- |
| `api/` | HTTP request/response routing | Business decisions |
| `models/` | Pydantic contracts and enums | Tool execution |
| `services/qwen_service.py` | Qwen calls, schema validation, fixture fallback | Business policy |
| `services/state_service.py` | Fixtures, runtime state, snapshots, hashes | Tool selection |
| `services/transition_service.py` | Intended/observed transition validation | LLM calls |
| `services/policy_service.py` | Policy predicates and decisions | Tool execution |
| `services/action_controller.py` | Decision table and tool gating | Domain-specific tool internals |
| `services/approval_service.py` | Approval lifecycle | Refund creation |
| `services/audit_service.py` | Audit receipts | Policy decisions |
| `services/idempotency_service.py` | Idempotency keys and duplicate detection | State mutation outside idempotency records |
| `domains/support/tools.py` | Mock support tools | Policy or LLM calls |
| `eval/` | Benchmark runner, baseline, metrics | Product workflow control |
| `ui/` | Demo display and approval buttons | Core safety logic |

## 3. Configuration And Environment Rules

Do not hardcode environment-specific values.

All configurable values must be read through `app/core/config.py` and environment variables.

Examples that must come from env/settings:

- Qwen API key.
- Qwen model name.
- model mode: `qwen` or `fixture_fallback`.
- fixture directory.
- benchmark path.
- results directory.
- API host and port.
- UI host and port.
- refund approval threshold.
- max extraction repair attempts.
- repeated run count.
- random seed.

Allowed hardcoded values:

- enum values.
- transition IDs.
- policy rule IDs.
- stable test fixture IDs.
- domain lifecycle states.

Rules:

- Add every new env var to `.env.example`.
- Do not read `os.getenv` directly outside `app/core/config.py`.
- Pass settings into services or import `settings` from `app/core/config.py`.
- Never commit `.env`.
- Never put secrets in fixtures, benchmark files, docs, or tests.

Current P0 env vars:

```text
QWEN_API_KEY
QWEN_MODEL
SAFEFLOW_MODEL_MODE
SAFEFLOW_RESULTS_DIR
SAFEFLOW_FIXTURES_DIR
SAFEFLOW_BENCHMARK_PATH
SAFEFLOW_API_HOST
SAFEFLOW_API_PORT
SAFEFLOW_UI_PORT
SAFEFLOW_CORS_ORIGINS
SAFEFLOW_REFUND_APPROVAL_THRESHOLD
SAFEFLOW_MAX_EXTRACTION_REPAIR_ATTEMPTS
SAFEFLOW_EVAL_REPEATED_RUNS
SAFEFLOW_RANDOM_SEED
```

## 4. Data And State Rules

P0 data storage:

- JSON fixtures under `data/fixtures/support/`.
- JSONL benchmark tasks under `data/benchmark/support_demo.jsonl`.
- JSON result snapshots under `data/results/`.
- In-memory runtime state during a workflow run.

Do not add Stripe, Redis, PostgreSQL, hosted databases, or public online databases to P0. Use synthetic deterministic fixtures with oracle predicates.

Every workflow run must record:

- `workflow_id`
- `fixture_id`
- `request_text`
- `model_mode`
- timeline events
- tool calls
- policy decisions
- approvals
- audit receipts
- final state
- metric result

Every consequential tool call must record:

- pre-state hash
- post-state hash
- intended transition
- observed transition
- policy decision
- idempotency key if applicable
- audit receipt ID

## 5. Naming Conventions

### Fixture IDs

Use:

```text
support_<scenario>_<number>
```

Examples:

- `support_refund_happy_001`
- `support_refund_timeout_after_commit_001`
- `support_refund_high_value_reject_001`
- `support_refund_no_duplicate_001`
- `support_tool_mismatch_001`

### IDs

Use stable prefixes:

| Entity | Prefix |
| --- | --- |
| Workflow | `wf_` |
| Customer | `cus_` |
| Order | `ord_` |
| Payment | `pay_` |
| Refund | `ref_` |
| Ticket | `tkt_` |
| Approval | `apr_` |
| Audit receipt | `aud_` |
| Tool call | `tool_` |

### Status Values

Use enums, not free-form strings.

Important workflow terminal states:

- `completed`
- `completed_with_recovered_timeout`
- `denied`
- `pending_manual_review`
- `escalated_state_mismatch`
- `failed_safe`

## 6. Qwen And Prompt Rules

- Qwen outputs must be structured JSON.
- Validate outputs with Pydantic.
- Retry invalid JSON once.
- If still invalid, stop in `failed_safe`.
- Do not let tool output or customer text override system/developer policy.
- Fixture fallback must be explicit through `SAFEFLOW_MODEL_MODE=fixture_fallback`.
- Audit whether live Qwen or fixture fallback was used.

## 7. Tool Rules

Tools are deterministic functions for MVP.

Each tool must define:

- name
- input schema
- output schema
- preconditions
- transition effects
- side effects
- reversibility
- risk level
- idempotency requirement
- failure modes

`create_refund` special rules:

- Requires `idempotency_key`.
- Must support `success`, `timeout_before_commit`, `timeout_after_commit`, and `success_but_state_mismatch`.
- Must never create more than one completed refund for the same payment, amount, and idempotency key.

## 8. Policy Rules

P0 policy rules are hardcoded and deterministic.

Use stable IDs:

- `P_REFUND_DUPLICATE_ONLY`
- `P_NO_ALREADY_REFUNDED`
- `P_HIGH_VALUE_APPROVAL`
- `P_APPROVAL_REJECTION_BLOCKS`
- `P_STATE_MISMATCH_STOPS`

Policy decisions:

- `allow`
- `deny`
- `approval_required`
- `escalate`

If policies conflict, choose `escalate`.

## 9. Safety Rules

Hard requirements:

- No refund without duplicate captured payment.
- No high-value refund without approved approval.
- No action after approval rejection.
- No consequential action after state mismatch.
- No retry after timeout-after-commit until state is checked.
- No customer response promising refund unless final state confirms refund completion.

## 10. Evaluation Rules

Evaluation must be runnable offline.

P0 benchmark:

- 20 support cases.
- 5 repeated runs per case.
- Same cases for SafeFlow and baseline.

Required metrics:

- Business Task Success Rate.
- Final State Exact Match.
- Desired Transition Match Rate.
- Forbidden Transition Count.
- Duplicate Refund Count.
- Approval Recall.
- Rejection Compliance Rate.
- Audit Completeness Rate.

Baseline:

- Same Qwen model.
- Same tool execution environment.
- Sees only tool names, descriptions, and schemas.
- Does not see transition metadata, policy internals, idempotency guard, or post-state validator.

## 11. Testing Rules

Minimum tests:

- Policy unit tests.
- Tool precondition unit tests.
- Idempotency unit tests.
- State validation unit tests.
- Audit receipt completeness tests.
- UC1-UC5 integration tests.
- Evaluation runner smoke test.

Tests must pass in fixture fallback mode without network access.

## 12. Commit Convention And Local Hooks

Commit messages should use Conventional Commits, even before automated commit linting is installed.

Format:

```text
<type>(optional-scope): <short imperative summary>
```

Recommended types:

| Type | Use For |
| --- | --- |
| `feat` | User-visible capability or P0 task implementation |
| `fix` | Bug fix or safety regression fix |
| `test` | Test-only changes |
| `docs` | Documentation-only changes |
| `refactor` | Behavior-preserving code structure changes |
| `chore` | Tooling, setup, dependency, or maintenance changes |
| `style` | Formatting-only changes |

Examples:

```text
feat(ui): add operator audit review console
fix(workflow): prevent refund retry after rejected approval
test(eval): cover repeated-run metric summary
docs(ui): add operator console design conventions
chore(dev): add commitlint hook
```

Husky and commitlint are allowed but not required for P0 unless the repo adds a root JavaScript tooling package.

If automated commit linting is added:

- Put Husky, commitlint, and their config at the repository root, not under `ui/`, so all commits are checked consistently.
- Use `@commitlint/config-conventional` unless there is a documented reason to customize it.
- Keep hook behavior local and fast; do not run full `pytest` or browser tests from a commit-msg hook.
- Use `commit-msg` only for message validation.
- If adding pre-commit checks, keep them opt-in or lightweight until the team agrees they are worth the local friction.
- Document install/setup commands in `docs/development/setup_decisions.md` and update `.env.example` only if new env vars are introduced.
- Do not let hook tooling replace the required task-specific test commands listed below.

## 13. Task Completion And Change Control

Done tasks are protected.

Rules:

- A task can be marked done only after its acceptance criteria pass and relevant tests run.
- Do not rewrite completed task code casually while implementing later tasks.
- New code must adapt to existing schemas, service boundaries, fixtures, and tests.
- Contract changes must be intentional and documented.
- If changing a done task is unavoidable, update related tests, fixtures, docs, and downstream callers in the same change.
- Every completion note should include:
  - task ID,
  - acceptance criteria status,
  - tests/commands run,
  - known limitations,
  - changed contracts, if any.

Recommended test scope by task type:

| Task Type | Required Check |
| --- | --- |
| Models/schemas | unit tests and fixture validation |
| Tool behavior | unit tests plus relevant UC integration test |
| Policy/action control | unit tests plus UC integration test |
| Evaluation metric | metric unit test and eval runner smoke test |
| UI | build check plus Playwright/e2e check when available |
| Docs-only | link/path sanity check |
| Data/benchmark | `python scripts/audit_test_data.py --benchmark <path>` |

## 14. UI Rules

Use React + Vite for P0.

UI should show:

- request and fixture selector
- workflow timeline
- approval buttons when pending
- state diff
- final validation result
- audit receipt
- metrics summary

Do not build a marketing landing page. The first screen should be the usable operator console.

Frontend rules:

- Do not hardcode API URLs. Use `VITE_API_BASE_URL`.
- Keep app UI under `ui/src/`.
- Use `lucide-react` icons for actions and status.
- Do not put core safety logic in React. UI calls backend APIs and displays state.
- Use fixed, responsive layout constraints so demo content does not jump.

## 15. Agent Skills And MCP Rules

Current agent skill setup:

- `playwright` skill installed for UI verification and e2e testing.
- No dedicated curated `frontend` skill was available.

MCP policy:

- No MCP server is required for P0.
- Do not add MCP servers for Stripe, Redis, DBs, CRMs, or external SaaS in P0.
- Add MCP only when a task explicitly needs live external data/actions or browser/e2e automation beyond local tooling.
- If adding MCP, document why it is needed, what data/actions it can access, required env vars/secrets, and fallback behavior when unavailable.

## 16. Documentation Rules

When changing behavior, update the closest source of truth:

- Product scope or ACs: `docs/product/mvp_product_requirements.md`.
- Dev conventions: this file and `AGENTS.md`.
- Evaluation design: `docs/evaluation/state_transition_evaluation_metrics.md` if changing metric definitions.
- Research framing: `docs/research/*` only if the research claim changes.

## 17. Definition Of Ready

A dev task is ready when it has:

- related use case or requirement ID
- fixture or test case
- expected state transition
- expected final predicates
- forbidden predicates if consequential
- owner/module

## 18. Definition Of Done

A dev task is done when:

- implementation is complete
- unit or integration test exists
- fixture result is reproducible
- audit/log output is inspectable if consequential
- docs updated if contract changed
- no P0 safety rule is violated
