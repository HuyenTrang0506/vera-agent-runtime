"""Approval lifecycle contracts."""

from pydantic import BaseModel


class ApprovalDecisionRequest(BaseModel):
    decided_by: str
    comment: str | None = None

