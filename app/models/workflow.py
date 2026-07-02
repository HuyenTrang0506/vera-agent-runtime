"""Workflow request and response contracts."""

from typing import Any

from pydantic import BaseModel, Field

from app.models.audit import AuditReceipt


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
    audit_receipts: list[AuditReceipt] = Field(default_factory=list)
    final_state: dict[str, Any] | None = None
    message: str | None = None
