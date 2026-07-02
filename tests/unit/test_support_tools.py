import pytest

from app.domains.support.tools import (
    create_refund,
    find_duplicate_payment_for_order,
    find_ticket_for_order,
    inspect_payment,
    list_order_payments,
    lookup_customer_by_email,
    lookup_order,
    lookup_ticket,
    resolve_ticket_with_completed_refund,
)
from app.services.idempotency_service import refund_idempotency_key
from app.services.state_service import load_support_fixture, runtime_state_from_fixture


def test_lookup_tools_resolve_happy_fixture_entities() -> None:
    fixture = load_support_fixture("support_refund_happy_001")
    state = runtime_state_from_fixture(fixture)

    customer = lookup_customer_by_email(state, "CUSTOMER@example.com")
    order = lookup_order(state, "ord_A102")
    payments = list_order_payments(state, "ord_A102")
    duplicate_payment = find_duplicate_payment_for_order(state, "ord_A102")
    ticket = find_ticket_for_order(state, "ord_A102")

    assert customer is not None
    assert customer.customer_id == "cus_001"
    assert order is not None
    assert order.customer_id == "cus_001"
    assert {payment.payment_id for payment in payments} == {"pay_original_001", "pay_dup_001"}
    assert duplicate_payment is not None
    assert duplicate_payment.payment_id == "pay_dup_001"
    assert ticket is not None
    assert ticket.ticket_id == "tkt_001"


def test_lookup_tools_return_none_for_missing_entities() -> None:
    fixture = load_support_fixture("support_refund_happy_001")
    state = runtime_state_from_fixture(fixture)

    assert lookup_customer_by_email(state, "missing@example.com") is None
    assert lookup_order(state, "ord_missing") is None
    assert inspect_payment(state, "pay_missing") is None
    assert lookup_ticket(state, "tkt_missing") is None
    assert find_duplicate_payment_for_order(state, "ord_missing") is None


def test_create_refund_requires_idempotency_key() -> None:
    fixture = load_support_fixture("support_refund_happy_001")
    state = runtime_state_from_fixture(fixture)

    with pytest.raises(ValueError, match="idempotency_key"):
        create_refund(state, payment_id="pay_dup_001", amount=120.0, idempotency_key="")


def test_create_refund_success_creates_one_completed_refund() -> None:
    fixture = load_support_fixture("support_refund_happy_001")
    state = runtime_state_from_fixture(fixture)
    key = refund_idempotency_key("pay_dup_001", 120.0)

    result = create_refund(
        state,
        payment_id="pay_dup_001",
        amount=120.0,
        idempotency_key=key,
    )

    assert result.success is True
    assert result.refund is not None
    assert result.refund.status == "completed"
    assert state.payments["pay_dup_001"].status == "refunded"
    assert state.payments["pay_dup_001"].refunded_amount == 120.0
    assert len(state.refunds) == 1


def test_create_refund_replay_same_key_does_not_duplicate_refund() -> None:
    fixture = load_support_fixture("support_refund_happy_001")
    state = runtime_state_from_fixture(fixture)
    key = refund_idempotency_key("pay_dup_001", 120.0)

    first = create_refund(state, "pay_dup_001", 120.0, key)
    second = create_refund(state, "pay_dup_001", 120.0, key)

    assert first.success is True
    assert second.success is True
    assert second.idempotent_replay is True
    assert first.refund == second.refund
    assert len(state.refunds) == 1


def test_create_refund_timeout_after_commit_commits_once_then_reports_timeout() -> None:
    fixture = load_support_fixture("support_refund_timeout_after_commit_001")
    state = runtime_state_from_fixture(fixture)
    key = refund_idempotency_key("pay_timeout_dup_001", 120.0)

    result = create_refund(
        state,
        payment_id="pay_timeout_dup_001",
        amount=120.0,
        idempotency_key=key,
        failure_mode="timeout_after_commit",
    )
    replay = create_refund(
        state,
        payment_id="pay_timeout_dup_001",
        amount=120.0,
        idempotency_key=key,
    )

    assert result.success is False
    assert result.error == "timeout_after_commit"
    assert result.refund is not None
    assert result.refund.status == "completed"
    assert replay.success is True
    assert replay.idempotent_replay is True
    assert len(state.refunds) == 1
    assert state.payments["pay_timeout_dup_001"].refunded_amount == 120.0


def test_resolve_ticket_with_completed_refund_drafts_safe_response() -> None:
    fixture = load_support_fixture("support_refund_happy_001")
    state = runtime_state_from_fixture(fixture)
    key = refund_idempotency_key("pay_dup_001", 120.0)
    refund = create_refund(state, "pay_dup_001", 120.0, key).refund
    assert refund is not None

    result = resolve_ticket_with_completed_refund(state, "tkt_001", refund.refund_id)

    assert result.success is True
    assert result.ticket is not None
    assert result.ticket.status == "resolved"
    assert result.ticket.response_draft is not None
    assert "completed" in result.ticket.response_draft
    assert "120.00 USD" in result.ticket.response_draft


def test_resolve_ticket_does_not_promise_missing_refund() -> None:
    fixture = load_support_fixture("support_refund_happy_001")
    state = runtime_state_from_fixture(fixture)

    result = resolve_ticket_with_completed_refund(state, "tkt_001", "ref_missing")

    assert result.success is False
    assert result.error == "completed_refund_not_found"
    assert state.tickets["tkt_001"].status == "new"
    assert state.tickets["tkt_001"].response_draft is None
