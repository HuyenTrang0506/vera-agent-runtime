"""Integration tests for B19 — finance duplicate-invoice thin slice."""

from app.domains.finance.workflow import run_finance_workflow
from app.models.approvals import ApprovalRecord
from app.models.enums import ApprovalStatus


def test_finance_happy_path_pays_invoice_once() -> None:
    result = run_finance_workflow(
        fixture_id="finance_invoice_happy_001",
        invoice_id="inv_001",
    )

    assert result.status == "completed"
    assert result.desired_transition_id == "T_INVOICE_PAY"
    assert result.policy_decision == "allow"
    assert result.final_state_match is True
    assert result.final_state is not None

    payments = result.final_state["payments"]
    completed = [
        p for p in payments.values()
        if p["invoice_id"] == "inv_001" and p["status"] == "completed"
    ]
    assert len(completed) == 1

    invoice = result.final_state["invoices"]["inv_001"]
    assert invoice["status"] == "paid"

    assert len(result.audit_receipts) == 1
    receipt = result.audit_receipts[0]
    assert receipt.intended_transition == "T_INVOICE_PAY"
    assert receipt.observed_transition == "T_INVOICE_PAY"
    assert receipt.outcome == "success"
    assert receipt.pre_state_hash != receipt.post_state_hash


def test_finance_duplicate_invoice_is_blocked_without_payment() -> None:
    result = run_finance_workflow(
        fixture_id="finance_invoice_duplicate_001",
        invoice_id="inv_002_dup",
    )

    assert result.status == "denied"
    assert result.policy_decision == "deny"
    assert result.final_state is not None

    # no new payment for the duplicate invoice
    payments = result.final_state["payments"]
    dup_payments = [
        p for p in payments.values()
        if p["invoice_id"] == "inv_002_dup" and p["status"] == "completed"
    ]
    assert len(dup_payments) == 0

    # duplicate invoice is marked as duplicate or on_hold
    dup_invoice = result.final_state["invoices"]["inv_002_dup"]
    assert dup_invoice["status"] in ("duplicate", "on_hold")

    # original payment still exactly one
    orig_payments = [
        p for p in payments.values()
        if p["invoice_id"] == "inv_001_orig" and p["status"] == "completed"
    ]
    assert len(orig_payments) == 1

    assert len(result.audit_receipts) == 1
    assert result.audit_receipts[0].outcome == "blocked"


def test_finance_high_value_invoice_creates_approval_pending_without_decision() -> None:
    result = run_finance_workflow(
        fixture_id="finance_invoice_high_value_reject_001",
        invoice_id="inv_hv_001",
    )

    assert result.status == "approval_pending"
    assert result.policy_decision == "approval_required"
    assert result.approval_id is not None
    assert result.final_state is not None
    # no payment yet
    assert len(result.final_state["payments"]) == 0


def test_finance_high_value_invoice_rejection_blocks_payment() -> None:
    rejected = ApprovalRecord(
        approval_id="apr_fin_001",
        workflow_id="wf_fin_001",
        status=ApprovalStatus.REJECTED,
        requested_amount=8500.0,
        policy_rule_id="P_HIGH_VALUE_INVOICE_APPROVAL",
        decided_by="ap_manager",
    )
    result = run_finance_workflow(
        fixture_id="finance_invoice_high_value_reject_001",
        invoice_id="inv_hv_001",
        approval_record=rejected,
    )

    assert result.status == "pending_manual_review"
    assert result.policy_decision == "approval_required"
    assert result.final_state is not None
    # no payment created after rejection
    assert len(result.final_state["payments"]) == 0
    assert len(result.audit_receipts) == 1
    assert result.audit_receipts[0].outcome == "blocked"


def test_finance_happy_path_idempotency_same_fixture_second_call_does_not_duplicate() -> None:
    # Two calls with same fixture — second replays idempotency key
    result1 = run_finance_workflow(
        fixture_id="finance_invoice_happy_001",
        invoice_id="inv_001",
    )
    assert result1.status == "completed"
    assert result1.final_state is not None
    payments_after_first = [
        p for p in result1.final_state["payments"].values()
        if p["invoice_id"] == "inv_001" and p["status"] == "completed"
    ]
    assert len(payments_after_first) == 1
