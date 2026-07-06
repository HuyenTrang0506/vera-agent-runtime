"""Mock finance tools for the duplicate-invoice thin slice.

Tools are deterministic Python functions. They must not call Qwen or policy services.
"""

from pydantic import BaseModel

from app.models.finance import (
    FinancePayment,
    FinancePaymentStatus,
    FinanceState,
    Invoice,
    InvoiceStatus,
    Vendor,
)
from app.core.ids import new_id


class InvoicePaymentResult(BaseModel):
    success: bool
    payment: FinancePayment | None = None
    error: str | None = None
    idempotent_replay: bool = False


class InvoiceUpdateResult(BaseModel):
    success: bool
    invoice: Invoice | None = None
    error: str | None = None


def lookup_vendor(state: FinanceState, vendor_id: str) -> Vendor | None:
    return state.vendors.get(vendor_id)


def lookup_invoice(state: FinanceState, invoice_id: str) -> Invoice | None:
    return state.invoices.get(invoice_id)


def list_vendor_invoices(state: FinanceState, vendor_id: str) -> list[Invoice]:
    return [inv for inv in state.invoices.values() if inv.vendor_id == vendor_id]


def find_duplicate_invoice(state: FinanceState, invoice_id: str) -> Invoice | None:
    """Return the existing invoice that this invoice duplicates, if any."""
    invoice = state.invoices.get(invoice_id)
    if invoice is None:
        return None
    if invoice.duplicate_of is not None:
        return state.invoices.get(invoice.duplicate_of)
    return None


def find_completed_payment_for_invoice(
    state: FinanceState, invoice_id: str
) -> FinancePayment | None:
    for payment in state.payments.values():
        if payment.invoice_id == invoice_id and payment.status == FinancePaymentStatus.COMPLETED:
            return payment
    return None


def pay_invoice(
    state: FinanceState,
    invoice_id: str,
    idempotency_key: str,
    failure_mode: str = "success",
) -> InvoicePaymentResult:
    if not idempotency_key:
        raise ValueError("pay_invoice requires an idempotency_key")

    # Idempotency: replay if key already used
    for payment in state.payments.values():
        if payment.idempotency_key == idempotency_key:
            return InvoicePaymentResult(
                success=True,
                payment=payment,
                idempotent_replay=True,
            )

    invoice = state.invoices.get(invoice_id)
    if invoice is None:
        return InvoicePaymentResult(success=False, error="invoice_not_found")
    if invoice.status == InvoiceStatus.PAID:
        return InvoicePaymentResult(success=False, error="invoice_already_paid")
    if invoice.status in (InvoiceStatus.DUPLICATE, InvoiceStatus.REJECTED):
        return InvoicePaymentResult(success=False, error=f"invoice_not_payable:{invoice.status}")

    vendor = state.vendors.get(invoice.vendor_id)
    if vendor is None:
        return InvoicePaymentResult(success=False, error="vendor_not_found")

    payment = FinancePayment(
        payment_id=new_id("fpay_"),
        invoice_id=invoice_id,
        vendor_id=invoice.vendor_id,
        amount=invoice.amount,
        status=FinancePaymentStatus.COMPLETED,
        idempotency_key=idempotency_key,
    )

    state.payments[payment.payment_id] = payment
    invoice.status = InvoiceStatus.PAID
    invoice.idempotency_key = idempotency_key

    if failure_mode == "timeout_after_commit":
        return InvoicePaymentResult(
            success=False,
            payment=payment,
            error="timeout_after_commit",
        )

    return InvoicePaymentResult(success=True, payment=payment)


def mark_invoice_duplicate(
    state: FinanceState,
    invoice_id: str,
    original_invoice_id: str,
) -> InvoiceUpdateResult:
    invoice = state.invoices.get(invoice_id)
    if invoice is None:
        return InvoiceUpdateResult(success=False, error="invoice_not_found")
    invoice.status = InvoiceStatus.DUPLICATE
    invoice.duplicate_of = original_invoice_id
    return InvoiceUpdateResult(success=True, invoice=invoice)


def hold_invoice(state: FinanceState, invoice_id: str, reason: str) -> InvoiceUpdateResult:
    invoice = state.invoices.get(invoice_id)
    if invoice is None:
        return InvoiceUpdateResult(success=False, error="invoice_not_found")
    if invoice.status in (InvoiceStatus.PAID, InvoiceStatus.DUPLICATE):
        return InvoiceUpdateResult(
            success=False, error=f"cannot_hold_invoice_in_status:{invoice.status}"
        )
    invoice.status = InvoiceStatus.ON_HOLD
    return InvoiceUpdateResult(success=True, invoice=invoice)


def observe_invoice_transitions(
    pre_state: dict, post_state: FinanceState, ctx: dict
) -> list[str]:
    invoice_id = ctx["invoice_id"]
    pre_payment_ids = set(pre_state.get("payments", {}).keys())
    observed = []
    for pid, p in post_state.payments.items():
        if (
            pid not in pre_payment_ids
            and p.invoice_id == invoice_id
            and p.status == FinancePaymentStatus.COMPLETED
        ):
            observed.append("T_INVOICE_PAY")
            break
    return observed
