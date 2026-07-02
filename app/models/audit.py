"""Audit receipt contracts."""

from pydantic import BaseModel


class AuditReceipt(BaseModel):
    receipt_id: str
    workflow_id: str
    action_id: str
    intended_transition: str
    observed_transition: str
    policy_decision: str
    pre_state_hash: str
    post_state_hash: str
    outcome: str

