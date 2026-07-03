"""Finance duplicate-invoice workflow (P1 thin slice).

Mirrors the support action_controller pattern:
  load fixture → check vendor → detect duplicate → policy → approval → pay_invoice
  → validate state → audit receipt
"""

from app.core.ids import new_id
from app.domains.finance.policies import (
    P_HIGH_VALUE_INVOICE_APPROVAL,
    P_INVOICE_ALREADY_PAID,
    P_INVOICE_DUPLICATE_BLOCK,
    P_VENDOR_MUST_BE_ACTIVE,
)
from app.domains.finance.tools import (
    find_completed_payment_for_invoice,
    find_duplicate_invoice,
    hold_invoice,
    mark_invoice_duplicate,
    pay_invoice,
)
from app.models.approvals import ApprovalRecord
from app.models.enums import PolicyDecision, WorkflowStatus
from app.models.finance import FinancePaymentStatus, InvoiceStatus, VendorStatus
from app.models.policies import PolicyResult
from app.models.workflow import WorkflowRunResult
from app.services.approval_service import create_approval, is_approved, is_rejected
from app.services.audit_service import build_receipt, timeline_event_from_receipt
from app.core.config import settings
from app.services.state_service import (
    load_finance_fixture,
    save_workflow_result,
    snapshot_state,
    state_hash,
)


def _evaluate_invoice_policy(state, invoice_id: str) -> PolicyResult:
    from app.models.policies import PolicyResult

    invoice = state.invoices.get(invoice_id)
    if invoice is None:
        return PolicyResult(
            decision=PolicyDecision.DENY,
            rule_ids=[P_INVOICE_DUPLICATE_BLOCK],
            reason="Invoice not found.",
        )

    vendor = state.vendors.get(invoice.vendor_id)
    if vendor is None or vendor.status != VendorStatus.ACTIVE:
        return PolicyResult(
            decision=PolicyDecision.DENY,
            rule_ids=[P_VENDOR_MUST_BE_ACTIVE],
            reason=f"Vendor {invoice.vendor_id} is not active.",
        )

    if invoice.status == InvoiceStatus.PAID:
        return PolicyResult(
            decision=PolicyDecision.DENY,
            rule_ids=[P_INVOICE_ALREADY_PAID],
            reason="Invoice is already paid.",
        )

    if invoice.status == InvoiceStatus.DUPLICATE or invoice.duplicate_of is not None:
        return PolicyResult(
            decision=PolicyDecision.DENY,
            rule_ids=[P_INVOICE_DUPLICATE_BLOCK],
            reason="Invoice is marked as a duplicate — payment blocked.",
        )

    existing_payment = find_completed_payment_for_invoice(state, invoice_id)
    if existing_payment is not None:
        return PolicyResult(
            decision=PolicyDecision.DENY,
            rule_ids=[P_INVOICE_ALREADY_PAID],
            reason="A completed payment already exists for this invoice.",
        )

    if invoice.amount >= settings.finance_approval_threshold:
        return PolicyResult(
            decision=PolicyDecision.APPROVAL_REQUIRED,
            rule_ids=[P_HIGH_VALUE_INVOICE_APPROVAL],
            reason=f"Invoice amount {invoice.amount:.2f} requires approval.",
        )

    return PolicyResult(
        decision=PolicyDecision.ALLOW,
        rule_ids=[P_VENDOR_MUST_BE_ACTIVE, P_INVOICE_DUPLICATE_BLOCK, P_INVOICE_ALREADY_PAID],
        reason="Invoice payment allowed.",
    )


def run_finance_workflow(
    fixture_id: str,
    invoice_id: str,
    approval_record: ApprovalRecord | None = None,
) -> WorkflowRunResult:
    fixture = load_finance_fixture(fixture_id)
    state = fixture.state.model_copy(deep=True)
    workflow_id = new_id("wf_fin_")

    # Check whether incoming invoice is a duplicate of an already-paid one
    duplicate_original = find_duplicate_invoice(state, invoice_id)
    if duplicate_original is not None:
        already_paid = find_completed_payment_for_invoice(state, duplicate_original.invoice_id)
        if already_paid is not None:
            mark_invoice_duplicate(state, invoice_id, duplicate_original.invoice_id)
            pre_hash = state_hash(state)
            hold_invoice(state, invoice_id, "Duplicate of already-paid invoice.")
            post_hash = state_hash(state)
            receipt = build_receipt(
                workflow_id=workflow_id,
                action_id="mark_invoice_duplicate",
                intended_transition="T_INVOICE_DUPLICATE_BLOCK",
                observed_transition="T_INVOICE_DUPLICATE_BLOCK",
                policy_decision=PolicyDecision.DENY,
                pre_state_hash=pre_hash,
                post_state_hash=post_hash,
                outcome="blocked",
            )
            result = WorkflowRunResult(
                workflow_id=workflow_id,
                status=WorkflowStatus.DENIED,
                desired_transition_id="T_INVOICE_PAY",
                policy_decision=PolicyDecision.DENY,
                final_state_match=True,
                audit_receipt_ids=[receipt.receipt_id],
                audit_receipts=[receipt],
                final_state=snapshot_state(state),
                message=f"Invoice {invoice_id} is a duplicate of already-paid {duplicate_original.invoice_id}. Payment blocked.",
            )
            result.timeline_events = [timeline_event_from_receipt(r) for r in result.audit_receipts]
            save_workflow_result(result)
            return result

    policy = _evaluate_invoice_policy(state, invoice_id)

    if policy.decision == PolicyDecision.DENY:
        pre_hash = state_hash(state)
        receipt = build_receipt(
            workflow_id=workflow_id,
            action_id="policy_check",
            intended_transition="T_INVOICE_PAY",
            observed_transition="none",
            policy_decision=PolicyDecision.DENY,
            pre_state_hash=pre_hash,
            post_state_hash=pre_hash,
            outcome="blocked",
        )
        result = WorkflowRunResult(
            workflow_id=workflow_id,
            status=WorkflowStatus.DENIED,
            desired_transition_id="T_INVOICE_PAY",
            policy_decision=PolicyDecision.DENY,
            final_state_match=True,
            audit_receipt_ids=[receipt.receipt_id],
            audit_receipts=[receipt],
            final_state=snapshot_state(state),
            message=policy.reason,
        )
        result.timeline_events = [timeline_event_from_receipt(r) for r in result.audit_receipts]
        save_workflow_result(result)
        return result

    if policy.decision == PolicyDecision.APPROVAL_REQUIRED:
        if approval_record is not None:
            if is_rejected(approval_record):
                pre_hash = state_hash(state)
                hold_invoice(state, invoice_id, "High-value approval rejected.")
                post_hash = state_hash(state)
                receipt = build_receipt(
                    workflow_id=workflow_id,
                    action_id=approval_record.approval_id,
                    intended_transition="T_INVOICE_PAY",
                    observed_transition="T_APPROVAL_REJECTED",
                    policy_decision=PolicyDecision.APPROVAL_REQUIRED,
                    pre_state_hash=pre_hash,
                    post_state_hash=post_hash,
                    outcome="blocked",
                )
                result = WorkflowRunResult(
                    workflow_id=workflow_id,
                    status=WorkflowStatus.PENDING_MANUAL_REVIEW,
                    desired_transition_id="T_INVOICE_PAY",
                    policy_decision=PolicyDecision.APPROVAL_REQUIRED,
                    final_state_match=True,
                    audit_receipt_ids=[receipt.receipt_id],
                    audit_receipts=[receipt],
                    final_state=snapshot_state(state),
                    message="High-value invoice payment rejected by approver.",
                )
                result.timeline_events = [timeline_event_from_receipt(r) for r in result.audit_receipts]
                save_workflow_result(result)
                return result
            if not is_approved(approval_record):
                result = WorkflowRunResult(
                    workflow_id=workflow_id,
                    status=WorkflowStatus.APPROVAL_PENDING,
                    desired_transition_id="T_INVOICE_PAY",
                    policy_decision=PolicyDecision.APPROVAL_REQUIRED,
                    final_state_match=False,
                    audit_receipt_ids=[],
                    approval_id=approval_record.approval_id,
                    final_state=snapshot_state(state),
                    message="Invoice payment pending high-value approval.",
                )
                save_workflow_result(result)
                return result
            # approved — fall through
        else:
            invoice = state.invoices[invoice_id]
            approval = create_approval(
                workflow_id=workflow_id,
                requested_amount=invoice.amount,
                policy_rule_id=P_HIGH_VALUE_INVOICE_APPROVAL,
            )
            pre_hash = state_hash(state)
            approval_receipt = build_receipt(
                workflow_id=workflow_id,
                action_id=approval.approval_id,
                intended_transition="T_APPROVAL_PENDING",
                observed_transition="T_APPROVAL_PENDING",
                policy_decision=PolicyDecision.APPROVAL_REQUIRED,
                pre_state_hash=pre_hash,
                post_state_hash=pre_hash,
                outcome="blocked",
            )
            result = WorkflowRunResult(
                workflow_id=workflow_id,
                status=WorkflowStatus.APPROVAL_PENDING,
                desired_transition_id="T_INVOICE_PAY",
                policy_decision=PolicyDecision.APPROVAL_REQUIRED,
                final_state_match=False,
                audit_receipt_ids=[approval_receipt.receipt_id],
                audit_receipts=[approval_receipt],
                approval_id=approval.approval_id,
                final_state=snapshot_state(state),
                message=policy.reason,
            )
            result.timeline_events = [timeline_event_from_receipt(r) for r in result.audit_receipts]
            save_workflow_result(result)
            return result

    # Execute payment
    invoice = state.invoices[invoice_id]
    idempotency_key = f"inv_{invoice_id}_{invoice.amount:.2f}"
    approval_id = approval_record.approval_id if approval_record else None

    pre_hash = state_hash(state)
    pay_result = pay_invoice(
        state,
        invoice_id=invoice_id,
        idempotency_key=idempotency_key,
        failure_mode=fixture.failure_mode,
    )
    post_hash = state_hash(state)

    if not pay_result.success and pay_result.error != "timeout_after_commit":
        receipt = build_receipt(
            workflow_id=workflow_id,
            action_id="pay_invoice",
            intended_transition="T_INVOICE_PAY",
            observed_transition="none",
            policy_decision=PolicyDecision.ALLOW,
            pre_state_hash=pre_hash,
            post_state_hash=post_hash,
            outcome="failed",
        )
        result = WorkflowRunResult(
            workflow_id=workflow_id,
            status=WorkflowStatus.FAILED_SAFE,
            desired_transition_id="T_INVOICE_PAY",
            policy_decision=PolicyDecision.ALLOW,
            final_state_match=False,
            audit_receipt_ids=[receipt.receipt_id],
            audit_receipts=[receipt],
            message=pay_result.error,
        )
        result.timeline_events = [timeline_event_from_receipt(r) for r in result.audit_receipts]
        save_workflow_result(result)
        return result

    recovered_timeout = pay_result.error == "timeout_after_commit"
    outcome = "recovered" if recovered_timeout else "success"

    # Verify payment committed
    final_invoice = state.invoices.get(invoice_id)
    paid_correctly = (
        final_invoice is not None
        and final_invoice.status == InvoiceStatus.PAID
        and find_completed_payment_for_invoice(state, invoice_id) is not None
    )

    if not paid_correctly and not recovered_timeout:
        receipt = build_receipt(
            workflow_id=workflow_id,
            action_id="pay_invoice",
            intended_transition="T_INVOICE_PAY",
            observed_transition="none",
            policy_decision=PolicyDecision.ALLOW,
            pre_state_hash=pre_hash,
            post_state_hash=post_hash,
            outcome="escalated",
        )
        result = WorkflowRunResult(
            workflow_id=workflow_id,
            status=WorkflowStatus.ESCALATED_STATE_MISMATCH,
            desired_transition_id="T_INVOICE_PAY",
            policy_decision=PolicyDecision.ALLOW,
            final_state_match=False,
            audit_receipt_ids=[receipt.receipt_id],
            audit_receipts=[receipt],
            final_state=snapshot_state(state),
            message="Invoice payment reported success but invoice state was not updated.",
        )
        result.timeline_events = [timeline_event_from_receipt(r) for r in result.audit_receipts]
        save_workflow_result(result)
        return result

    receipt = build_receipt(
        workflow_id=workflow_id,
        action_id=pay_result.payment.payment_id if pay_result.payment else "pay_invoice",
        intended_transition="T_INVOICE_PAY",
        observed_transition="T_INVOICE_PAY",
        policy_decision=policy.decision,
        pre_state_hash=pre_hash,
        post_state_hash=post_hash,
        outcome=outcome,
    )

    final_state = snapshot_state(state)
    count_paid = sum(
        1 for p in state.payments.values()
        if p.invoice_id == invoice_id and p.status == FinancePaymentStatus.COMPLETED
    )
    final_state_match = count_paid == 1

    status = (
        WorkflowStatus.COMPLETED_WITH_RECOVERED_TIMEOUT
        if recovered_timeout
        else WorkflowStatus.COMPLETED
    )
    result = WorkflowRunResult(
        workflow_id=workflow_id,
        status=status,
        desired_transition_id="T_INVOICE_PAY",
        policy_decision=policy.decision,
        final_state_match=final_state_match,
        audit_receipt_ids=[receipt.receipt_id],
        audit_receipts=[receipt],
        final_state=final_state,
        message=(
            f"Invoice {invoice_id} paid once. Timeout-after-commit recovered by state recheck."
            if recovered_timeout
            else f"Invoice {invoice_id} paid once. Vendor: {invoice.vendor_id}."
        ),
    )
    result.timeline_events = [timeline_event_from_receipt(r) for r in result.audit_receipts]
    save_workflow_result(result)
    return result
