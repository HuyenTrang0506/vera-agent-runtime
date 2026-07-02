"""Hardcoded P0 policy predicates."""

from app.models.policies import PolicyResult


def allow(reason: str, rule_ids: list[str] | None = None) -> PolicyResult:
    return PolicyResult(decision="allow", rule_ids=rule_ids or [], reason=reason)


def deny(reason: str, rule_ids: list[str] | None = None) -> PolicyResult:
    return PolicyResult(decision="deny", rule_ids=rule_ids or [], reason=reason)

