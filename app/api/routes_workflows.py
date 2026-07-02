"""Workflow API routes.

Business logic belongs in services, not route handlers.
"""

from fastapi import APIRouter

from app.models.workflow import WorkflowRequest, WorkflowRunResult
from app.services.action_controller import run_support_workflow

router = APIRouter(prefix="/workflows", tags=["workflows"])


@router.post("/run", response_model=WorkflowRunResult)
def run_workflow(request: WorkflowRequest) -> WorkflowRunResult:
    return run_support_workflow(
        fixture_id=request.fixture_id,
        request_text=request.request_text,
    )


@router.get("/{workflow_id}")
def get_workflow(workflow_id: str) -> dict[str, str]:
    return {"workflow_id": workflow_id, "status": "not_implemented"}
