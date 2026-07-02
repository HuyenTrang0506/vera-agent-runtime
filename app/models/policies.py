"""Policy decision contracts."""

from pydantic import BaseModel


class PolicyResult(BaseModel):
    decision: str
    rule_ids: list[str]
    reason: str

