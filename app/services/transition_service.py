"""Intended and observed transition validation."""

from typing import Any

from pydantic import BaseModel, Field

from app.models.extraction import TransitionId
from app.models.state import RefundStatus, SupportState
from app.services.state_service import snapshot_state


def transition_matches(expected_transition_id: str, observed_transition_ids: list[str]) -> bool:
    return expected_transition_id in observed_transition_ids


class TransitionValidationResult(BaseModel):
    expected_transition_ids: list[str]
    observed_transition_ids: list[str]
    matches: bool
    expected_delta: dict[str, Any] = Field(default_factory=dict)
    observed_delta: dict[str, Any] = Field(default_factory=dict)
    reason: str


def _coerce_state(state: SupportState | dict[str, Any]) -> SupportState:
    if isinstance(state, SupportState):
        return state
    return SupportState.model_validate(state)


def observe_refund_transitions(
    pre_state: SupportState | dict[str, Any],
    post_state: SupportState | dict[str, Any],
    payment_id: str,
    amount: float,
) -> list[str]:
    pre = _coerce_state(pre_state)
    post = _coerce_state(post_state)
    observed: list[str] = []

    pre_refund_ids = set(pre.refunds)
    new_completed_refunds = [
        refund
        for refund_id, refund in post.refunds.items()
        if refund_id not in pre_refund_ids
        and refund.payment_id == payment_id
        and refund.amount == amount
        and refund.status == RefundStatus.COMPLETED
    ]
    if len(new_completed_refunds) == 1:
        observed.append(TransitionId.REFUND_CREATE.value)

    pre_payment = pre.payments.get(payment_id)
    post_payment = post.payments.get(payment_id)
    if (
        pre_payment is not None
        and post_payment is not None
        and pre_payment.refunded_amount == 0
        and post_payment.refunded_amount == amount
    ):
        observed.append(TransitionId.PAYMENT_REFUNDED_AMOUNT.value)

    return observed


def validate_refund_transition(
    pre_state: SupportState | dict[str, Any],
    post_state: SupportState | dict[str, Any],
    payment_id: str,
    amount: float,
    expected_transition_ids: list[str] | None = None,
) -> TransitionValidationResult:
    expected = expected_transition_ids or [
        TransitionId.REFUND_CREATE.value,
        TransitionId.PAYMENT_REFUNDED_AMOUNT.value,
    ]
    observed = observe_refund_transitions(pre_state, post_state, payment_id, amount)
    missing = [transition_id for transition_id in expected if transition_id not in observed]
    matches = not missing

    return TransitionValidationResult(
        expected_transition_ids=expected,
        observed_transition_ids=observed,
        matches=matches,
        expected_delta={
            "payment_id": payment_id,
            "refund_amount": amount,
            "transitions": expected,
        },
        observed_delta={
            "payment_id": payment_id,
            "refund_amount": snapshot_state(post_state)
            .get("payments", {})
            .get(payment_id, {})
            .get("refunded_amount"),
            "transitions": observed,
        },
        reason="Observed transition matched expected transition."
        if matches
        else f"Missing expected transitions: {missing}",
    )
