"""Workflow API routes.

Business logic belongs in services, not route handlers.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.domains.support.tools import correct_ticket_status
from app.eval.baselines import run_description_only_baseline_task
from app.models.evaluation import BenchmarkTask
from app.models.state import SupportState, TicketStatus
from app.models.workflow import BaselineComparison, WorkflowRequest, WorkflowRunResult
from app.services.action_controller import run_support_workflow
from app.services.state_service import (
    load_support_fixture,
    load_workflow_result,
    save_workflow_result,
    snapshot_state,
)

router = APIRouter(prefix="/workflows", tags=["workflows"])


class TicketCorrectionRequest(BaseModel):
    ticket_id: str
    new_status: TicketStatus
    operator_note: str
    operator_id: str = "op_demo"


def _baseline_comparison(fixture_id: str) -> BaselineComparison:
    fixture = load_support_fixture(fixture_id)
    task = BenchmarkTask(
        task_id=fixture_id,
        domain="support",
        fixture_id=fixture_id,
        request_text="",
        failure_mode=fixture.failure_mode,
    )
    bl = run_description_only_baseline_task(task)
    final_state = bl.final_state or {}
    completed_refunds = sum(
        1
        for r in final_state.get("refunds", {}).values()
        if isinstance(r, dict) and r.get("status") == "completed"
    )
    return BaselineComparison(
        status=bl.status,
        completed_refunds=completed_refunds,
        final_state_match=bl.final_state_match,
        audit_receipts=len(bl.audit_receipt_ids),
    )


@router.post("/run", response_model=WorkflowRunResult)
def run_workflow(request: WorkflowRequest) -> WorkflowRunResult:
    result = run_support_workflow(
        fixture_id=request.fixture_id,
        request_text=request.request_text,
    )
    if request.include_baseline:
        result = result.model_copy(update={"baseline": _baseline_comparison(request.fixture_id)})
    return result


@router.get("/{workflow_id}", response_model=WorkflowRunResult)
def get_workflow(workflow_id: str) -> WorkflowRunResult:
    result = load_workflow_result(workflow_id)
    if result is None:
        raise HTTPException(status_code=404, detail="workflow_not_found")
    return result


@router.post("/{workflow_id}/correct-ticket", response_model=WorkflowRunResult)
def correct_ticket(workflow_id: str, request: TicketCorrectionRequest) -> WorkflowRunResult:
    """Non-financial compensating action: operator corrects ticket status post-incident."""
    result = load_workflow_result(workflow_id)
    if result is None:
        raise HTTPException(status_code=404, detail="workflow_not_found")

    correctable_statuses = {
        "escalated_state_mismatch",
        "pending_manual_review",
        "pending_customer_followup",
        "failed_safe",
    }
    if result.status not in correctable_statuses:
        raise HTTPException(
            status_code=409,
            detail=f"workflow_status_not_correctable: {result.status}",
        )

    if result.final_state is None:
        raise HTTPException(status_code=409, detail="workflow_has_no_final_state")

    state = SupportState.model_validate(result.final_state)
    update = correct_ticket_status(
        state,
        ticket_id=request.ticket_id,
        new_status=request.new_status,
        operator_note=request.operator_note,
    )
    if not update.success:
        raise HTTPException(status_code=422, detail=update.error)

    updated_result = result.model_copy(update={"final_state": snapshot_state(state)})
    save_workflow_result(updated_result)
    return updated_result
