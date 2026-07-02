from app.domains.support.policies import (
    P_HIGH_VALUE_APPROVAL,
    P_NO_ALREADY_REFUNDED,
    P_REFUND_DUPLICATE_ONLY,
)
from app.domains.support.tools import create_refund
from app.models.enums import PolicyDecision
from app.services.idempotency_service import refund_idempotency_key
from app.services.policy_service import evaluate_refund_policy
from app.services.state_service import load_support_fixture, runtime_state_from_fixture


def test_refund_policy_allows_happy_duplicate_payment() -> None:
    fixture = load_support_fixture("support_refund_happy_001")
    state = runtime_state_from_fixture(fixture)

    result = evaluate_refund_policy(state, payment_id="pay_dup_001", amount=120.0)

    assert result.decision == "allow"
    assert result.rule_ids == [P_REFUND_DUPLICATE_ONLY, P_NO_ALREADY_REFUNDED]


def test_refund_policy_denies_non_duplicate_payment() -> None:
    fixture = load_support_fixture("support_refund_happy_001")
    state = runtime_state_from_fixture(fixture)

    result = evaluate_refund_policy(state, payment_id="pay_original_001", amount=120.0)

    assert result.decision == "deny"
    assert result.rule_ids == [P_REFUND_DUPLICATE_ONLY]


def test_refund_policy_denies_already_refunded_payment() -> None:
    fixture = load_support_fixture("support_refund_happy_001")
    state = runtime_state_from_fixture(fixture)
    key = refund_idempotency_key("pay_dup_001", 120.0)
    create_refund(state, payment_id="pay_dup_001", amount=120.0, idempotency_key=key)

    result = evaluate_refund_policy(state, payment_id="pay_dup_001", amount=120.0)

    assert result.decision == "deny"
    assert result.rule_ids == [P_NO_ALREADY_REFUNDED]


def test_refund_policy_requires_approval_for_high_value() -> None:
    fixture = load_support_fixture("support_refund_high_value_reject_001")
    state = runtime_state_from_fixture(fixture)

    result = evaluate_refund_policy(state, payment_id="pay_hv_dup_001", amount=750.0)

    assert result.decision == PolicyDecision.APPROVAL_REQUIRED
    assert P_HIGH_VALUE_APPROVAL in result.rule_ids


def test_refund_policy_allows_below_threshold() -> None:
    fixture = load_support_fixture("support_refund_happy_001")
    state = runtime_state_from_fixture(fixture)

    result = evaluate_refund_policy(
        state, payment_id="pay_dup_001", amount=120.0, threshold=500.0
    )

    assert result.decision == PolicyDecision.ALLOW
