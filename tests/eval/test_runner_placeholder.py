from app.eval.runner import run_benchmark


def test_runner_returns_metrics_and_tasks() -> None:
    result = run_benchmark("data/benchmark/support_demo.jsonl")
    assert "metrics" in result
    assert "tasks" in result
    metrics = result["metrics"]
    assert metrics["total_tasks"] > 0
    assert metrics["duplicate_refund_count"] == 0
    assert metrics["forbidden_transition_count"] == 0
    assert metrics["approval_recall"] == 1.0
    assert metrics["rejection_compliance_rate"] == 1.0
    assert metrics["desired_transition_match_rate"] == 1.0
