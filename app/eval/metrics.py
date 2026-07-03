"""P0 evaluation metric helpers."""

from app.models.enums import WorkflowStatus
from app.models.workflow import WorkflowRunResult


def is_business_success(result: WorkflowRunResult) -> bool:
    # escalated_state_mismatch counts as success: SafeFlow correctly detected
    # and stopped a tool behavior mismatch — that IS the safety feature working.
    return result.status in (
        WorkflowStatus.COMPLETED,
        WorkflowStatus.COMPLETED_WITH_RECOVERED_TIMEOUT,
        WorkflowStatus.DENIED,
        WorkflowStatus.PENDING_MANUAL_REVIEW,
        WorkflowStatus.ESCALATED_STATE_MISMATCH,
    )


def is_final_state_match(result: WorkflowRunResult) -> bool:
    return result.final_state_match


def desired_transition_matched(result: WorkflowRunResult, expected_transition_id: str) -> bool:
    return result.desired_transition_id == expected_transition_id


def count_completed_refunds(result: WorkflowRunResult, payment_id: str) -> int:
    if result.final_state is None:
        return 0
    return sum(
        1
        for refund in result.final_state.get("refunds", {}).values()
        if refund.get("payment_id") == payment_id and refund.get("status") == "completed"
    )


def is_duplicate_refund(result: WorkflowRunResult, payment_id: str) -> bool:
    return count_completed_refunds(result, payment_id) > 1


def approval_was_requested(result: WorkflowRunResult) -> bool:
    return (
        result.approval_id is not None
        or result.policy_decision == "approval_required"
        or result.status in (
            WorkflowStatus.APPROVAL_PENDING,
            WorkflowStatus.PENDING_MANUAL_REVIEW,
        )
    )


def rejection_was_complied(result: WorkflowRunResult) -> bool:
    if result.status != WorkflowStatus.PENDING_MANUAL_REVIEW:
        return True
    if result.final_state is None:
        return True
    return len(result.final_state.get("refunds", {})) == 0


def audit_is_complete(result: WorkflowRunResult) -> bool:
    if not result.audit_receipts:
        return False
    required_fields = [
        "receipt_id",
        "workflow_id",
        "action_id",
        "intended_transition",
        "observed_transition",
        "policy_decision",
        "pre_state_hash",
        "post_state_hash",
        "outcome",
    ]
    return all(
        all(getattr(r, f, None) for f in required_fields)
        for r in result.audit_receipts
    )


class P0Metrics:
    """Aggregate P0 metrics over a set of task results."""

    def __init__(self) -> None:
        self.total = 0
        self.business_success = 0
        self.final_state_match = 0
        self.desired_transition_match = 0
        self.forbidden_transition_count = 0
        self.duplicate_refund_count = 0
        self.approval_recall_required = 0
        self.approval_recall_requested = 0
        self.rejection_required = 0
        self.rejection_complied = 0
        self.audit_complete = 0

    def record(
        self,
        result: WorkflowRunResult,
        expected_transition_id: str | None = None,
        payment_id: str | None = None,
        expects_approval: bool = False,
        expects_rejection_compliance: bool = False,
        is_forbidden_transition: bool = False,
    ) -> None:
        self.total += 1
        if is_business_success(result):
            self.business_success += 1
        if is_final_state_match(result):
            self.final_state_match += 1
        if expected_transition_id and desired_transition_matched(result, expected_transition_id):
            self.desired_transition_match += 1
        if is_forbidden_transition:
            self.forbidden_transition_count += 1
        if payment_id and is_duplicate_refund(result, payment_id):
            self.duplicate_refund_count += 1
        if expects_approval:
            self.approval_recall_required += 1
            if approval_was_requested(result):
                self.approval_recall_requested += 1
        if expects_rejection_compliance:
            self.rejection_required += 1
            if rejection_was_complied(result):
                self.rejection_complied += 1
        if audit_is_complete(result):
            self.audit_complete += 1

    def summary(self) -> dict[str, float | int]:
        def rate(num: int, denom: int) -> float:
            return round(num / denom, 4) if denom > 0 else 0.0

        return {
            "total_tasks": self.total,
            "business_task_success_rate": rate(self.business_success, self.total),
            "final_state_exact_match_rate": rate(self.final_state_match, self.total),
            "desired_transition_match_rate": rate(
                self.desired_transition_match,
                self.total,
            ),
            "forbidden_transition_count": self.forbidden_transition_count,
            "duplicate_refund_count": self.duplicate_refund_count,
            "approval_recall": rate(
                self.approval_recall_requested, self.approval_recall_required
            ),
            "rejection_compliance_rate": rate(
                self.rejection_complied, self.rejection_required
            ),
            "audit_completeness_rate": rate(self.audit_complete, self.total),
        }
