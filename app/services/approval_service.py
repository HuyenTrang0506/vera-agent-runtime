"""Human approval lifecycle service."""

from app.core.config import settings


def approval_required(
    amount: float, threshold: float = settings.refund_approval_threshold
) -> bool:
    return amount >= threshold
