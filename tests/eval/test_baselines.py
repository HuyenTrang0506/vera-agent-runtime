from app.eval.baselines import (
    run_description_only_baseline,
    run_finance_description_only_baseline,
)


def test_description_only_baseline_runs_same_benchmark() -> None:
    result = run_description_only_baseline(
        "data/benchmark/support_demo.jsonl",
        repeated_runs=1,
    )

    assert result["baseline"] == "description_schema_only"
    assert result["repeated_runs"] == 1
    assert result["metrics"]["total_tasks"] > 0
    assert len(result["tasks"]) == result["metrics"]["total_tasks"]


def test_description_only_baseline_has_no_audit_completeness() -> None:
    result = run_description_only_baseline(
        "data/benchmark/support_demo.jsonl",
        repeated_runs=1,
    )

    assert result["metrics"]["audit_completeness_rate"] == 0.0


def test_baseline_approval_recall_is_zero() -> None:
    result = run_description_only_baseline(
        "data/benchmark/support_demo.jsonl",
        repeated_runs=1,
    )
    # Baseline has no policy engine → never routes to approval
    assert result["metrics"]["approval_recall"] == 0.0


def test_baseline_has_forbidden_transitions() -> None:
    result = run_description_only_baseline(
        "data/benchmark/support_demo.jsonl",
        repeated_runs=1,
    )
    # Baseline has no policy engine → fires forbidden predicates on at least one task
    assert result["metrics"]["forbidden_transition_count"] > 0


def test_finance_baseline_runs_finance_benchmark() -> None:
    result = run_finance_description_only_baseline(
        "data/benchmark/finance_demo.jsonl",
        repeated_runs=1,
    )

    assert result["baseline"] == "finance_description_schema_only"
    assert result["metrics"]["total_tasks"] == 3
    assert len(result["tasks"]) == 3


def test_finance_baseline_has_no_audit_completeness() -> None:
    result = run_finance_description_only_baseline(
        "data/benchmark/finance_demo.jsonl",
        repeated_runs=1,
    )
    assert result["metrics"]["audit_completeness_rate"] == 0.0


def test_finance_baseline_pays_duplicate_invoice() -> None:
    result = run_finance_description_only_baseline(
        "data/benchmark/finance_demo.jsonl",
        repeated_runs=1,
    )
    # Baseline has no duplicate-block policy → forbidden_violation_count > 0
    assert result["metrics"]["forbidden_violation_count"] > 0


def test_finance_baseline_business_success_rate_below_vera() -> None:
    result = run_finance_description_only_baseline(
        "data/benchmark/finance_demo.jsonl",
        repeated_runs=1,
    )
    # Baseline only gets happy path right → < 1.0
    assert result["metrics"]["business_task_success_rate"] < 1.0
