import pytest
from pydantic import ValidationError

from app.models.state import SupportState, TicketStatus
from app.models.workflow import WorkflowRunResult
from app.services.state_service import (
    load_workflow_result,
    load_support_fixture,
    runtime_state_from_fixture,
    save_workflow_result,
    snapshot_state,
    state_hash,
)


def test_state_hash_is_order_invariant() -> None:
    assert state_hash({"b": 2, "a": 1}) == state_hash({"a": 1, "b": 2})


def test_support_fixture_loads_into_typed_state() -> None:
    fixture = load_support_fixture("support_refund_happy_001")

    assert fixture.fixture_id == "support_refund_happy_001"
    assert fixture.state.payments["pay_dup_001"].duplicate_of == "pay_original_001"
    assert fixture.expected_extraction.desired_transition.transition_id == "T_REFUND_CREATE"


def test_runtime_state_from_fixture_is_deep_copy() -> None:
    fixture = load_support_fixture("support_refund_happy_001")
    runtime_state = runtime_state_from_fixture(fixture)

    runtime_state.tickets["tkt_001"].status = TicketStatus.RESOLVED

    assert fixture.state.tickets["tkt_001"].status == "new"
    assert runtime_state.tickets["tkt_001"].status == "resolved"


def test_snapshot_and_hash_accept_typed_state() -> None:
    fixture = load_support_fixture("support_refund_happy_001")

    snapshot = snapshot_state(fixture.state)

    assert snapshot["payments"]["pay_dup_001"]["status"] == "captured"
    assert state_hash(fixture.state) == state_hash(snapshot)


def test_support_state_rejects_missing_references() -> None:
    with pytest.raises(ValidationError):
        SupportState.model_validate(
            {
                "customers": {},
                "orders": {},
                "payments": {
                    "pay_missing_order": {
                        "payment_id": "pay_missing_order",
                        "order_id": "ord_missing",
                        "status": "captured",
                        "amount": 120.0,
                    }
                },
            }
        )


def test_save_and_load_workflow_result_snapshot() -> None:
    result = WorkflowRunResult(
        workflow_id="wf_test_snapshot",
        status="completed",
        desired_transition_id="T_REFUND_CREATE",
        policy_decision="allow",
        final_state_match=True,
        audit_receipt_ids=[],
    )

    path = save_workflow_result(result)
    loaded = load_workflow_result("wf_test_snapshot")

    assert path.exists()
    assert loaded == result
    path.unlink()
    assert load_workflow_result("wf_test_snapshot") is None
