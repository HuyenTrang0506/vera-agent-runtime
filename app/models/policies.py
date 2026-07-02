"""Policy decision contracts."""

from pydantic import BaseModel

from app.models.enums import PolicyDecision


class PolicyResult(BaseModel):
    decision: PolicyDecision
    rule_ids: list[str]
    reason: str
