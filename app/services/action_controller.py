"""State-transition-aware action controller.

This module owns the P0 decision table. Keep domain tool internals out of here.
"""

from pathlib import Path

from app.core.executor import ToolExecutor
from app.core.ids import new_id
from app.core.registry import load_tool_registry
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
from app.services.audit_service import build_receipt, timeline_event_from_receipt
from app.services.idempotency_service import refund_idempotency_key
from app.services.policy_service import evaluate_refund_policy
from app.services.qwen_service import extract_support_request
from app.services.state_service import (
    load_support_fixture,
    runtime_state_from_fixture,
    save_workflow_result,
    snapshot_state,
    state_hash,
)
from app.services.transition_service import observe_refund_transitions

_REGISTRY = load_tool_registry(
    Path(__file__).parent.parent / "registries" / "support_tools.yaml"
)
_REFUND_EXECUTOR = ToolExecutor(
    metadata=_REGISTRY["create_refund"],
    tool_fn=create_refund,
    observe_fn=lambda pre, post, ctx: observe_refund_transitions(
        pre, post, ctx["payment_id"], ctx["amount"]
    ),
)


def _run_support_workflow(
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
        cur_hash = state_hash(state)
        safe_receipt = build_receipt(
            workflow_id=workflow_id,
            action_id="safe_stop_missing_order_id",
            intended_transition="T_REFUND_CREATE",
            observed_transition="none",
            policy_decision=PolicyDecision.DENY,
            pre_state_hash=cur_hash,
            post_state_hash=cur_hash,
            outcome="blocked",
        )
        return WorkflowRunResult(
            workflow_id=workflow_id,
            status=WorkflowStatus.FAILED_SAFE,
            desired_transition_id=extraction.desired_transition.transition_id,
            policy_decision=None,
            final_state_match=False,
            audit_receipt_ids=[safe_receipt.receipt_id],
            audit_receipts=[safe_receipt],
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
    idempotency_key = refund_idempotency_key(
        duplicate_payment.payment_id, duplicate_payment.amount
    )

    exec_result = _REFUND_EXECUTOR.run(
        workflow_id=workflow_id,
        state=state,
        params={
            "payment_id": duplicate_payment.payment_id,
            "amount": duplicate_payment.amount,
            "idempotency_key": idempotency_key,
            "approval_id": approval_id,
        },
        failure_mode=fixture.failure_mode,
        policy_decision=policy.decision,
    )

    # Hard failure — tool errored and nothing committed
    if not exec_result.committed:
        return WorkflowRunResult(
            workflow_id=workflow_id,
            status=WorkflowStatus.FAILED_SAFE,
            desired_transition_id=extraction.desired_transition.transition_id,
            policy_decision=policy.decision,
            final_state_match=False,
            audit_receipt_ids=[exec_result.receipt.receipt_id] if exec_result.receipt else [],
            audit_receipts=[exec_result.receipt] if exec_result.receipt else [],
            message=exec_result.error,
        )

    # UC5: state mismatch escalation (committed but transitions not observed)
    if exec_result.receipt and exec_result.receipt.outcome == "escalated":
        ticket = find_ticket_for_order(state, order_id)
        if ticket is not None:
            update_ticket_to_mismatch_escalation(state, ticket_id=ticket.ticket_id)
        expected = _REGISTRY["create_refund"].transition_effects
        return WorkflowRunResult(
            workflow_id=workflow_id,
            status=WorkflowStatus.ESCALATED_STATE_MISMATCH,
            desired_transition_id=extraction.desired_transition.transition_id,
            policy_decision=policy.decision,
            final_state_match=False,
            audit_receipt_ids=[exec_result.receipt.receipt_id],
            audit_receipts=[exec_result.receipt],
            final_state=snapshot_state(state),
            mismatch_detail={
                "expected_delta": {"transitions": expected},
                "observed_delta": {"transitions": exec_result.observed_transitions},
            },
            message=f"Missing expected transitions: {[t for t in expected if t not in exec_result.observed_transitions]}",
        )

    # timeout_after_commit but state not confirmed — failed safe
    if not exec_result.success and exec_result.committed:
        return WorkflowRunResult(
            workflow_id=workflow_id,
            status=WorkflowStatus.FAILED_SAFE,
            desired_transition_id=extraction.desired_transition.transition_id,
            policy_decision=policy.decision,
            final_state_match=False,
            audit_receipt_ids=[exec_result.receipt.receipt_id] if exec_result.receipt else [],
            audit_receipts=[exec_result.receipt] if exec_result.receipt else [],
            message="Timeout-after-commit recovery could not find committed refund.",
        )

    refund_receipt = exec_result.receipt

    # Find refund id from state for ticket resolution
    refund_id = None
    pre_refunds = set()  # executor already ran, find new refund in state
    for rid, r in state.refunds.items():
        if r.payment_id == duplicate_payment.payment_id:
            refund_id = rid
            break

    ticket = find_ticket_for_order(state, order_id)
    if ticket is None or refund_id is None:
        return WorkflowRunResult(
            workflow_id=workflow_id,
            status=WorkflowStatus.FAILED_SAFE,
            desired_transition_id=extraction.desired_transition.transition_id,
            policy_decision=policy.decision,
            final_state_match=False,
            audit_receipt_ids=[refund_receipt.receipt_id] if refund_receipt else [],
            audit_receipts=[refund_receipt] if refund_receipt else [],
            message="Cannot resolve ticket because ticket or refund is missing.",
        )

    pre_ticket_hash = state_hash(state)
    ticket_update = resolve_ticket_with_completed_refund(
        state,
        ticket_id=ticket.ticket_id,
        refund_id=refund_id,
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
    audit_receipts = [r for r in [refund_receipt, ticket_receipt] if r is not None]
    reason = "Observed transition matched expected transition."

    return WorkflowRunResult(
        workflow_id=workflow_id,
        status=WorkflowStatus.COMPLETED_WITH_RECOVERED_TIMEOUT
        if exec_result.recovered_timeout
        else WorkflowStatus.COMPLETED,
        desired_transition_id=extraction.desired_transition.transition_id,
        policy_decision=policy.decision,
        final_state_match=True,
        audit_receipt_ids=[r.receipt_id for r in audit_receipts],
        audit_receipts=audit_receipts,
        final_state=snapshot_state(state),
        message=(
            f"{reason} Timeout-after-commit recovered by state recheck. "
            "Ticket resolved and response drafted."
            if exec_result.recovered_timeout
            else f"{reason} Ticket resolved and response drafted."
        ),
    )


def run_support_workflow(
    fixture_id: str = "support_refund_happy_001",
    request_text: str | None = None,
    approval_record: ApprovalRecord | None = None,
) -> WorkflowRunResult:
    result = _run_support_workflow(
        fixture_id=fixture_id,
        request_text=request_text,
        approval_record=approval_record,
    )
    result.timeline_events = [
        timeline_event_from_receipt(receipt) for receipt in result.audit_receipts
    ]
    save_workflow_result(result)
    return result
