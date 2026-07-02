from app.services.approval_service import (
    clear_approvals,
    create_approval,
    get_approval,
    record_approval_decision,
)
from app.models.enums import ApprovalStatus


def test_create_approval_stores_pending_record_and_decision_update() -> None:
    clear_approvals()
    approval = create_approval(
        workflow_id="wf_test",
        requested_amount=750.0,
        policy_rule_id="P_HIGH_VALUE_APPROVAL",
    )

    assert approval.status == ApprovalStatus.PENDING
    assert get_approval(approval.approval_id) == approval

    updated = record_approval_decision(
        approval,
        decision=ApprovalStatus.REJECTED,
        decided_by="manager_demo",
        comment="Needs manual review.",
    )

    assert updated.status == ApprovalStatus.REJECTED
    assert updated.decided_by == "manager_demo"
    assert updated.comment == "Needs manual review."
    assert get_approval(approval.approval_id) == updated
