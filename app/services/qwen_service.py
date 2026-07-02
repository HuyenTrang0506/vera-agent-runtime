"""Qwen extraction service.

P0 supports live Qwen calls later and fixture fallback now.
"""

from app.models.extraction import ExtractionResult


def extract_from_fixture(payload: dict) -> ExtractionResult:
    return ExtractionResult.model_validate(payload)

