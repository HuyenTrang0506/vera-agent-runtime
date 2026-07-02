from app.models.approvals import ApprovalRecord
from app.models.enums import ApprovalStatus
from app.services.action_controller import run_support_workflow


def test_support_workflow_happy_path_controller_completes_refund_transition() -> None:
    result = run_support_workflow(fixture_id="support_refund_happy_001")

    assert result.status == "completed"
    assert result.desired_transition_id == "T_REFUND_CREATE"
    assert result.policy_decision == "allow"
    assert result.final_state_match is True
    assert result.final_state is not None
    refunds = result.final_state["refunds"]
    completed_refunds = [
        refund
        for refund in refunds.values()
        if refund["payment_id"] == "pay_dup_001" and refund["status"] == "completed"
    ]
    assert len(completed_refunds) == 1
    assert result.final_state["tickets"]["tkt_001"]["status"] == "resolved"
    assert "completed" in result.final_state["tickets"]["tkt_001"]["response_draft"]
    assert len(result.audit_receipts) == 2
    assert result.audit_receipt_ids == [
        receipt.receipt_id for receipt in result.audit_receipts
    ]

    refund_receipt = result.audit_receipts[0]
    assert refund_receipt.workflow_id == result.workflow_id
    assert refund_receipt.intended_transition == "T_REFUND_CREATE,T_PAYMENT_REFUNDED_AMOUNT"
    assert refund_receipt.observed_transition == "T_REFUND_CREATE,T_PAYMENT_REFUNDED_AMOUNT"
    assert refund_receipt.policy_decision == "allow"
    assert refund_receipt.pre_state_hash
    assert refund_receipt.post_state_hash
    assert refund_receipt.pre_state_hash != refund_receipt.post_state_hash

    ticket_receipt = result.audit_receipts[1]
    assert ticket_receipt.intended_transition == "T_TICKET_RESOLVE"
    assert ticket_receipt.observed_transition == "T_TICKET_RESOLVE"
    assert ticket_receipt.pre_state_hash != ticket_receipt.post_state_hash


def test_support_workflow_recovers_timeout_after_commit_without_duplicate_refund() -> None:
    result = run_support_workflow(fixture_id="support_refund_timeout_after_commit_001")

    assert result.status == "completed_with_recovered_timeout"
    assert result.final_state_match is True
    assert result.final_state is not None

    refunds = result.final_state["refunds"]
    completed_refunds = [
        refund
        for refund in refunds.values()
        if refund["payment_id"] == "pay_timeout_dup_001" and refund["status"] == "completed"
    ]
    assert len(completed_refunds) == 1
    assert result.final_state["payments"]["pay_timeout_dup_001"]["refunded_amount"] == 120.0
    assert result.final_state["tickets"]["tkt_timeout_001"]["status"] == "resolved"
    assert "Timeout-after-commit recovered by state recheck" in (result.message or "")

    refund_receipt = result.audit_receipts[0]
    assert refund_receipt.outcome == "recovered"
    assert refund_receipt.observed_transition == "T_REFUND_CREATE,T_PAYMENT_REFUNDED_AMOUNT"
    assert refund_receipt.pre_state_hash != refund_receipt.post_state_hash


# UC3: high-value approval rejection

def test_uc3_high_value_refund_creates_approval_pending_when_no_decision() -> None:
    result = run_support_workflow(fixture_id="support_refund_high_value_reject_001")

    assert result.status == "approval_pending"
    assert result.policy_decision == "approval_required"
    assert result.approval_id is not None
    assert result.final_state_match is False
    assert len(result.audit_receipts) == 1
    assert result.audit_receipts[0].observed_transition == "T_APPROVAL_PENDING"


def test_uc3_high_value_refund_rejected_blocks_refund_and_moves_ticket_to_manual_review() -> None:
    # simulate manager rejection by passing a rejected ApprovalRecord
    rejected_record = ApprovalRecord(
        approval_id="apr_test_001",
        workflow_id="wf_test_001",
        status=ApprovalStatus.REJECTED,
        requested_amount=750.0,
        policy_rule_id="P_HIGH_VALUE_APPROVAL",
        decided_by="manager_demo",
    )
    result = run_support_workflow(
        fixture_id="support_refund_high_value_reject_001",
        approval_record=rejected_record,
    )

    assert result.status == "pending_manual_review"
    assert result.policy_decision == "approval_required"
    assert result.final_state_match is False
    # no refund created
    assert result.final_state is not None
    assert len(result.final_state["refunds"]) == 0
    # ticket moved to manual review
    assert result.final_state["tickets"]["tkt_hv_001"]["status"] == "pending_manual_review"
    assert len(result.audit_receipts) == 1
    assert result.audit_receipts[0].outcome == "blocked"


def test_uc3_pending_approval_record_does_not_execute_refund() -> None:
    pending_record = ApprovalRecord(
        approval_id="apr_pending_001",
        workflow_id="wf_test_001",
        status=ApprovalStatus.PENDING,
        requested_amount=750.0,
        policy_rule_id="P_HIGH_VALUE_APPROVAL",
        decided_by=None,
    )
    result = run_support_workflow(
        fixture_id="support_refund_high_value_reject_001",
        approval_record=pending_record,
    )

    assert result.status == "approval_pending"
    assert result.approval_id == "apr_pending_001"
    assert result.final_state is not None
    assert len(result.final_state["refunds"]) == 0


# UC4: no duplicate charge denial

def test_uc4_no_duplicate_payment_denies_refund_without_calling_create_refund() -> None:
    result = run_support_workflow(fixture_id="support_refund_no_duplicate_001")

    assert result.status == "denied"
    assert result.policy_decision == "deny"
    assert result.final_state_match is False
    assert result.final_state is not None
    # no refund created
    assert len(result.final_state["refunds"]) == 0
    # ticket moved to pending_customer_followup with no refund promise
    ticket = result.final_state["tickets"]["tkt_nodup_001"]
    assert ticket["status"] == "pending_customer_followup"
    response = ticket.get("response_draft", "")
    assert "refund" not in response.lower() or "could not process" in response.lower()
    assert len(result.audit_receipts) == 1
    assert result.audit_receipts[0].outcome == "blocked"


# UC5: tool behavior mismatch escalation

def test_uc5_state_mismatch_escalates_and_halts_further_consequential_actions() -> None:
    result = run_support_workflow(fixture_id="support_tool_mismatch_001")

    assert result.status == "escalated_state_mismatch"
    assert result.final_state_match is False
    assert result.mismatch_detail is not None
    assert "expected_delta" in result.mismatch_detail
    assert "observed_delta" in result.mismatch_detail
    assert result.final_state is not None
    # ticket escalated
    ticket = result.final_state["tickets"]["tkt_mismatch_001"]
    assert ticket["status"] == "escalated_state_mismatch"
    # audit receipt with escalated outcome
    assert len(result.audit_receipts) == 1
    assert result.audit_receipts[0].outcome == "escalated"
