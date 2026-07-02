"""Mock support tools.

Tools must stay deterministic and must not call Qwen or policy services.
"""

from app.models.state import SupportState


def lookup_order(state: SupportState, order_id: str):
    return state.orders.get(order_id)


def inspect_payment(state: SupportState, payment_id: str):
    return state.payments.get(payment_id)

