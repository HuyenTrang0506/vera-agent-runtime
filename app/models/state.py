"""Support-domain state models for P0."""

from enum import StrEnum

from pydantic import BaseModel, Field, model_validator

from app.models.extraction import ExtractionResult


class CustomerTier(StrEnum):
    STANDARD = "standard"
    PREMIUM = "premium"
    ENTERPRISE = "enterprise"


class OrderStatus(StrEnum):
    CREATED = "created"
    PAID = "paid"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"


class PaymentStatus(StrEnum):
    AUTHORIZED = "authorized"
    CAPTURED = "captured"
    REFUNDED = "refunded"
    PARTIALLY_REFUNDED = "partially_refunded"
    FAILED = "failed"


class RefundStatus(StrEnum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TicketStatus(StrEnum):
    NEW = "new"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    PENDING_CUSTOMER_FOLLOWUP = "pending_customer_followup"
    PENDING_MANUAL_REVIEW = "pending_manual_review"
    ESCALATED_STATE_MISMATCH = "escalated_state_mismatch"


class TicketPriority(StrEnum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class Customer(BaseModel):
    customer_id: str
    email: str
    tier: CustomerTier
    risk_flags: list[str] = Field(default_factory=list)


class Order(BaseModel):
    order_id: str
    customer_id: str
    status: OrderStatus
    total_amount: float
    currency: str = "USD"


class Payment(BaseModel):
    payment_id: str
    order_id: str
    status: PaymentStatus
    amount: float
    duplicate_of: str | None = None
    refunded_amount: float = 0.0


class Refund(BaseModel):
    refund_id: str
    payment_id: str
    status: RefundStatus
    amount: float
    idempotency_key: str
    approval_id: str | None = None


class Ticket(BaseModel):
    ticket_id: str
    customer_id: str
    order_id: str | None = None
    status: TicketStatus
    priority: TicketPriority
    summary: str
    response_draft: str | None = None


class SupportState(BaseModel):
    customers: dict[str, Customer]
    orders: dict[str, Order]
    payments: dict[str, Payment]
    refunds: dict[str, Refund] = Field(default_factory=dict)
    tickets: dict[str, Ticket] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_references(self) -> "SupportState":
        for customer_id, customer in self.customers.items():
            if customer.customer_id != customer_id:
                raise ValueError(f"customer key {customer_id} does not match customer_id")

        for order_id, order in self.orders.items():
            if order.order_id != order_id:
                raise ValueError(f"order key {order_id} does not match order_id")
            if order.customer_id not in self.customers:
                raise ValueError(f"order {order_id} references missing customer {order.customer_id}")

        for payment_id, payment in self.payments.items():
            if payment.payment_id != payment_id:
                raise ValueError(f"payment key {payment_id} does not match payment_id")
            if payment.order_id not in self.orders:
                raise ValueError(f"payment {payment_id} references missing order {payment.order_id}")
            if payment.duplicate_of is not None and payment.duplicate_of not in self.payments:
                raise ValueError(
                    f"payment {payment_id} references missing duplicate_of {payment.duplicate_of}"
                )

        for refund_id, refund in self.refunds.items():
            if refund.refund_id != refund_id:
                raise ValueError(f"refund key {refund_id} does not match refund_id")
            if refund.payment_id not in self.payments:
                raise ValueError(f"refund {refund_id} references missing payment {refund.payment_id}")

        for ticket_id, ticket in self.tickets.items():
            if ticket.ticket_id != ticket_id:
                raise ValueError(f"ticket key {ticket_id} does not match ticket_id")
            if ticket.customer_id not in self.customers:
                raise ValueError(f"ticket {ticket_id} references missing customer {ticket.customer_id}")
            if ticket.order_id is not None and ticket.order_id not in self.orders:
                raise ValueError(f"ticket {ticket_id} references missing order {ticket.order_id}")

        return self


class SupportFixture(BaseModel):
    fixture_id: str
    failure_mode: str = "success"
    state: SupportState
    expected_extraction: ExtractionResult
