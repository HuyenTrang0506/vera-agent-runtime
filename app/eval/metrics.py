"""P0 evaluation metric helpers."""


def exact_match(expected: bool, observed: bool) -> int:
    return int(expected == observed)

