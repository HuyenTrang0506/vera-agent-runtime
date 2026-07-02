"""Audit receipt generation service."""

from app.core.ids import new_id
from app.models.audit import AuditReceipt
from app.models.workflow import TimelineEvent


def build_receipt(
    *,
    workflow_id: str,
    action_id: str,
    intended_transition: str,
    observed_transition: str,
    policy_decision: str,
    pre_state_hash: str,
    post_state_hash: str,
    outcome: str,
) -> AuditReceipt:
    return AuditReceipt(
        receipt_id=new_id("aud_"),
        workflow_id=workflow_id,
        action_id=action_id,
        intended_transition=intended_transition,
        observed_transition=observed_transition,
        policy_decision=policy_decision,
        pre_state_hash=pre_state_hash,
        post_state_hash=post_state_hash,
        outcome=outcome,
    )


def timeline_event_from_receipt(receipt: AuditReceipt) -> TimelineEvent:
    return TimelineEvent(
        event_id=new_id("evt_"),
        workflow_id=receipt.workflow_id,
        event_type=receipt.outcome,
        summary=(
            f"{receipt.action_id}: {receipt.intended_transition} -> "
            f"{receipt.observed_transition}"
        ),
        receipt_id=receipt.receipt_id,
        state_hash=receipt.post_state_hash,
    )
