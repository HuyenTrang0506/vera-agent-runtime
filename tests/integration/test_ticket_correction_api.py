"""Integration tests for POST /workflows/{workflow_id}/correct-ticket."""

import pytest
from fastapi.testclient import TestClient

from app.main import create_app


@pytest.fixture()
def client() -> TestClient:
    return TestClient(create_app())


def _run_mismatch_workflow(client: TestClient) -> dict:
    resp = client.post("/workflows/run", json={
        "domain": "customer_support",
        "request_text": "I was charged twice for order A102. Refund me.",
        "fixture_id": "support_tool_mismatch_001",
        "operator_id": "op_test",
    })
    assert resp.status_code == 200
    return resp.json()


def test_correct_ticket_on_mismatch_workflow(client: TestClient) -> None:
    result = _run_mismatch_workflow(client)
    assert result["status"] == "escalated_state_mismatch"
    workflow_id = result["workflow_id"]

    # Find ticket_id from final state
    final_state = result["final_state"]
    ticket_id = next(iter(final_state["tickets"].keys()))

    resp = client.post(f"/workflows/{workflow_id}/correct-ticket", json={
        "ticket_id": ticket_id,
        "new_status": "pending_manual_review",
        "operator_note": "Operator confirmed no action needed; routing to manual review.",
        "operator_id": "op_test",
    })
    assert resp.status_code == 200
    updated = resp.json()
    assert updated["final_state"]["tickets"][ticket_id]["status"] == "pending_manual_review"


def test_correct_ticket_unknown_workflow_returns_404(client: TestClient) -> None:
    resp = client.post("/workflows/wf_does_not_exist/correct-ticket", json={
        "ticket_id": "tkt_001",
        "new_status": "resolved",
        "operator_note": "test",
    })
    assert resp.status_code == 404


def test_correct_ticket_on_completed_workflow_returns_409(client: TestClient) -> None:
    run_resp = client.post("/workflows/run", json={
        "domain": "customer_support",
        "request_text": "I was charged twice for order A102. Refund me.",
        "fixture_id": "support_refund_happy_001",
        "operator_id": "op_test",
    })
    assert run_resp.status_code == 200
    workflow_id = run_resp.json()["workflow_id"]
    assert run_resp.json()["status"] == "completed"

    resp = client.post(f"/workflows/{workflow_id}/correct-ticket", json={
        "ticket_id": "tkt_001",
        "new_status": "pending_manual_review",
        "operator_note": "test",
    })
    assert resp.status_code == 409


def test_correct_ticket_invalid_target_status_returns_422(client: TestClient) -> None:
    result = _run_mismatch_workflow(client)
    workflow_id = result["workflow_id"]
    final_state = result["final_state"]
    ticket_id = next(iter(final_state["tickets"].keys()))

    # "new" is not an allowed correction target (can only correct forward to
    # resolved, pending_manual_review, or pending_customer_followup)
    resp = client.post(f"/workflows/{workflow_id}/correct-ticket", json={
        "ticket_id": ticket_id,
        "new_status": "new",
        "operator_note": "Setting ticket back to new is not allowed.",
    })
    assert resp.status_code == 422


def test_correct_ticket_to_resolved_on_mismatch(client: TestClient) -> None:
    result = _run_mismatch_workflow(client)
    workflow_id = result["workflow_id"]
    final_state = result["final_state"]
    ticket_id = next(iter(final_state["tickets"].keys()))

    resp = client.post(f"/workflows/{workflow_id}/correct-ticket", json={
        "ticket_id": ticket_id,
        "new_status": "resolved",
        "operator_note": "Operator manually verified no bad state; closing.",
    })
    assert resp.status_code == 200
    assert resp.json()["final_state"]["tickets"][ticket_id]["status"] == "resolved"
