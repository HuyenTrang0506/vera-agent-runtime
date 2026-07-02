"""Human approval lifecycle service."""

from types import MappingProxyType
from typing import Mapping

from app.core.config import settings
from app.core.ids import new_id
from app.models.approvals import ApprovalRecord
from app.models.enums import ApprovalStatus


_APPROVALS: dict[str, ApprovalRecord] = {}


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
    record = ApprovalRecord(
        approval_id=new_id("apr_"),
        workflow_id=workflow_id,
        action_type=action_type,
        status=ApprovalStatus.PENDING,
        requested_amount=requested_amount,
        policy_rule_id=policy_rule_id,
    )
    _APPROVALS[record.approval_id] = record
    return record


def get_approval(approval_id: str) -> ApprovalRecord | None:
    return _APPROVALS.get(approval_id)


def list_approvals() -> Mapping[str, ApprovalRecord]:
    return MappingProxyType(_APPROVALS)


def record_approval_decision(
    record: ApprovalRecord,
    decision: ApprovalStatus,
    decided_by: str,
    comment: str | None = None,
) -> ApprovalRecord:
    record.status = decision
    record.decided_by = decided_by
    record.comment = comment
    _APPROVALS[record.approval_id] = record
    return record


def is_approved(record: ApprovalRecord) -> bool:
    return record.status == ApprovalStatus.APPROVED


def is_rejected(record: ApprovalRecord) -> bool:
    return record.status in (ApprovalStatus.REJECTED, ApprovalStatus.EXPIRED)


def clear_approvals() -> None:
    _APPROVALS.clear()
