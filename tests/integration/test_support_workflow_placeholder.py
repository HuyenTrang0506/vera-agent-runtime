import pytest

from app.services.action_controller import ActionControllerNotImplemented, run_support_workflow


def test_support_workflow_placeholder_marks_not_implemented() -> None:
    with pytest.raises(ActionControllerNotImplemented):
        run_support_workflow()

