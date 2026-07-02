from fastapi.testclient import TestClient

from app.main import create_app
from app.services.state_service import workflow_result_path


def test_workflow_run_persists_result_and_audit_route_returns_receipts() -> None:
    client = TestClient(create_app())
    response = client.post(
        "/workflows/run",
        json={
            "domain": "customer_support",
            "request_text": "I was charged twice for order ord_A102.",
            "fixture_id": "support_refund_happy_001",
        },
    )
    assert response.status_code == 200
    body = response.json()
    workflow_id = body["workflow_id"]

    try:
        path = workflow_result_path(workflow_id)
        assert path.exists()

        workflow_response = client.get(f"/workflows/{workflow_id}")
        assert workflow_response.status_code == 200
        workflow_body = workflow_response.json()
        assert workflow_body["workflow_id"] == workflow_id
        assert workflow_body["status"] == "completed"
        assert len(workflow_body["timeline_events"]) == len(workflow_body["audit_receipts"])

        audit_response = client.get(f"/audit/{workflow_id}")
        assert audit_response.status_code == 200
        audit_body = audit_response.json()
        assert len(audit_body) == 2
        assert audit_body[0]["workflow_id"] == workflow_id
        assert audit_body[0]["pre_state_hash"]
        assert audit_body[0]["post_state_hash"]
    finally:
        workflow_result_path(workflow_id).unlink(missing_ok=True)


def test_audit_route_returns_404_for_unknown_workflow() -> None:
    client = TestClient(create_app())

    response = client.get("/audit/wf_missing")

    assert response.status_code == 404
    assert response.json()["detail"] == "workflow_not_found"
