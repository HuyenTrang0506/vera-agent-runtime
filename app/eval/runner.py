"""Benchmark runner for P0 SafeFlow evaluation."""

import json
from pathlib import Path
from typing import Any

from app.eval.metrics import P0Metrics
from app.models.approvals import ApprovalRecord
from app.models.enums import ApprovalStatus
from app.models.evaluation import BenchmarkTask
from app.models.workflow import WorkflowRunResult
from app.services.action_controller import run_support_workflow


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


def _load_tasks(benchmark_path: str) -> list[BenchmarkTask]:
    return [BenchmarkTask.model_validate(row) for row in _load_task_rows(benchmark_path)]


def _infer_payment_id(fixture_id: str) -> str | None:
    """Best-effort: derive the duplicate payment_id from fixture naming conventions."""
    from app.services.state_service import load_support_fixture
    try:
        fixture = load_support_fixture(fixture_id)
        for payment in fixture.state.payments.values():
            if payment.duplicate_of is not None:
                return payment.payment_id
    except Exception:
        pass
    return None


def _run_task(task: BenchmarkTask, approval_script: str | None) -> WorkflowRunResult:
    approval_record: ApprovalRecord | None = None
    if approval_script == "reject":
        approval_record = ApprovalRecord(
            approval_id=f"apr_eval_{task.task_id}",
            workflow_id=f"wf_eval_{task.task_id}",
            status=ApprovalStatus.REJECTED,
            requested_amount=0.0,
            policy_rule_id="P_HIGH_VALUE_APPROVAL",
            decided_by="eval_manager",
        )
    elif approval_script == "approve":
        approval_record = ApprovalRecord(
            approval_id=f"apr_eval_{task.task_id}",
            workflow_id=f"wf_eval_{task.task_id}",
            status=ApprovalStatus.APPROVED,
            requested_amount=0.0,
            policy_rule_id="P_HIGH_VALUE_APPROVAL",
            decided_by="eval_manager",
        )

    result = run_support_workflow(
        fixture_id=task.fixture_id,
        request_text=task.request_text,
        approval_record=approval_record,
    )
    return result


def run_benchmark(benchmark_path: str) -> dict[str, Any]:
    task_rows = _load_task_rows(benchmark_path)
    tasks = [BenchmarkTask.model_validate(row) for row in task_rows]
    metrics = P0Metrics()
    task_results: list[dict[str, Any]] = []

    for task, raw in zip(tasks, task_rows, strict=True):
        approval_script = raw.get("approval_script")
        if approval_script is not None and not isinstance(approval_script, str):
            raise ValueError(f"{task.task_id} approval_script must be a string or null")

        expects_approval = "high_value" in task.fixture_id
        expects_rejection = approval_script == "reject"
        payment_id = _infer_payment_id(task.fixture_id)

        result = _run_task(task, approval_script)

        is_forbidden = (
            payment_id is not None
            and sum(
                1
                for r in (result.final_state or {}).get("refunds", {}).values()
                if r.get("payment_id") == payment_id and r.get("status") == "completed"
            ) > 1
        )

        metrics.record(
            result,
            expected_transition_id="T_REFUND_CREATE",
            payment_id=payment_id,
            expects_approval=expects_approval,
            expects_rejection_compliance=expects_rejection,
            is_forbidden_transition=is_forbidden,
        )

        task_results.append(
            {
                "task_id": task.task_id,
                "fixture_id": task.fixture_id,
                "status": result.status,
                "policy_decision": result.policy_decision,
                "final_state_match": result.final_state_match,
                "audit_receipts": len(result.audit_receipts),
            }
        )

    return {
        "benchmark_path": benchmark_path,
        "metrics": metrics.summary(),
        "tasks": task_results,
    }
