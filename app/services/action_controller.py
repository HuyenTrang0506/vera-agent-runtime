"""State-transition-aware action controller.

This module owns the P0 decision table. Keep domain tool internals out of here.
"""

from app.core.ids import new_id
from app.domains.support.tools import (
    create_refund,
    find_duplicate_payment_for_order,
    find_ticket_for_order,
    resolve_ticket_with_completed_refund,
    update_ticket_to_denied,
    update_ticket_to_manual_review,
    update_ticket_to_mismatch_escalation,
)
from app.models.approvals import ApprovalRecord
from app.models.enums import PolicyDecision, WorkflowStatus
from app.models.workflow import WorkflowRunResult
from app.services.approval_service import create_approval, is_approved, is_rejected
from app.services.audit_service import build_receipt
from app.services.idempotency_service import refund_idempotency_key
from app.services.policy_service import evaluate_refund_policy
from app.services.qwen_service import extract_support_request
from app.services.recovery_service import should_recheck_state
from app.services.state_service import (
    load_support_fixture,
    runtime_state_from_fixture,
    snapshot_state,
    state_hash,
)
from app.services.transition_service import validate_refund_transition


def run_support_workflow(
    fixture_id: str = "support_refund_happy_001",
    request_text: str | None = None,
    approval_record: ApprovalRecord | None = None,
) -> WorkflowRunResult:
    fixture = load_support_fixture(fixture_id)
    state = runtime_state_from_fixture(fixture)
    extraction_result = extract_support_request(
        request_text=request_text or "",
        fixture=fixture,
        model_mode="fixture_fallback",
    )
    extraction = extraction_result.extraction
    workflow_id = new_id("wf_")
    order_id = extraction.entities.order_id

    if order_id is None:
        return WorkflowRunResult(
            workflow_id=workflow_id,
            status=WorkflowStatus.FAILED_SAFE,
            desired_transition_id=extraction.desired_transition.transition_id,
            policy_decision=None,
            final_state_match=False,
            audit_receipt_ids=[],
            message="Extraction did not identify an order_id.",
        )

    duplicate_payment = find_duplicate_payment_for_order(state, order_id)

    # UC4: no duplicate → deny
    if duplicate_payment is None:
        ticket = find_ticket_for_order(state, order_id)
        if ticket is not None:
            update_ticket_to_denied(
                state,
                ticket_id=ticket.ticket_id,
                reason="No duplicate captured payment found for this order.",
            )
        deny_receipt = build_receipt(
            workflow_id=workflow_id,
            action_id="policy_check",
            intended_transition="T_REFUND_CREATE",
            observed_transition="none",
            policy_decision=PolicyDecision.DENY,
            pre_state_hash=state_hash(state),
            post_state_hash=state_hash(state),
            outcome="blocked",
        )
        return WorkflowRunResult(
            workflow_id=workflow_id,
            status=WorkflowStatus.DENIED,
            desired_transition_id=extraction.desired_transition.transition_id,
            policy_decision=PolicyDecision.DENY,
            final_state_match=False,
            audit_receipt_ids=[deny_receipt.receipt_id],
            audit_receipts=[deny_receipt],
            final_state=snapshot_state(state),
            message="No duplicate captured payment was found.",
        )

    policy = evaluate_refund_policy(
        state,
        payment_id=duplicate_payment.payment_id,
        amount=duplicate_payment.amount,
    )

    # Deny path (not approval_required, just deny)
    if policy.decision == PolicyDecision.DENY:
        ticket = find_ticket_for_order(state, order_id)
        if ticket is not None:
            update_ticket_to_denied(
                state,
                ticket_id=ticket.ticket_id,
                reason=policy.reason,
            )
        deny_receipt = build_receipt(
            workflow_id=workflow_id,
            action_id="policy_check",
            intended_transition="T_REFUND_CREATE",
            observed_transition="none",
            policy_decision=policy.decision,
            pre_state_hash=state_hash(state),
            post_state_hash=state_hash(state),
            outcome="blocked",
        )
        return WorkflowRunResult(
            workflow_id=workflow_id,
            status=WorkflowStatus.DENIED,
            desired_transition_id=extraction.desired_transition.transition_id,
            policy_decision=policy.decision,
            final_state_match=False,
            audit_receipt_ids=[deny_receipt.receipt_id],
            audit_receipts=[deny_receipt],
            final_state=snapshot_state(state),
            message=policy.reason,
        )

    # UC3: approval_required path
    if policy.decision == PolicyDecision.APPROVAL_REQUIRED:
        # If an approval_record was passed in (resume after decision), handle it
        if approval_record is not None:
            if is_rejected(approval_record):
                ticket = find_ticket_for_order(state, order_id)
                if ticket is not None:
                    update_ticket_to_manual_review(
                        state,
                        ticket_id=ticket.ticket_id,
                        reason="High-value refund approval was rejected.",
                    )
                rejection_receipt = build_receipt(
                    workflow_id=workflow_id,
                    action_id=approval_record.approval_id,
                    intended_transition="T_REFUND_CREATE",
                    observed_transition="T_APPROVAL_REJECTED",
                    policy_decision=policy.decision,
                    pre_state_hash=state_hash(state),
                    post_state_hash=state_hash(state),
                    outcome="blocked",
                )
                return WorkflowRunResult(
                    workflow_id=workflow_id,
                    status=WorkflowStatus.PENDING_MANUAL_REVIEW,
                    desired_transition_id=extraction.desired_transition.transition_id,
                    policy_decision=policy.decision,
                    final_state_match=False,
                    audit_receipt_ids=[rejection_receipt.receipt_id],
                    audit_receipts=[rejection_receipt],
                    final_state=snapshot_state(state),
                    message="High-value refund rejected by manager. Ticket moved to manual review.",
                )
            if not is_approved(approval_record):
                return WorkflowRunResult(
                    workflow_id=workflow_id,
                    status=WorkflowStatus.APPROVAL_PENDING,
                    desired_transition_id=extraction.desired_transition.transition_id,
                    policy_decision=policy.decision,
                    final_state_match=False,
                    audit_receipt_ids=[],
                    approval_id=approval_record.approval_id,
                    final_state=snapshot_state(state),
                    message="High-value refund is still pending approval.",
                )
            # approved -> fall through to execution below with approval_id
        else:
            # No decision yet — create approval and pause
            approval = create_approval(
                workflow_id=workflow_id,
                requested_amount=duplicate_payment.amount,
                policy_rule_id=policy.rule_ids[0] if policy.rule_ids else "P_HIGH_VALUE_APPROVAL",
            )
            approval_receipt = build_receipt(
                workflow_id=workflow_id,
                action_id=approval.approval_id,
                intended_transition="T_APPROVAL_PENDING",
                observed_transition="T_APPROVAL_PENDING",
                policy_decision=policy.decision,
                pre_state_hash=state_hash(state),
                post_state_hash=state_hash(state),
                outcome="blocked",
            )
            return WorkflowRunResult(
                workflow_id=workflow_id,
                status=WorkflowStatus.APPROVAL_PENDING,
                desired_transition_id=extraction.desired_transition.transition_id,
                policy_decision=policy.decision,
                final_state_match=False,
                audit_receipt_ids=[approval_receipt.receipt_id],
                audit_receipts=[approval_receipt],
                approval_id=approval.approval_id,
                final_state=snapshot_state(state),
                message=f"High-value refund of {duplicate_payment.amount:.2f} requires approval.",
            )

    # Execute refund (allow or approved)
    approval_id = approval_record.approval_id if approval_record is not None else None

    pre_state = snapshot_state(state)
    pre_refund_hash = state_hash(pre_state)
    idempotency_key = refund_idempotency_key(
        duplicate_payment.payment_id, duplicate_payment.amount
    )
    refund_result = create_refund(
        state,
        payment_id=duplicate_payment.payment_id,
        amount=duplicate_payment.amount,
        idempotency_key=idempotency_key,
        approval_id=approval_id,
        failure_mode=fixture.failure_mode,
    )
    recovered_timeout = False
    if not refund_result.success and should_recheck_state(refund_result.error or ""):
        recovered_timeout = True
    elif not refund_result.success:
        return WorkflowRunResult(
            workflow_id=workflow_id,
            status=WorkflowStatus.FAILED_SAFE,
            desired_transition_id=extraction.desired_transition.transition_id,
            policy_decision=policy.decision,
            final_state_match=False,
            audit_receipt_ids=[],
            message=refund_result.error,
        )
    post_refund_hash = state_hash(state)

    validation = validate_refund_transition(
        pre_state,
        state,
        payment_id=duplicate_payment.payment_id,
        amount=duplicate_payment.amount,
    )

    # UC5: state mismatch escalation
    if not validation.matches and not recovered_timeout:
        ticket = find_ticket_for_order(state, order_id)
        if ticket is not None:
            update_ticket_to_mismatch_escalation(state, ticket_id=ticket.ticket_id)
        mismatch_receipt = build_receipt(
            workflow_id=workflow_id,
            action_id=refund_result.refund.refund_id if refund_result.refund else "create_refund",
            intended_transition="T_REFUND_CREATE,T_PAYMENT_REFUNDED_AMOUNT",
            observed_transition=",".join(validation.observed_transition_ids) or "none",
            policy_decision=policy.decision,
            pre_state_hash=pre_refund_hash,
            post_state_hash=post_refund_hash,
            outcome="escalated",
        )
        return WorkflowRunResult(
            workflow_id=workflow_id,
            status=WorkflowStatus.ESCALATED_STATE_MISMATCH,
            desired_transition_id=extraction.desired_transition.transition_id,
            policy_decision=policy.decision,
            final_state_match=False,
            audit_receipt_ids=[mismatch_receipt.receipt_id],
            audit_receipts=[mismatch_receipt],
            final_state=snapshot_state(state),
            mismatch_detail={
                "expected_delta": validation.expected_delta,
                "observed_delta": validation.observed_delta,
            },
            message=validation.reason,
        )

    if not validation.matches and recovered_timeout:
        return WorkflowRunResult(
            workflow_id=workflow_id,
            status=WorkflowStatus.FAILED_SAFE,
            desired_transition_id=extraction.desired_transition.transition_id,
            policy_decision=policy.decision,
            final_state_match=False,
            audit_receipt_ids=[],
            message="Timeout-after-commit recovery could not find committed refund.",
        )

    refund_outcome = "recovered" if recovered_timeout else "success"
    refund_receipt = build_receipt(
        workflow_id=workflow_id,
        action_id=refund_result.refund.refund_id if refund_result.refund else "create_refund",
        intended_transition="T_REFUND_CREATE,T_PAYMENT_REFUNDED_AMOUNT",
        observed_transition=",".join(validation.observed_transition_ids),
        policy_decision=policy.decision,
        pre_state_hash=pre_refund_hash,
        post_state_hash=post_refund_hash,
        outcome=refund_outcome,
    )

    ticket = find_ticket_for_order(state, order_id)
    if ticket is None or refund_result.refund is None:
        return WorkflowRunResult(
            workflow_id=workflow_id,
            status=WorkflowStatus.FAILED_SAFE,
            desired_transition_id=extraction.desired_transition.transition_id,
            policy_decision=policy.decision,
            final_state_match=False,
            audit_receipt_ids=[],
            message="Cannot resolve ticket because ticket or refund is missing.",
        )

    pre_ticket_hash = state_hash(state)
    ticket_update = resolve_ticket_with_completed_refund(
        state,
        ticket_id=ticket.ticket_id,
        refund_id=refund_result.refund.refund_id,
    )
    if not ticket_update.success:
        return WorkflowRunResult(
            workflow_id=workflow_id,
            status=WorkflowStatus.FAILED_SAFE,
            desired_transition_id=extraction.desired_transition.transition_id,
            policy_decision=policy.decision,
            final_state_match=False,
            audit_receipt_ids=[],
            message=ticket_update.error,
        )
    post_ticket_hash = state_hash(state)
    ticket_receipt = build_receipt(
        workflow_id=workflow_id,
        action_id=ticket.ticket_id,
        intended_transition="T_TICKET_RESOLVE",
        observed_transition="T_TICKET_RESOLVE",
        policy_decision=policy.decision,
        pre_state_hash=pre_ticket_hash,
        post_state_hash=post_ticket_hash,
        outcome="success",
    )
    audit_receipts = [refund_receipt, ticket_receipt]

    return WorkflowRunResult(
        workflow_id=workflow_id,
        status=WorkflowStatus.COMPLETED_WITH_RECOVERED_TIMEOUT
        if recovered_timeout
        else WorkflowStatus.COMPLETED,
        desired_transition_id=extraction.desired_transition.transition_id,
        policy_decision=policy.decision,
        final_state_match=True,
        audit_receipt_ids=[receipt.receipt_id for receipt in audit_receipts],
        audit_receipts=audit_receipts,
        final_state=snapshot_state(state),
        message=(
            f"{validation.reason} Timeout-after-commit recovered by state recheck. "
            "Ticket resolved and response drafted."
            if recovered_timeout
            else f"{validation.reason} Ticket resolved and response drafted."
        ),
    )
