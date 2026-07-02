"""Workflow API routes.

Business logic belongs in services, not route handlers.
"""

from fastapi import APIRouter, HTTPException

from app.models.workflow import WorkflowRequest, WorkflowRunResult
from app.services.action_controller import run_support_workflow
from app.services.state_service import load_workflow_result

router = APIRouter(prefix="/workflows", tags=["workflows"])


@router.post("/run", response_model=WorkflowRunResult)
def run_workflow(request: WorkflowRequest) -> WorkflowRunResult:
    return run_support_workflow(
        fixture_id=request.fixture_id,
        request_text=request.request_text,
    )


@router.get("/{workflow_id}", response_model=WorkflowRunResult)
def get_workflow(workflow_id: str) -> WorkflowRunResult:
    result = load_workflow_result(workflow_id)
    if result is None:
        raise HTTPException(status_code=404, detail="workflow_not_found")
    return result
