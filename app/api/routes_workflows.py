"""Workflow API routes.

Business logic belongs in services, not route handlers.
"""

from fastapi import APIRouter

from app.models.workflow import WorkflowRequest, WorkflowRunResult

router = APIRouter(prefix="/workflows", tags=["workflows"])


@router.post("/run", response_model=WorkflowRunResult)
def run_workflow(request: WorkflowRequest) -> WorkflowRunResult:
    # TODO: wire to action_controller once services are implemented.
    return WorkflowRunResult(
        workflow_id="wf_placeholder",
        status="failed_safe",
        desired_transition_id=None,
        policy_decision=None,
        final_state_match=False,
        audit_receipt_ids=[],
        message="Workflow controller is not implemented yet.",
    )


@router.get("/{workflow_id}")
def get_workflow(workflow_id: str) -> dict[str, str]:
    return {"workflow_id": workflow_id, "status": "not_implemented"}

