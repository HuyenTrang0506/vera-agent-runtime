"""Hardcoded P0 policy predicates."""

from app.domains.support.policies import P_NO_ALREADY_REFUNDED, P_REFUND_DUPLICATE_ONLY
from app.models.enums import PolicyDecision
from app.models.policies import PolicyResult
from app.models.state import PaymentStatus, SupportState
from app.services.idempotency_service import has_completed_refund_for_payment_amount


def allow(reason: str, rule_ids: list[str] | None = None) -> PolicyResult:
    return PolicyResult(decision=PolicyDecision.ALLOW, rule_ids=rule_ids or [], reason=reason)


def deny(reason: str, rule_ids: list[str] | None = None) -> PolicyResult:
    return PolicyResult(decision=PolicyDecision.DENY, rule_ids=rule_ids or [], reason=reason)


def evaluate_refund_policy(state: SupportState, payment_id: str, amount: float) -> PolicyResult:
    payment = state.payments.get(payment_id)
    if payment is not None and has_completed_refund_for_payment_amount(state, payment_id, amount):
        return deny(
            "Refund denied because a completed refund already exists for this payment and amount.",
            [P_NO_ALREADY_REFUNDED],
        )

    if (
        payment is None
        or payment.status != PaymentStatus.CAPTURED
        or payment.duplicate_of is None
    ):
        return deny(
            "Refund denied because payment is not a captured duplicate charge.",
            [P_REFUND_DUPLICATE_ONLY],
        )

    return allow(
        "Refund allowed for captured duplicate payment with no existing completed refund.",
        [P_REFUND_DUPLICATE_ONLY, P_NO_ALREADY_REFUNDED],
    )
