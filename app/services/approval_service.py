"""Human approval lifecycle service."""

from app.core.config import settings
from app.core.ids import new_id
from app.models.approvals import ApprovalRecord
from app.models.enums import ApprovalStatus


def approval_required(
    amount: float, threshold: float = settings.refund_approval_threshold
) -> bool:
    return amount >= threshold


def create_approval(
    workflow_id: str,
    requested_amount: float,
    policy_rule_id: str,
    action_type: str = "create_refund",
) -> ApprovalRecord:
    return ApprovalRecord(
        approval_id=new_id("apr_"),
        workflow_id=workflow_id,
        action_type=action_type,
        status=ApprovalStatus.PENDING,
        requested_amount=requested_amount,
        policy_rule_id=policy_rule_id,
    )


def record_approval_decision(
    record: ApprovalRecord,
    decision: ApprovalStatus,
    decided_by: str,
    comment: str | None = None,
) -> ApprovalRecord:
    record.status = decision
    record.decided_by = decided_by
    record.comment = comment
    return record


def is_approved(record: ApprovalRecord) -> bool:
    return record.status == ApprovalStatus.APPROVED


def is_rejected(record: ApprovalRecord) -> bool:
    return record.status in (ApprovalStatus.REJECTED, ApprovalStatus.EXPIRED)
