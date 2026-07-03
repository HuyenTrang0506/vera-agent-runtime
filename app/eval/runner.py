"""Benchmark runner for P0 SafeFlow evaluation."""

import json
from pathlib import Path
from typing import Any

from app.core.config import settings
from app.eval.metrics import P0Metrics, is_business_success
from app.eval.predicates import count_forbidden_violations, evaluate_predicates
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


def run_benchmark(benchmark_path: str, repeated_runs: int | None = None) -> dict[str, Any]:
    task_rows = _load_task_rows(benchmark_path)
    tasks = [BenchmarkTask.model_validate(row) for row in task_rows]
    run_count = repeated_runs if repeated_runs is not None else settings.eval_repeated_runs
    if run_count < 1:
        raise ValueError("repeated_runs must be at least 1")

    metrics = P0Metrics()
    task_results: list[dict[str, Any]] = []
    task_success_counts: dict[str, int] = {task.task_id: 0 for task in tasks}

    for run_index in range(run_count):
        for task, raw in zip(tasks, task_rows, strict=True):
            approval_script = raw.get("approval_script")
            if approval_script is not None and not isinstance(approval_script, str):
                raise ValueError(f"{task.task_id} approval_script must be a string or null")

            # Use explicit field when present; fall back to fixture-name heuristic
            # for existing tasks that predate the field.
            expects_approval = (
                task.expects_approval
                if task.expects_approval is not None
                else "high_value" in task.fixture_id
            )
            expects_rejection = (
                task.expects_rejection_compliance
                if task.expects_rejection_compliance is not None
                else approval_script == "reject"
            )
            payment_id = _infer_payment_id(task.fixture_id)

            result = _run_task(task, approval_script)

            # Override final_state_match using benchmark predicates when available.
            if task.expected_final_predicates:
                predicate_match = evaluate_predicates(task.expected_final_predicates, result)
                result = result.model_copy(update={"final_state_match": predicate_match})

            if is_business_success(result):
                task_success_counts[task.task_id] += 1

            forbidden_violations = count_forbidden_violations(task.forbidden_predicates, result)
            is_forbidden = forbidden_violations > 0

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
                    "run_index": run_index,
                    "task_id": task.task_id,
                    "fixture_id": task.fixture_id,
                    "status": result.status,
                    "policy_decision": result.policy_decision,
                    "final_state_match": result.final_state_match,
                    "audit_receipts": len(result.audit_receipts),
                }
            )

    # pass^k: fraction of tasks where ALL k runs succeeded
    pass_k = (
        sum(1 for count in task_success_counts.values() if count == run_count) / len(tasks)
        if tasks
        else 0.0
    )

    return {
        "benchmark_path": benchmark_path,
        "repeated_runs": run_count,
        "metrics": metrics.summary(),
        "pass_k": round(pass_k, 4),
        "repeated_run_summary": {
            "task_count": len(tasks),
            "total_runs": len(tasks) * run_count,
            "task_success_counts": task_success_counts,
        },
        "tasks": task_results,
    }
