from app.eval.baselines import run_description_only_baseline


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
