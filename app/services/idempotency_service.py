"""Idempotency helpers for consequential actions."""

from hashlib import sha256

from app.models.state import Refund, RefundStatus, SupportState


def refund_idempotency_key(payment_id: str, amount: float) -> str:
    raw = f"refund:{payment_id}:{amount:.2f}"
    return sha256(raw.encode("utf-8")).hexdigest()[:24]


def find_refund_by_idempotency_key(state: SupportState, idempotency_key: str) -> Refund | None:
    for refund in state.refunds.values():
        if refund.idempotency_key == idempotency_key:
            return refund
    return None


def has_completed_refund_for_payment_amount(
    state: SupportState,
    payment_id: str,
    amount: float,
) -> bool:
    return any(
        refund.payment_id == payment_id
        and refund.amount == amount
        and refund.status == RefundStatus.COMPLETED
        for refund in state.refunds.values()
    )
