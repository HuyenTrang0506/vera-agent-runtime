"""Tests for YAML tool registry loader."""

from pathlib import Path

import pytest

from app.core.registry import load_tool_registry

SUPPORT_YAML = Path("app/registries/support_tools.yaml")
FINANCE_YAML = Path("app/registries/finance_tools.yaml")


def test_load_support_registry_returns_create_refund() -> None:
    registry = load_tool_registry(SUPPORT_YAML)
    assert "create_refund" in registry


def test_create_refund_metadata_fields() -> None:
    registry = load_tool_registry(SUPPORT_YAML)
    tool = registry["create_refund"]

    assert tool.name == "create_refund"
    assert "T_REFUND_CREATE" in tool.transition_effects
    assert "T_PAYMENT_REFUNDED_AMOUNT" in tool.transition_effects
    assert tool.reversibility == "irreversible"
    assert tool.risk_level == "high"
    assert tool.idempotency_required is True
    assert "refund_amount_gte_500" in tool.approval_required_when
    assert "timeout_after_commit" in tool.failure_modes


def test_load_finance_registry_returns_pay_invoice() -> None:
    registry = load_tool_registry(FINANCE_YAML)
    assert "pay_invoice" in registry


def test_pay_invoice_metadata_fields() -> None:
    registry = load_tool_registry(FINANCE_YAML)
    tool = registry["pay_invoice"]

    assert tool.name == "pay_invoice"
    assert "T_INVOICE_PAY" in tool.transition_effects
    assert tool.reversibility == "irreversible"
    assert tool.idempotency_required is True
    assert "invoice_amount_gte_5000" in tool.approval_required_when
    assert "timeout_after_commit" in tool.failure_modes


def test_registry_raises_on_missing_file() -> None:
    with pytest.raises(FileNotFoundError):
        load_tool_registry("nonexistent_registry.yaml")
