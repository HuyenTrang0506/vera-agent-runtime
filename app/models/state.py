"""Support-domain state models for P0."""

from pydantic import BaseModel, Field


class Customer(BaseModel):
    customer_id: str
    email: str
    tier: str
    risk_flags: list[str] = Field(default_factory=list)


class Order(BaseModel):
    order_id: str
    customer_id: str
    status: str
    total_amount: float
    currency: str = "USD"


class Payment(BaseModel):
    payment_id: str
    order_id: str
    status: str
    amount: float
    duplicate_of: str | None = None
    refunded_amount: float = 0.0


class Refund(BaseModel):
    refund_id: str
    payment_id: str
    status: str
    amount: float
    idempotency_key: str
    approval_id: str | None = None


class Ticket(BaseModel):
    ticket_id: str
    customer_id: str
    order_id: str | None = None
    status: str
    priority: str
    summary: str


class SupportState(BaseModel):
    customers: dict[str, Customer]
    orders: dict[str, Order]
    payments: dict[str, Payment]
    refunds: dict[str, Refund] = Field(default_factory=dict)
    tickets: dict[str, Ticket] = Field(default_factory=dict)

