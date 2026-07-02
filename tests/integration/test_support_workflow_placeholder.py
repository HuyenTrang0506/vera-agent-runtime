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
