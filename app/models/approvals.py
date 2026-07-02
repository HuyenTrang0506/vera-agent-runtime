"""Approval lifecycle contracts."""

from pydantic import BaseModel

from app.models.enums import ApprovalStatus


class ApprovalRecord(BaseModel):
    approval_id: str
    workflow_id: str
    action_type: str = "create_refund"
    status: ApprovalStatus = ApprovalStatus.PENDING
    requested_amount: float
    policy_rule_id: str
    decided_by: str | None = None
    comment: str | None = None


class ApprovalDecisionRequest(BaseModel):
    decided_by: str
    comment: str | None = None
