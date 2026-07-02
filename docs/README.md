# Research Docs

This folder is now organized around the selected research direction:

**Qwen-powered enterprise Autopilot Agent with State-Transition-Aware Action Control.**

Implementation scaffold lives at the repository root under `app/`, `ui/`, `scripts/`, `tests/`, and `data/fixtures|benchmark|results`. Development conventions are enforced through root `AGENTS.md` plus `docs/development/project_conventions.md`.

## Structure

```text
docs/
+-- development/
|   +-- code_structure.md
|   +-- project_conventions.md
|   +-- setup_decisions.md
|   `-- test_data_criteria.md
+-- evaluation/
|   `-- state_transition_evaluation_metrics.md
+-- product/
|   `-- mvp_product_requirements.md
`-- research/
    +-- failure_patterns.md
    +-- framework_summary.md
    +-- industrial_problem_brief.md
    `-- qwen_hackathon_topic_fit.md
```

## Current Focus

- `research/industrial_problem_brief.md` - industrial framing and selected problem.
- `development/project_conventions.md` - development conventions for scope, architecture, state, tools, testing, evaluation, and demo UI.
- `development/code_structure.md` - actual implementation structure for backend, UI, scripts, tests, and data.
- `development/setup_decisions.md` - setup and infrastructure decisions, including why P0 does not use Stripe, Redis, external DBs, or public online DBs as benchmark state.
- `development/test_data_criteria.md` - criteria for benchmark/test data quality and assessment of the current datasets.
- `research/failure_patterns.md` - evidence of common agent failures from repository issue analysis.
- `research/qwen_hackathon_topic_fit.md` - hackathon track framing for SafeFlow/Qwen Autopilot.
- `research/framework_summary.md` - ecosystem survey used for baseline selection.
- `evaluation/state_transition_evaluation_metrics.md` - reusable evaluation framework, metrics, dataset design, baselines, protocol, stress tests, enterprise criteria, and novelty analysis.
- `product/mvp_product_requirements.md` - MVP product requirements, delivery framework, sprint plan, use cases, acceptance criteria, backlog, and proposed technical architecture.

Removed broad ideation files that are no longer part of the focused direction:

- `analysis/decision_brief.md`
- `analysis/research_analysis.md`
- `analysis/assumption_database.md`
