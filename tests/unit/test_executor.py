"""Tests for generic ToolExecutor."""

from app.core.executor import ToolExecutor
from app.core.registry import load_tool_registry
from app.models.enums import PolicyDecision
from app.services.state_service import load_support_fixture, runtime_state_from_fixture

from pathlib import Path

SUPPORT_YAML = Path("app/registries/support_tools.yaml")


def _make_executor(observe_fn=None):
    registry = load_tool_registry(SUPPORT_YAML)

    from app.domains.support.tools import create_refund
    from app.services.transition_service import observe_refund_transitions

    if observe_fn is None:
        observe_fn = lambda pre, post, ctx: observe_refund_transitions(
            pre, post, ctx["payment_id"], ctx["amount"]
        )

    return ToolExecutor(
        metadata=registry["create_refund"],
        tool_fn=create_refund,
        observe_fn=observe_fn,
    )


def _happy_state():
    fixture = load_support_fixture("support_refund_happy_001")
    return runtime_state_from_fixture(fixture)


def test_executor_success_returns_committed_and_observed_transitions() -> None:
    state = _happy_state()
    executor = _make_executor()

    result = executor.run(
        workflow_id="wf_test_001",
        state=state,
        params={
            "payment_id": "pay_dup_001",
            "amount": 120.0,
            "idempotency_key": "refund:pay_dup_001:120.00",
            "approval_id": None,
        },
        failure_mode="success",
        policy_decision=PolicyDecision.ALLOW,
    )

    assert result.success is True
    assert result.committed is True
    assert result.recovered_timeout is False
    assert "T_REFUND_CREATE" in result.observed_transitions
    assert "T_PAYMENT_REFUNDED_AMOUNT" in result.observed_transitions
    assert result.receipt is not None
    assert result.receipt.outcome == "success"


def test_executor_timeout_after_commit_recovers() -> None:
    from app.domains.support.tools import find_duplicate_payment_for_order
    from app.services.idempotency_service import refund_idempotency_key

    fixture = load_support_fixture("support_refund_timeout_after_commit_001")
    state = runtime_state_from_fixture(fixture)
    executor = _make_executor()

    dup_payment = find_duplicate_payment_for_order(state, list(state.orders.keys())[0])
    assert dup_payment is not None

    ikey = refund_idempotency_key(dup_payment.payment_id, dup_payment.amount)
    result = executor.run(
        workflow_id="wf_test_002",
        state=state,
        params={
            "payment_id": dup_payment.payment_id,
            "amount": dup_payment.amount,
            "idempotency_key": ikey,
            "approval_id": None,
        },
        failure_mode="timeout_after_commit",
        policy_decision=PolicyDecision.ALLOW,
    )

    assert result.committed is True
    assert result.recovered_timeout is True
    assert result.receipt is not None
    assert result.receipt.outcome == "recovered"


def test_executor_hard_failure_not_committed() -> None:
    from app.domains.support.tools import CreateRefundResult
    from app.core.registry import load_tool_registry
    from app.services.transition_service import observe_refund_transitions

    registry = load_tool_registry(SUPPORT_YAML)

    def failing_tool(state, *, payment_id, amount, idempotency_key, approval_id, failure_mode):
        return CreateRefundResult(success=False, error="network_error")

    executor = ToolExecutor(
        metadata=registry["create_refund"],
        tool_fn=failing_tool,
        observe_fn=lambda pre, post, ctx: observe_refund_transitions(
            pre, post, ctx["payment_id"], ctx["amount"]
        ),
    )
    state = _happy_state()

    result = executor.run(
        workflow_id="wf_test_003",
        state=state,
        params={
            "payment_id": "pay_dup_001",
            "amount": 120.0,
            "idempotency_key": "refund:pay_dup_001:120.00",
            "approval_id": None,
        },
        failure_mode="success",
        policy_decision=PolicyDecision.ALLOW,
    )

    assert result.success is False
    assert result.committed is False
    assert result.receipt is not None
    assert result.receipt.outcome == "failed"


def test_executor_mismatch_escalates_when_observe_returns_empty() -> None:
    state = _happy_state()
    # observe_fn that always returns empty — simulates mismatch
    executor = _make_executor(observe_fn=lambda pre, post, ctx: [])

    result = executor.run(
        workflow_id="wf_test_004",
        state=state,
        params={
            "payment_id": "pay_dup_001",
            "amount": 120.0,
            "idempotency_key": "refund:pay_dup_001:120.00",
            "approval_id": None,
        },
        failure_mode="success_but_state_mismatch",
        policy_decision=PolicyDecision.ALLOW,
    )

    assert result.receipt is not None
    assert result.receipt.outcome == "escalated"


def test_executor_receipt_has_correct_hashes() -> None:
    state = _happy_state()
    executor = _make_executor()

    result = executor.run(
        workflow_id="wf_test_005",
        state=state,
        params={
            "payment_id": "pay_dup_001",
            "amount": 120.0,
            "idempotency_key": "refund:pay_dup_001:120.00",
            "approval_id": None,
        },
        failure_mode="success",
        policy_decision=PolicyDecision.ALLOW,
    )

    assert result.pre_state_hash != result.post_state_hash
    assert result.receipt.pre_state_hash == result.pre_state_hash
    assert result.receipt.post_state_hash == result.post_state_hash
