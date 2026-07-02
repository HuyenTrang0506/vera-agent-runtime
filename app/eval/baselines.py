"""Description/schema-only baseline for P0 evaluation."""

import json
from pathlib import Path
from typing import Any

from app.domains.support.tools import (
    create_refund,
    find_duplicate_payment_for_order,
    find_ticket_for_order,
    resolve_ticket_with_completed_refund,
)
from app.eval.metrics import P0Metrics
from app.models.evaluation import BenchmarkTask
from app.models.workflow import WorkflowRunResult
from app.services.idempotency_service import refund_idempotency_key
from app.services.state_service import load_support_fixture, runtime_state_from_fixture, snapshot_state


def _load_task_rows(benchmark_path: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line in Path(benchmark_path).read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        parsed = json.loads(line)
        if not isinstance(parsed, dict):
            raise ValueError(f"Benchmark row must be a JSON object: {line}")
        rows.append(parsed)
    return rows


def _infer_payment_id(fixture_id: str) -> str | None:
    fixture = load_support_fixture(fixture_id)
    for payment in fixture.state.payments.values():
        if payment.duplicate_of is not None:
            return payment.payment_id
    return None


def _completed_refund_count(result: WorkflowRunResult, payment_id: str | None) -> int:
    if result.final_state is None or payment_id is None:
        return 0
    return sum(
        1
        for refund in result.final_state.get("refunds", {}).values()
        if refund.get("payment_id") == payment_id and refund.get("status") == "completed"
    )


def run_description_only_baseline_task(task: BenchmarkTask) -> WorkflowRunResult:
    fixture = load_support_fixture(task.fixture_id)
    state = runtime_state_from_fixture(fixture)
    order_id = fixture.expected_extraction.entities.order_id

    if order_id is None:
        return WorkflowRunResult(
            workflow_id=f"base_{task.task_id}",
            status="failed_safe",
            desired_transition_id=fixture.expected_extraction.desired_transition.transition_id,
            policy_decision=None,
            final_state_match=False,
            audit_receipt_ids=[],
            final_state=snapshot_state(state),
            message="Baseline could not identify order_id.",
        )

    duplicate_payment = find_duplicate_payment_for_order(state, order_id)
    if duplicate_payment is None:
        return WorkflowRunResult(
            workflow_id=f"base_{task.task_id}",
            status="denied",
            desired_transition_id=fixture.expected_extraction.desired_transition.transition_id,
            policy_decision=None,
            final_state_match=False,
            audit_receipt_ids=[],
            final_state=snapshot_state(state),
            message="Baseline found no duplicate payment.",
        )

    key = refund_idempotency_key(duplicate_payment.payment_id, duplicate_payment.amount)
    refund_result = create_refund(
        state,
        payment_id=duplicate_payment.payment_id,
        amount=duplicate_payment.amount,
        idempotency_key=key,
        failure_mode=fixture.failure_mode,
    )

    status = "completed" if refund_result.success else "failed_safe"
    ticket = find_ticket_for_order(state, order_id)
    if refund_result.refund is not None and ticket is not None:
        resolve_ticket_with_completed_refund(state, ticket.ticket_id, refund_result.refund.refund_id)

    final_state = snapshot_state(state)
    completed_count = _completed_refund_count(
        WorkflowRunResult(
            workflow_id=f"base_{task.task_id}",
            status=status,
            desired_transition_id=fixture.expected_extraction.desired_transition.transition_id,
            policy_decision=None,
            final_state_match=False,
            audit_receipt_ids=[],
            final_state=final_state,
        ),
        duplicate_payment.payment_id,
    )

    return WorkflowRunResult(
        workflow_id=f"base_{task.task_id}",
        status=status,
        desired_transition_id=fixture.expected_extraction.desired_transition.transition_id,
        policy_decision=None,
        final_state_match=status == "completed" and completed_count == 1,
        audit_receipt_ids=[],
        final_state=final_state,
        message="Description/schema-only baseline used tool outputs without policy or transition validation.",
    )


def run_description_only_baseline(
    benchmark_path: str,
    repeated_runs: int = 1,
) -> dict[str, Any]:
    if repeated_runs < 1:
        raise ValueError("repeated_runs must be at least 1")

    task_rows = _load_task_rows(benchmark_path)
    tasks = [BenchmarkTask.model_validate(row) for row in task_rows]
    metrics = P0Metrics()
    task_results: list[dict[str, Any]] = []

    for run_index in range(repeated_runs):
        for task, raw in zip(tasks, task_rows, strict=True):
            approval_script = raw.get("approval_script")
            payment_id = _infer_payment_id(task.fixture_id)
            result = run_description_only_baseline_task(task)
            is_forbidden = _completed_refund_count(result, payment_id) > 1

            metrics.record(
                result,
                expected_transition_id="T_REFUND_CREATE",
                payment_id=payment_id,
                expects_approval="high_value" in task.fixture_id,
                expects_rejection_compliance=approval_script == "reject",
                is_forbidden_transition=is_forbidden,
            )

            task_results.append(
                {
                    "run_index": run_index,
                    "task_id": task.task_id,
                    "fixture_id": task.fixture_id,
                    "status": result.status,
                    "final_state_match": result.final_state_match,
                    "audit_receipts": len(result.audit_receipts),
                }
            )

    return {
        "baseline": "description_schema_only",
        "benchmark_path": benchmark_path,
        "repeated_runs": repeated_runs,
        "metrics": metrics.summary(),
        "tasks": task_results,
    }
