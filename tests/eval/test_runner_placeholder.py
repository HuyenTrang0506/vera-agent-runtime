from app.eval.runner import run_benchmark


def test_runner_returns_metrics_and_tasks() -> None:
    result = run_benchmark("data/benchmark/support_demo.jsonl", repeated_runs=2)
    assert "metrics" in result
    assert "tasks" in result
    assert result["repeated_runs"] == 2
    assert result["repeated_run_summary"]["total_runs"] == len(result["tasks"])
    metrics = result["metrics"]
    assert metrics["total_tasks"] > 0
    assert metrics["total_tasks"] == result["repeated_run_summary"]["total_runs"]
    assert metrics["duplicate_refund_count"] == 0
    assert metrics["forbidden_transition_count"] == 0
    assert metrics["approval_recall"] == 1.0
    assert metrics["rejection_compliance_rate"] == 1.0
    assert metrics["desired_transition_match_rate"] == 1.0


def test_runner_vera_has_full_audit_completeness() -> None:
    result = run_benchmark("data/benchmark/support_demo.jsonl", repeated_runs=1)
    assert result["metrics"]["audit_completeness_rate"] == 1.0


def test_runner_vera_business_success_rate_above_baseline() -> None:
    from app.eval.baselines import run_description_only_baseline
    vera = run_benchmark("data/benchmark/support_demo.jsonl", repeated_runs=1)
    baseline = run_description_only_baseline("data/benchmark/support_demo.jsonl", repeated_runs=1)
    assert vera["metrics"]["business_task_success_rate"] > baseline["metrics"]["business_task_success_rate"]


def test_runner_vera_final_state_match_above_baseline() -> None:
    from app.eval.baselines import run_description_only_baseline
    vera = run_benchmark("data/benchmark/support_demo.jsonl", repeated_runs=1)
    baseline = run_description_only_baseline("data/benchmark/support_demo.jsonl", repeated_runs=1)
    assert vera["metrics"]["final_state_exact_match_rate"] > baseline["metrics"]["final_state_exact_match_rate"]
