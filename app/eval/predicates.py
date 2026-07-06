"""Evaluate benchmark expected_final_predicates against a WorkflowRunResult.

Supported predicate forms:
  workflow.status == 'X'
  ticket.status == 'X'
  count_completed_refunds() == N
  count_completed_refunds(payment_id='pay_xxx') == N
  total_refunded_amount(payment_id='pay_xxx') == payment.amount
  create_refund.called == false
"""

from __future__ import annotations

import re
from typing import Any

from app.models.workflow import WorkflowRunResult


def _count_completed_refunds(final_state: dict[str, Any], payment_id: str | None) -> int:
    refunds: dict[str, Any] = final_state.get("refunds", {})
    return sum(
        1
        for r in refunds.values()
        if r.get("status") == "completed"
        and (payment_id is None or r.get("payment_id") == payment_id)
    )


def _total_refunded_amount(final_state: dict[str, Any], payment_id: str) -> float:
    refunds: dict[str, Any] = final_state.get("refunds", {})
    return sum(
        float(r.get("amount", 0))
        for r in refunds.values()
        if r.get("payment_id") == payment_id and r.get("status") == "completed"
    )


def _payment_amount(final_state: dict[str, Any], payment_id: str) -> float | None:
    payments: dict[str, Any] = final_state.get("payments", {})
    for p in payments.values():
        if p.get("payment_id") == payment_id:
            return float(p.get("amount", 0))
    return None


def _ticket_status(final_state: dict[str, Any]) -> str | None:
    tickets: dict[str, Any] = final_state.get("tickets", {})
    if not tickets:
        return None
    return next(iter(tickets.values())).get("status")


def _count_completed_finance_payments(final_state: dict[str, Any], invoice_id: str) -> int:
    payments: dict[str, Any] = final_state.get("payments", {})
    return sum(
        1
        for p in payments.values()
        if p.get("invoice_id") == invoice_id and p.get("status") == "completed"
    )


def _create_refund_was_called(result: WorkflowRunResult) -> bool:
    return any(
        "create_refund" in r.action_id
        for r in result.audit_receipts
        if r.outcome in ("success", "recovered")
    )


_PAY_ID_RE = re.compile(r"payment_id='([^']+)'")
_INV_ID_RE = re.compile(r"invoice_id='([^']+)'")
_STATUS_RE = re.compile(r"^([a-z_.]+\.status)\s*==\s*'([^']+)'$")
_COUNT_RE = re.compile(r"^count_completed_refunds\(([^)]*)\)\s*(==|!=|>|>=|<|<=)\s*(\d+)$")
_FINANCE_PAY_RE = re.compile(r"^count_completed_finance_payments\(invoice_id='([^']+)'\)\s*(==|!=|>|>=|<|<=)\s*(\d+)$")
_TOTAL_RE = re.compile(r"^total_refunded_amount\(payment_id='([^']+)'\)\s*==\s*payment\.amount$")
_REFUND_CALLED_RE = re.compile(r"^create_refund\.called\s*==\s*(true|false)$")

_OPS: dict[str, Any] = {
    "==": lambda a, b: a == b,
    "!=": lambda a, b: a != b,
    ">": lambda a, b: a > b,
    ">=": lambda a, b: a >= b,
    "<": lambda a, b: a < b,
    "<=": lambda a, b: a <= b,
}


def evaluate_predicate(predicate: str, result: WorkflowRunResult, *, strict: bool = False) -> bool:
    """Return True if predicate holds for the given result.

    strict=True: unknown predicates return False (use for forbidden checks).
    strict=False: unknown predicates return True (use for expected checks — give benefit of doubt).
    """
    p = predicate.strip()

    # compound: split on " and " and evaluate each part
    if " and " in p:
        return all(evaluate_predicate(part, result, strict=strict) for part in p.split(" and "))

    # workflow.status == 'X'
    if p.startswith("workflow.status"):
        m = _STATUS_RE.match(p)
        if m:
            return result.status == m.group(2)
        return not strict

    # ticket.status == 'X'
    if p.startswith("ticket.status"):
        m = _STATUS_RE.match(p)
        if m and result.final_state is not None:
            return _ticket_status(result.final_state) == m.group(2)
        return not strict

    # count_completed_refunds(...) OP N
    m = _COUNT_RE.match(p)
    if m:
        args_str, op_str, expected_str = m.group(1).strip(), m.group(2), m.group(3)
        pid_match = _PAY_ID_RE.search(args_str)
        payment_id = pid_match.group(1) if pid_match else None
        fs = result.final_state or {}
        actual = _count_completed_refunds(fs, payment_id)
        return _OPS[op_str](actual, int(expected_str))

    # count_completed_finance_payments(invoice_id='X') OP N
    m = _FINANCE_PAY_RE.match(p)
    if m:
        invoice_id, op_str, expected_str = m.group(1), m.group(2), m.group(3)
        fs = result.final_state or {}
        actual = _count_completed_finance_payments(fs, invoice_id)
        return _OPS[op_str](actual, int(expected_str))

    # total_refunded_amount(payment_id='X') == payment.amount
    m = _TOTAL_RE.match(p)
    if m and result.final_state is not None:
        pid = m.group(1)
        total = _total_refunded_amount(result.final_state, pid)
        pay_amount = _payment_amount(result.final_state, pid)
        if pay_amount is not None:
            return abs(total - pay_amount) < 0.01
        return not strict

    # create_refund.called == false / true
    m = _REFUND_CALLED_RE.match(p)
    if m:
        expected_called = m.group(1) == "true"
        return _create_refund_was_called(result) == expected_called

    return not strict


def evaluate_predicates(predicates: list[str], result: WorkflowRunResult) -> bool:
    """Return True if all predicates hold."""
    return all(evaluate_predicate(p, result) for p in predicates)


def count_forbidden_violations(predicates: list[str], result: WorkflowRunResult) -> int:
    """Return number of forbidden predicates that hold (i.e. violations)."""
    return sum(1 for p in predicates if evaluate_predicate(p, result, strict=True))
