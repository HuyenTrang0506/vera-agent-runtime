from app.eval.runner import run_benchmark


def test_runner_placeholder() -> None:
    result = run_benchmark("data/benchmark/support_demo.jsonl")
    assert result["status"] == "not_implemented"

