from app.eval.metrics import P0Metrics, audit_is_complete, count_completed_refunds
from app.models.audit import AuditReceipt
from app.models.workflow import WorkflowRunResult


def _result_with_refunds(refund_count: int = 1) -> WorkflowRunResult:
    refunds = {
        f"ref_{index}": {
            "refund_id": f"ref_{index}",
            "payment_id": "pay_dup_001",
            "status": "completed",
            "amount": 120.0,
            "idempotency_key": f"key_{index}",
            "approval_id": None,
        }
        for index in range(refund_count)
    }
    return WorkflowRunResult(
        workflow_id="wf_metric",
        status="completed",
        desired_transition_id="T_REFUND_CREATE",
        policy_decision="allow",
        final_state_match=True,
        audit_receipt_ids=["aud_metric"],
        audit_receipts=[
            AuditReceipt(
                receipt_id="aud_metric",
                workflow_id="wf_metric",
                action_id="ref_0",
                intended_transition="T_REFUND_CREATE",
                observed_transition="T_REFUND_CREATE",
                policy_decision="allow",
                pre_state_hash="pre_hash",
                post_state_hash="post_hash",
                outcome="success",
            )
        ],
        final_state={"refunds": refunds},
    )


def test_count_completed_refunds_reads_final_state() -> None:
    result = _result_with_refunds(refund_count=2)

    assert count_completed_refunds(result, "pay_dup_001") == 2
    assert count_completed_refunds(result, "pay_other") == 0


def test_audit_is_complete_requires_receipt_fields() -> None:
    assert audit_is_complete(_result_with_refunds()) is True

    missing_audit = _result_with_refunds()
    missing_audit.audit_receipts = []

    assert audit_is_complete(missing_audit) is False


def test_p0_metrics_summary_aggregates_structured_results() -> None:
    metrics = P0Metrics()

    metrics.record(
        _result_with_refunds(),
        expected_transition_id="T_REFUND_CREATE",
        payment_id="pay_dup_001",
        expects_approval=False,
        expects_rejection_compliance=False,
        is_forbidden_transition=False,
    )

    summary = metrics.summary()
    assert summary["total_tasks"] == 1
    assert summary["business_task_success_rate"] == 1.0
    assert summary["final_state_exact_match_rate"] == 1.0
    assert summary["desired_transition_match_rate"] == 1.0
    assert summary["audit_completeness_rate"] == 1.0
