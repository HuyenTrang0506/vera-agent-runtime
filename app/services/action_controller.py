"""State-transition-aware action controller.

This module owns the P0 decision table. Keep domain tool internals out of here.
"""

from app.core.ids import new_id
from app.domains.support.tools import (
    create_refund,
    find_duplicate_payment_for_order,
    find_ticket_for_order,
    resolve_ticket_with_completed_refund,
)
from app.models.enums import WorkflowStatus
from app.models.workflow import WorkflowRunResult
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


class ActionControllerNotImplemented(NotImplementedError):
    """Raised until the P0 controller is implemented."""


def run_support_workflow(
    fixture_id: str = "support_refund_happy_001",
    request_text: str | None = None,
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
    if duplicate_payment is None:
        return WorkflowRunResult(
            workflow_id=workflow_id,
            status=WorkflowStatus.DENIED,
            desired_transition_id=extraction.desired_transition.transition_id,
            policy_decision="deny",
            final_state_match=False,
            audit_receipt_ids=[],
            message="No duplicate captured payment was found.",
        )

    policy = evaluate_refund_policy(
        state,
        payment_id=duplicate_payment.payment_id,
        amount=duplicate_payment.amount,
    )
    if policy.decision != "allow":
        return WorkflowRunResult(
            workflow_id=workflow_id,
            status=WorkflowStatus.DENIED,
            desired_transition_id=extraction.desired_transition.transition_id,
            policy_decision=policy.decision,
            final_state_match=False,
            audit_receipt_ids=[],
            message=policy.reason,
        )

    pre_state = snapshot_state(state)
    pre_refund_hash = state_hash(pre_state)
    idempotency_key = refund_idempotency_key(duplicate_payment.payment_id, duplicate_payment.amount)
    refund_result = create_refund(
        state,
        payment_id=duplicate_payment.payment_id,
        amount=duplicate_payment.amount,
        idempotency_key=idempotency_key,
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
    if not validation.matches:
        return WorkflowRunResult(
            workflow_id=workflow_id,
            status=WorkflowStatus.FAILED_SAFE,
            desired_transition_id=extraction.desired_transition.transition_id,
            policy_decision=policy.decision,
            final_state_match=False,
            audit_receipt_ids=[],
            message=validation.reason,
        )
    if recovered_timeout and refund_result.refund is None:
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
