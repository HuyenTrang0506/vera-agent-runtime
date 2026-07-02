"""Audit review API routes."""

from fastapi import APIRouter, HTTPException

from app.models.audit import AuditReceipt
from app.services.state_service import load_workflow_result

router = APIRouter(prefix="/audit", tags=["audit"])


@router.get("/{workflow_id}", response_model=list[AuditReceipt])
def get_workflow_audit(workflow_id: str) -> list[AuditReceipt]:
    result = load_workflow_result(workflow_id)
    if result is None:
        raise HTTPException(status_code=404, detail="workflow_not_found")
    return result.audit_receipts
