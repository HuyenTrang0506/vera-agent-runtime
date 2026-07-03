"""Run a deterministic VERA demo fixture, optionally with side-by-side baseline comparison."""

from argparse import ArgumentParser
import json

from app.services.action_controller import run_support_workflow


def _completed_refund_count(final_state: dict | None) -> int:
    if final_state is None:
        return 0
    return sum(
        1
        for r in final_state.get("refunds", {}).values()
        if r.get("status") == "completed"
    )


def _run_baseline(fixture_id: str) -> dict:
    from app.eval.baselines import run_description_only_baseline_task
    from app.models.evaluation import BenchmarkTask
    from app.services.state_service import load_support_fixture

    fixture = load_support_fixture(fixture_id)
    task = BenchmarkTask(
        task_id=fixture_id,
        domain="support",
        fixture_id=fixture_id,
        request_text="",
        failure_mode=fixture.failure_mode,
    )
    result = run_description_only_baseline_task(task)
    return result.model_dump(mode="json")


def main() -> None:
    parser = ArgumentParser()
    parser.add_argument("--fixture", required=True)
    parser.add_argument("--request-text", default=None)
    parser.add_argument(
        "--compare-baseline",
        action="store_true",
        help="Show baseline (description-only) result alongside VERA result.",
    )
    args = parser.parse_args()

    vera_result = run_support_workflow(fixture_id=args.fixture, request_text=args.request_text)

    if args.compare_baseline:
        baseline = _run_baseline(args.fixture)
        vera_dump = vera_result.model_dump(mode="json")
        output = {
            "baseline": {
                "status": baseline.get("status"),
                "completed_refunds": _completed_refund_count(baseline.get("final_state")),
                "final_state_match": baseline.get("final_state_match"),
                "audit_receipts": len(baseline.get("audit_receipt_ids", [])),
            },
            "vera": {
                "status": vera_result.status,
                "completed_refunds": _completed_refund_count(vera_dump.get("final_state")),
                "final_state_match": vera_result.final_state_match,
                "audit_receipts": len(vera_result.audit_receipts),
            },
        }
        print(json.dumps(output, indent=2))
    else:
        print(json.dumps(vera_result.model_dump(mode="json"), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
