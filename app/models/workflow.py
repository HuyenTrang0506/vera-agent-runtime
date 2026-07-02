"""Workflow request and response contracts."""

from pydantic import BaseModel


class WorkflowRequest(BaseModel):
    domain: str
    request_text: str
    fixture_id: str
    operator_id: str = "op_demo"


class WorkflowRunResult(BaseModel):
    workflow_id: str
    status: str
    desired_transition_id: str | None
    policy_decision: str | None
    final_state_match: bool
    audit_receipt_ids: list[str]
    message: str | None = None

