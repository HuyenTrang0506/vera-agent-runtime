"""Tool registry and execution contracts."""

from pydantic import BaseModel, Field


class ToolMetadata(BaseModel):
    name: str
    description: str
    preconditions: list[str] = Field(default_factory=list)
    transition_effects: list[str] = Field(default_factory=list)
    side_effects: list[str] = Field(default_factory=list)
    reversibility: str
    risk_level: str
    idempotency_required: bool = False
    approval_required_when: list[str] = Field(default_factory=list)
    failure_modes: list[str] = Field(default_factory=list)
    input_schema: dict = Field(default_factory=dict)

