"""State-transition-aware action controller.

This module owns the P0 decision table. Keep domain tool internals out of here.
"""


class ActionControllerNotImplemented(NotImplementedError):
    """Raised until the P0 controller is implemented."""


def run_support_workflow() -> None:
    raise ActionControllerNotImplemented("Support workflow controller is not implemented yet.")

