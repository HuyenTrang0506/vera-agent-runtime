"""Workflow request and response contracts."""

from typing import Any

from pydantic import BaseModel, Field

from app.models.audit import AuditReceipt


class WorkflowRequest(BaseModel):
    domain: str
    request_text: str
    fixture_id: str
    operator_id: str = "op_demo"


class TimelineEvent(BaseModel):
    event_id: str
    workflow_id: str
    event_type: str
    summary: str
    receipt_id: str | None = None
    state_hash: str | None = None


class WorkflowRunResult(BaseModel):
    workflow_id: str
    status: str
    desired_transition_id: str | None
    policy_decision: str | None
    final_state_match: bool
    audit_receipt_ids: list[str]
    audit_receipts: list[AuditReceipt] = Field(default_factory=list)
    timeline_events: list[TimelineEvent] = Field(default_factory=list)
    final_state: dict[str, Any] | None = None
    approval_id: str | None = None
    mismatch_detail: dict[str, Any] | None = None
    message: str | None = None
