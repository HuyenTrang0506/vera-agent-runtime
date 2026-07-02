import pytest
from pydantic import ValidationError

from app.models.extraction import ExtractionResult
from app.services.qwen_service import extract_from_fixture, extract_support_request
from app.services.state_service import load_support_fixture


def test_extract_from_fixture_validates_expected_extraction() -> None:
    fixture = load_support_fixture("support_refund_happy_001")

    extraction = extract_from_fixture(fixture.expected_extraction.model_dump(mode="json"))

    assert extraction.domain == "customer_support"
    assert extraction.intent == "request_refund_for_duplicate_charge"
    assert extraction.desired_transition.transition_id == "T_REFUND_CREATE"


def test_extraction_rejects_unknown_transition() -> None:
    with pytest.raises(ValidationError):
        ExtractionResult.model_validate(
            {
                "domain": "customer_support",
                "intent": "request_refund_for_duplicate_charge",
                "entities": {"customer_email": "customer@example.com"},
                "desired_transition": {
                    "transition_id": "T_UNKNOWN",
                    "from_state": "unknown",
                    "to_state": "unknown",
                },
                "confidence": 0.9,
            }
        )


def test_extract_support_request_uses_explicit_fixture_fallback() -> None:
    fixture = load_support_fixture("support_refund_happy_001")

    result = extract_support_request(
        request_text="I was charged twice for order ord_A102.",
        fixture=fixture,
        model_mode="fixture_fallback",
    )

    assert result.model_mode == "fixture_fallback"
    assert result.used_fixture_fallback is True
    assert result.extraction.entities.order_id == "ord_A102"


def test_extract_support_request_rejects_unimplemented_live_mode() -> None:
    fixture = load_support_fixture("support_refund_happy_001")

    with pytest.raises(NotImplementedError):
        extract_support_request(
            request_text="I was charged twice for order ord_A102.",
            fixture=fixture,
            model_mode="qwen",
        )
