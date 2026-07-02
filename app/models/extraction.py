"""Qwen structured extraction contract."""

from enum import StrEnum

from pydantic import BaseModel, Field


class ExtractionDomain(StrEnum):
    CUSTOMER_SUPPORT = "customer_support"


class SupportIntent(StrEnum):
    REQUEST_REFUND_FOR_DUPLICATE_CHARGE = "request_refund_for_duplicate_charge"
    ASK_ORDER_OR_PAYMENT_STATUS = "ask_order_or_payment_status"
    UNKNOWN_OR_UNSUPPORTED = "unknown_or_unsupported"


class TransitionId(StrEnum):
    REFUND_CREATE = "T_REFUND_CREATE"
    PAYMENT_REFUNDED_AMOUNT = "T_PAYMENT_REFUNDED_AMOUNT"
    TICKET_RESOLVE = "T_TICKET_RESOLVE"
    APPROVAL_PENDING = "T_APPROVAL_PENDING"
    APPROVAL_REJECTED = "T_APPROVAL_REJECTED"
    MANUAL_REVIEW = "T_MANUAL_REVIEW"
    STATE_MISMATCH = "T_STATE_MISMATCH"


class ExtractedEntities(BaseModel):
    customer_email: str | None = None
    order_id: str | None = None
    payment_id: str | None = None
    amount: float | None = None


class DesiredTransition(BaseModel):
    transition_id: TransitionId
    from_state: str
    to_state: str


class ExtractionResult(BaseModel):
    domain: ExtractionDomain
    intent: SupportIntent
    entities: ExtractedEntities
    desired_transition: DesiredTransition
    risk_flags: list[str] = Field(default_factory=list)
    missing_information: list[str] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0)
