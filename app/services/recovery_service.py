"""Recovery and safe-stop behavior."""


def should_recheck_state(error_code: str) -> bool:
    return error_code == "timeout_after_commit"

