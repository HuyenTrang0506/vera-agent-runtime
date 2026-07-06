"""Generic tool executor: precondition snapshot → execute → observe transitions → audit receipt."""

from dataclasses import dataclass, field
from typing import Any, Callable

from app.models.audit import AuditReceipt
from app.models.enums import PolicyDecision
from app.models.tools import ToolMetadata
from app.services.audit_service import build_receipt
from app.services.recovery_service import should_recheck_state
from app.services.state_service import snapshot_state, state_hash


@dataclass
class ExecutorResult:
    success: bool
    committed: bool  # True even when error == timeout_after_commit
    pre_state_hash: str
    post_state_hash: str
    observed_transitions: list[str]
    receipt: AuditReceipt | None = None
    error: str | None = None
    recovered_timeout: bool = False
    action_id: str = "unknown"


class ToolExecutor:
    """Registry-driven executor. Same pipeline for every tool:
    snapshot → call → recover → observe → receipt."""

    def __init__(
        self,
        metadata: ToolMetadata,
        tool_fn: Callable,
        observe_fn: Callable[[dict, Any, dict], list[str]],
        # observe_fn(pre_state_snapshot, post_state, ctx) -> [transition_ids]
    ) -> None:
        self.metadata = metadata
        self.tool_fn = tool_fn
        self.observe_fn = observe_fn

    def run(
        self,
        workflow_id: str,
        state: Any,
        params: dict,
        failure_mode: str,
        policy_decision: PolicyDecision,
    ) -> ExecutorResult:
        pre_snapshot = snapshot_state(state)
        pre_hash = state_hash(pre_snapshot)

        result = self.tool_fn(state, **params, failure_mode=failure_mode)

        post_hash = state_hash(state)
        action_id = getattr(result, "refund", None) or getattr(result, "payment", None)
        action_id = action_id.payment_id if hasattr(action_id, "payment_id") else (
            action_id.refund_id if hasattr(action_id, "refund_id") else self.metadata.name
        )

        error = result.error if not result.success else None
        recovered_timeout = bool(error and should_recheck_state(error))
        committed = result.success or recovered_timeout

        # Hard failure — not recoverable, no transition to observe
        if not committed:
            receipt = build_receipt(
                workflow_id=workflow_id,
                action_id=self.metadata.name,
                intended_transition=",".join(self.metadata.transition_effects),
                observed_transition="none",
                policy_decision=policy_decision,
                pre_state_hash=pre_hash,
                post_state_hash=post_hash,
                outcome="failed",
            )
            return ExecutorResult(
                success=False,
                committed=False,
                pre_state_hash=pre_hash,
                post_state_hash=post_hash,
                observed_transitions=[],
                receipt=receipt,
                error=error,
                action_id=self.metadata.name,
            )

        observed = self.observe_fn(pre_snapshot, state, params)
        expected = self.metadata.transition_effects
        matches = all(t in observed for t in expected)

        if not matches and not recovered_timeout:
            outcome = "escalated"
        elif not matches and recovered_timeout:
            # timeout_after_commit but state not yet visible — treat as failed
            outcome = "failed"
        elif recovered_timeout:
            outcome = "recovered"
        else:
            outcome = "success"

        receipt = build_receipt(
            workflow_id=workflow_id,
            action_id=str(action_id),
            intended_transition=",".join(expected),
            observed_transition=",".join(observed) if observed else "none",
            policy_decision=policy_decision,
            pre_state_hash=pre_hash,
            post_state_hash=post_hash,
            outcome=outcome,
        )

        return ExecutorResult(
            success=matches or recovered_timeout,
            committed=committed,
            pre_state_hash=pre_hash,
            post_state_hash=post_hash,
            observed_transitions=observed,
            receipt=receipt,
            error=error if not matches else None,
            recovered_timeout=recovered_timeout,
            action_id=str(action_id),
        )
