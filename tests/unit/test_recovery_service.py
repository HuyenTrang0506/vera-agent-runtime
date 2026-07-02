from app.services.recovery_service import should_recheck_state


def test_should_recheck_state_only_for_timeout_after_commit() -> None:
    assert should_recheck_state("timeout_after_commit") is True
    assert should_recheck_state("timeout_before_commit") is False
    assert should_recheck_state("payment_not_found") is False
