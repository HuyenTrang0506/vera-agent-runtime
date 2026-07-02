from app.services.state_service import state_hash


def test_state_hash_is_order_invariant() -> None:
    assert state_hash({"b": 2, "a": 1}) == state_hash({"a": 1, "b": 2})

