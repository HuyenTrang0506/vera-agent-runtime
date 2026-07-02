"""Approval API routes."""

from fastapi import APIRouter

from app.models.approvals import ApprovalDecisionRequest

router = APIRouter(prefix="/approvals", tags=["approvals"])


@router.post("/{approval_id}/approve")
def approve(approval_id: str, request: ApprovalDecisionRequest) -> dict[str, str]:
    return {"approval_id": approval_id, "status": "approved", "decided_by": request.decided_by}


@router.post("/{approval_id}/reject")
def reject(approval_id: str, request: ApprovalDecisionRequest) -> dict[str, str]:
    return {"approval_id": approval_id, "status": "rejected", "decided_by": request.decided_by}

