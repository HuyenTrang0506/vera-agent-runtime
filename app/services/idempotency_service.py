"""Idempotency helpers for consequential actions."""

from hashlib import sha256


def refund_idempotency_key(payment_id: str, amount: float) -> str:
    raw = f"refund:{payment_id}:{amount:.2f}"
    return sha256(raw.encode("utf-8")).hexdigest()[:24]

