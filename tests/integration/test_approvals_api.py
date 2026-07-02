from fastapi.testclient import TestClient

from app.main import create_app
from app.services.action_controller import run_support_workflow
from app.services.approval_service import clear_approvals, get_approval


def test_reject_endpoint_records_manager_decision_for_pending_approval() -> None:
    clear_approvals()
    workflow_result = run_support_workflow(fixture_id="support_refund_high_value_reject_001")
    assert workflow_result.approval_id is not None

    client = TestClient(create_app())
    response = client.post(
        f"/approvals/{workflow_result.approval_id}/reject",
        json={"decided_by": "manager_demo", "comment": "Duplicate charge needs review."},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["approval_id"] == workflow_result.approval_id
    assert body["status"] == "rejected"
    assert body["decided_by"] == "manager_demo"
    assert body["comment"] == "Duplicate charge needs review."

    stored = get_approval(workflow_result.approval_id)
    assert stored is not None
    assert stored.status == "rejected"
    assert stored.decided_by == "manager_demo"


def test_approval_decision_endpoint_returns_404_for_unknown_approval() -> None:
    clear_approvals()
    client = TestClient(create_app())

    response = client.post(
        "/approvals/apr_missing/reject",
        json={"decided_by": "manager_demo"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "approval_not_found"
