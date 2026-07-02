from app.services.audit_service import build_receipt, timeline_event_from_receipt


def test_timeline_event_from_receipt_links_audit_evidence() -> None:
    receipt = build_receipt(
        workflow_id="wf_test",
        action_id="ref_test",
        intended_transition="T_REFUND_CREATE",
        observed_transition="T_REFUND_CREATE",
        policy_decision="allow",
        pre_state_hash="pre_hash",
        post_state_hash="post_hash",
        outcome="success",
    )

    event = timeline_event_from_receipt(receipt)

    assert event.workflow_id == "wf_test"
    assert event.event_type == "success"
    assert event.receipt_id == receipt.receipt_id
    assert event.state_hash == "post_hash"
    assert "T_REFUND_CREATE" in event.summary
