"""Finance-domain state models for the duplicate-invoice thin slice (P1/B19)."""

from enum import StrEnum

from pydantic import BaseModel, Field, model_validator


class VendorStatus(StrEnum):
    ACTIVE = "active"
    SUSPENDED = "suspended"
    UNDER_REVIEW = "under_review"


class InvoiceStatus(StrEnum):
    RECEIVED = "received"
    VALIDATED = "validated"
    APPROVED = "approved"
    PAID = "paid"
    DUPLICATE = "duplicate"
    REJECTED = "rejected"
    ON_HOLD = "on_hold"


class FinancePaymentStatus(StrEnum):
    PENDING = "pending"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    FAILED = "failed"


class Vendor(BaseModel):
    vendor_id: str
    name: str
    status: VendorStatus
    approved_bank_account: str


class Invoice(BaseModel):
    invoice_id: str
    vendor_id: str
    amount: float
    currency: str = "USD"
    status: InvoiceStatus
    reference_number: str
    duplicate_of: str | None = None
    idempotency_key: str | None = None


class FinancePayment(BaseModel):
    payment_id: str
    invoice_id: str
    vendor_id: str
    amount: float
    status: FinancePaymentStatus
    idempotency_key: str


class FinanceState(BaseModel):
    vendors: dict[str, Vendor]
    invoices: dict[str, Invoice]
    payments: dict[str, FinancePayment] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_references(self) -> "FinanceState":
        for vendor_id, vendor in self.vendors.items():
            if vendor.vendor_id != vendor_id:
                raise ValueError(f"vendor key {vendor_id} != vendor_id")

        for invoice_id, invoice in self.invoices.items():
            if invoice.invoice_id != invoice_id:
                raise ValueError(f"invoice key {invoice_id} != invoice_id")
            if invoice.vendor_id not in self.vendors:
                raise ValueError(f"invoice {invoice_id} references missing vendor {invoice.vendor_id}")
            if invoice.duplicate_of is not None and invoice.duplicate_of not in self.invoices:
                raise ValueError(f"invoice {invoice_id} duplicate_of {invoice.duplicate_of} not found")

        for payment_id, payment in self.payments.items():
            if payment.payment_id != payment_id:
                raise ValueError(f"payment key {payment_id} != payment_id")
            if payment.invoice_id not in self.invoices:
                raise ValueError(f"payment {payment_id} references missing invoice {payment.invoice_id}")

        return self


class FinanceFixture(BaseModel):
    fixture_id: str
    failure_mode: str = "success"
    state: FinanceState
    expected_invoice_id: str
    expected_duplicate_invoice_id: str | None = None
