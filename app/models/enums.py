"""Shared enums for workflow, policy, and approval state."""

from enum import StrEnum


class WorkflowStatus(StrEnum):
    RECEIVED = "received"
    EXTRACTED = "extracted"
    PLANNED = "planned"
    POLICY_CHECKED = "policy_checked"
    APPROVAL_PENDING = "approval_pending"
    EXECUTING = "executing"
    VALIDATING = "validating"
    COMPLETED = "completed"
    COMPLETED_WITH_RECOVERED_TIMEOUT = "completed_with_recovered_timeout"
    DENIED = "denied"
    PENDING_MANUAL_REVIEW = "pending_manual_review"
    ESCALATED_STATE_MISMATCH = "escalated_state_mismatch"
    FAILED_SAFE = "failed_safe"


class PolicyDecision(StrEnum):
    ALLOW = "allow"
    DENY = "deny"
    APPROVAL_REQUIRED = "approval_required"
    ESCALATE = "escalate"


class ApprovalStatus(StrEnum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"

