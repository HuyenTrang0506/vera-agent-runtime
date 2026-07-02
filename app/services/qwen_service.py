"""Qwen extraction service.

P0 supports live Qwen calls later and fixture fallback now.
"""

from pydantic import BaseModel

from app.core.config import settings
from app.models.extraction import ExtractionResult
from app.models.state import SupportFixture


class ExtractionServiceResult(BaseModel):
    extraction: ExtractionResult
    model_mode: str
    used_fixture_fallback: bool


def extract_from_fixture(payload: dict) -> ExtractionResult:
    return ExtractionResult.model_validate(payload)


def extract_support_request(
    request_text: str,
    fixture: SupportFixture,
    model_mode: str | None = None,
) -> ExtractionServiceResult:
    active_mode = model_mode or settings.model_mode
    if active_mode != "fixture_fallback":
        raise NotImplementedError("Live Qwen extraction is not implemented for P0 yet.")

    return ExtractionServiceResult(
        extraction=fixture.expected_extraction,
        model_mode=active_mode,
        used_fixture_fallback=True,
    )
