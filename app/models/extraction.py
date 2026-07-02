"""Qwen structured extraction contract."""

from pydantic import BaseModel, Field


class ExtractedEntities(BaseModel):
    customer_email: str | None = None
    order_id: str | None = None
    payment_id: str | None = None
    amount: float | None = None


class DesiredTransition(BaseModel):
    transition_id: str
    from_state: str
    to_state: str


class ExtractionResult(BaseModel):
    domain: str
    intent: str
    entities: ExtractedEntities
    desired_transition: DesiredTransition
    risk_flags: list[str] = Field(default_factory=list)
    missing_information: list[str] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0)

