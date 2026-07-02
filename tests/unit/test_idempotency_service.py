from app.services.idempotency_service import refund_idempotency_key


def test_refund_idempotency_key_is_stable() -> None:
    assert refund_idempotency_key("pay_dup_001", 120.0) == refund_idempotency_key(
        "pay_dup_001", 120.0
    )

