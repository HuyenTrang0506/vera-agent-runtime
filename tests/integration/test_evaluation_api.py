"""Integration tests for POST /evaluation/run and GET /evaluation/{run_id}."""

import pytest
from fastapi.testclient import TestClient

from app.main import create_app

@pytest.fixture()
def client() -> TestClient:
    return TestClient(create_app())


def test_run_evaluation_returns_metrics(client: TestClient) -> None:
    response = client.post("/evaluation/run", json={"repeated_runs": 1})
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "completed"
    assert "run_id" in body
    assert "metrics" in body
    m = body["metrics"]
    assert "business_task_success_rate" in m
    assert "duplicate_refund_count" in m
    assert "audit_completeness_rate" in m
    assert body["repeated_runs"] == 1
    assert body["repeated_run_summary"]["total_runs"] >= 1
    assert len(body["tasks"]) >= 1


def test_get_evaluation_returns_stored_result(client: TestClient) -> None:
    run_resp = client.post("/evaluation/run", json={"repeated_runs": 1})
    run_id = run_resp.json()["run_id"]

    get_resp = client.get(f"/evaluation/{run_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["run_id"] == run_id


def test_get_evaluation_unknown_id_returns_404(client: TestClient) -> None:
    response = client.get("/evaluation/eval_does_not_exist")
    assert response.status_code == 404


def test_run_evaluation_no_body_uses_defaults(client: TestClient) -> None:
    response = client.post("/evaluation/run")
    assert response.status_code == 200
    assert response.json()["status"] == "completed"
