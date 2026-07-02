from app.domains.support.tools import create_refund
from app.services.idempotency_service import refund_idempotency_key
from app.services.state_service import load_support_fixture, runtime_state_from_fixture, snapshot_state
from app.services.transition_service import validate_refund_transition


def test_validate_refund_transition_matches_create_refund_state_delta() -> None:
    fixture = load_support_fixture("support_refund_happy_001")
    state = runtime_state_from_fixture(fixture)
    pre_state = snapshot_state(state)
    key = refund_idempotency_key("pay_dup_001", 120.0)

    create_refund(state, payment_id="pay_dup_001", amount=120.0, idempotency_key=key)
    result = validate_refund_transition(
        pre_state,
        state,
        payment_id="pay_dup_001",
        amount=120.0,
    )

    assert result.matches is True
    assert result.observed_transition_ids == ["T_REFUND_CREATE", "T_PAYMENT_REFUNDED_AMOUNT"]


def test_validate_refund_transition_detects_missing_state_delta() -> None:
    fixture = load_support_fixture("support_refund_happy_001")
    state = runtime_state_from_fixture(fixture)
    pre_state = snapshot_state(state)

    result = validate_refund_transition(
        pre_state,
        state,
        payment_id="pay_dup_001",
        amount=120.0,
    )

    assert result.matches is False
    assert result.observed_transition_ids == []
    assert "T_REFUND_CREATE" in result.reason
