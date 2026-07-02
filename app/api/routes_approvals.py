"""Approval API routes."""

from fastapi import APIRouter, HTTPException

from app.models.approvals import ApprovalDecisionRequest, ApprovalRecord
from app.models.enums import ApprovalStatus
from app.services.approval_service import get_approval, record_approval_decision

router = APIRouter(prefix="/approvals", tags=["approvals"])


def _get_existing_approval(approval_id: str) -> ApprovalRecord:
    approval = get_approval(approval_id)
    if approval is None:
        raise HTTPException(status_code=404, detail="approval_not_found")
    return approval


@router.get("/{approval_id}", response_model=ApprovalRecord)
def get_approval_route(approval_id: str) -> ApprovalRecord:
    return _get_existing_approval(approval_id)


@router.post("/{approval_id}/approve", response_model=ApprovalRecord)
def approve(approval_id: str, request: ApprovalDecisionRequest) -> ApprovalRecord:
    approval = _get_existing_approval(approval_id)
    return record_approval_decision(
        approval,
        decision=ApprovalStatus.APPROVED,
        decided_by=request.decided_by,
        comment=request.comment,
    )


@router.post("/{approval_id}/reject", response_model=ApprovalRecord)
def reject(approval_id: str, request: ApprovalDecisionRequest) -> ApprovalRecord:
    approval = _get_existing_approval(approval_id)
    return record_approval_decision(
        approval,
        decision=ApprovalStatus.REJECTED,
        decided_by=request.decided_by,
        comment=request.comment,
    )
