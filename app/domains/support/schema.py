"""Support domain schema aliases."""

from app.models.state import (
    Customer,
    CustomerTier,
    Order,
    OrderStatus,
    Payment,
    PaymentStatus,
    Refund,
    RefundStatus,
    SupportFixture,
    SupportState,
    Ticket,
    TicketPriority,
    TicketStatus,
)

__all__ = [
    "Customer",
    "CustomerTier",
    "Order",
    "OrderStatus",
    "Payment",
    "PaymentStatus",
    "Refund",
    "RefundStatus",
    "SupportFixture",
    "SupportState",
    "Ticket",
    "TicketPriority",
    "TicketStatus",
]
