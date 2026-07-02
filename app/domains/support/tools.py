"""Mock support tools.

Tools must stay deterministic and must not call Qwen or policy services.
"""

from pydantic import BaseModel

from app.models.state import (
    Customer,
    Order,
    Payment,
    PaymentStatus,
    Refund,
    RefundStatus,
    SupportState,
    Ticket,
    TicketStatus,
)
from app.services.idempotency_service import (
    find_refund_by_idempotency_key,
    has_completed_refund_for_payment_amount,
)


class CreateRefundResult(BaseModel):
    success: bool
    refund: Refund | None = None
    error: str | None = None
    idempotent_replay: bool = False


class TicketUpdateResult(BaseModel):
    success: bool
    ticket: Ticket | None = None
    error: str | None = None


def lookup_customer_by_email(state: SupportState, email: str) -> Customer | None:
    normalized_email = email.casefold()
    for customer in state.customers.values():
        if customer.email.casefold() == normalized_email:
            return customer
    return None


def lookup_order(state: SupportState, order_id: str) -> Order | None:
    return state.orders.get(order_id)


def list_order_payments(state: SupportState, order_id: str) -> list[Payment]:
    return [payment for payment in state.payments.values() if payment.order_id == order_id]


def inspect_payment(state: SupportState, payment_id: str) -> Payment | None:
    return state.payments.get(payment_id)


def lookup_ticket(state: SupportState, ticket_id: str) -> Ticket | None:
    return state.tickets.get(ticket_id)


def find_ticket_for_order(state: SupportState, order_id: str) -> Ticket | None:
    for ticket in state.tickets.values():
        if ticket.order_id == order_id:
            return ticket
    return None


def find_duplicate_payment_for_order(state: SupportState, order_id: str) -> Payment | None:
    for payment in list_order_payments(state, order_id):
        if payment.status == PaymentStatus.CAPTURED and payment.duplicate_of is not None:
            return payment
    return None


def create_refund(
    state: SupportState,
    payment_id: str,
    amount: float,
    idempotency_key: str,
    approval_id: str | None = None,
    failure_mode: str = "success",
) -> CreateRefundResult:
    if not idempotency_key:
        raise ValueError("create_refund requires an idempotency_key")

    existing_refund = find_refund_by_idempotency_key(state, idempotency_key)
    if existing_refund is not None:
        return CreateRefundResult(
            success=True,
            refund=existing_refund,
            idempotent_replay=True,
        )

    payment = inspect_payment(state, payment_id)
    if payment is None:
        return CreateRefundResult(success=False, error="payment_not_found")

    if has_completed_refund_for_payment_amount(state, payment_id, amount):
        return CreateRefundResult(success=False, error="refund_already_exists")

    refund = Refund(
        refund_id=f"ref_{idempotency_key[:12]}",
        payment_id=payment_id,
        status=RefundStatus.COMPLETED,
        amount=amount,
        idempotency_key=idempotency_key,
        approval_id=approval_id,
    )
    state.refunds[refund.refund_id] = refund
    payment.refunded_amount += amount
    payment.status = (
        PaymentStatus.REFUNDED
        if payment.refunded_amount >= payment.amount
        else PaymentStatus.PARTIALLY_REFUNDED
    )

    if failure_mode == "timeout_after_commit":
        return CreateRefundResult(
            success=False,
            refund=refund,
            error="timeout_after_commit",
        )

    return CreateRefundResult(success=True, refund=refund)


def resolve_ticket_with_completed_refund(
    state: SupportState,
    ticket_id: str,
    refund_id: str,
) -> TicketUpdateResult:
    ticket = lookup_ticket(state, ticket_id)
    if ticket is None:
        return TicketUpdateResult(success=False, error="ticket_not_found")

    refund = state.refunds.get(refund_id)
    if refund is None or refund.status != RefundStatus.COMPLETED:
        return TicketUpdateResult(success=False, error="completed_refund_not_found")

    order_id = ticket.order_id or state.payments[refund.payment_id].order_id
    ticket.status = TicketStatus.RESOLVED
    ticket.response_draft = (
        f"We completed the duplicate charge refund of {refund.amount:.2f} USD "
        f"for order {order_id}."
    )
    return TicketUpdateResult(success=True, ticket=ticket)
