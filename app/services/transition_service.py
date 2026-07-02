"""Intended and observed transition validation."""


def transition_matches(expected_transition_id: str, observed_transition_ids: list[str]) -> bool:
    return expected_transition_id in observed_transition_ids

