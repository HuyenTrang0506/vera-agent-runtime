"""ID helpers for stable SafeFlow entity prefixes."""

from uuid import uuid4


def new_id(prefix: str) -> str:
    return f"{prefix}{uuid4().hex[:12]}"

