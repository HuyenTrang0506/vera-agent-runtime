"""Unit tests for app.eval.predicates."""

from app.eval.predicates import evaluate_predicate, evaluate_predicates
from app.models.audit import AuditReceipt
from app.models.workflow import WorkflowRunResult


def _make_result(
    status: str = "completed",
    final_state: dict | None = None,
    audit_receipts: list[AuditReceipt] | None = None,
) -> WorkflowRunResult:
    return WorkflowRunResult(
        workflow_id="wf_test",
        status=status,
        desired_transition_id="T_REFUND_CREATE",
        policy_decision="allow",
        final_state_match=False,
        audit_receipt_ids=[],
        audit_receipts=audit_receipts or [],
        final_state=final_state,
    )


def _make_final_state(
    refunds: dict | None = None,
    tickets: dict | None = None,
    payments: dict | None = None,
) -> dict:
    return {
        "refunds": refunds or {},
        "tickets": tickets or {},
        "payments": payments or {},
    }


def _refund(payment_id: str, status: str = "completed", amount: float = 100.0) -> dict:
    return {"payment_id": payment_id, "status": status, "amount": amount}


def _payment(payment_id: str, amount: float) -> dict:
    return {"payment_id": payment_id, "amount": amount}


class TestWorkflowStatus:
    def test_matches_status(self):
        r = _make_result(status="denied")
        assert evaluate_predicate("workflow.status == 'denied'", r) is True

    def test_mismatches_status(self):
        r = _make_result(status="completed")
        assert evaluate_predicate("workflow.status == 'denied'", r) is False

    def test_escalated_mismatch(self):
        r = _make_result(status="escalated_state_mismatch")
        assert evaluate_predicate("workflow.status == 'escalated_state_mismatch'", r) is True


class TestTicketStatus:
    def test_matches_ticket_status(self):
        fs = _make_final_state(tickets={"t1": {"status": "resolved"}})
        r = _make_result(final_state=fs)
        assert evaluate_predicate("ticket.status == 'resolved'", r) is True

    def test_mismatches_ticket_status(self):
        fs = _make_final_state(tickets={"t1": {"status": "new"}})
        r = _make_result(final_state=fs)
        assert evaluate_predicate("ticket.status == 'resolved'", r) is False

    def test_no_final_state_skips(self):
        r = _make_result(final_state=None)
        assert evaluate_predicate("ticket.status == 'resolved'", r) is True


class TestCountCompletedRefunds:
    def test_one_completed_refund_no_payment_id(self):
        fs = _make_final_state(refunds={"r1": _refund("pay_001")})
        r = _make_result(final_state=fs)
        assert evaluate_predicate("count_completed_refunds() == 1", r) is True

    def test_zero_refunds(self):
        r = _make_result(final_state=_make_final_state())
        assert evaluate_predicate("count_completed_refunds() == 0", r) is True

    def test_payment_id_filter_match(self):
        fs = _make_final_state(refunds={
            "r1": _refund("pay_dup_001"),
            "r2": _refund("pay_other", status="failed"),
        })
        r = _make_result(final_state=fs)
        assert evaluate_predicate("count_completed_refunds(payment_id='pay_dup_001') == 1", r) is True

    def test_payment_id_filter_mismatch(self):
        fs = _make_final_state(refunds={"r1": _refund("pay_other")})
        r = _make_result(final_state=fs)
        assert evaluate_predicate("count_completed_refunds(payment_id='pay_dup_001') == 1", r) is False

    def test_duplicate_refund_detected(self):
        fs = _make_final_state(refunds={
            "r1": _refund("pay_dup_001"),
            "r2": _refund("pay_dup_001"),
        })
        r = _make_result(final_state=fs)
        assert evaluate_predicate("count_completed_refunds(payment_id='pay_dup_001') == 1", r) is False
        assert evaluate_predicate("count_completed_refunds(payment_id='pay_dup_001') == 2", r) is True


class TestTotalRefundedAmount:
    def test_matches_payment_amount(self):
        fs = _make_final_state(
            refunds={"r1": _refund("pay_001", amount=250.0)},
            payments={"p1": _payment("pay_001", 250.0)},
        )
        r = _make_result(final_state=fs)
        assert evaluate_predicate("total_refunded_amount(payment_id='pay_001') == payment.amount", r) is True

    def test_partial_refund_mismatch(self):
        fs = _make_final_state(
            refunds={"r1": _refund("pay_001", amount=100.0)},
            payments={"p1": _payment("pay_001", 250.0)},
        )
        r = _make_result(final_state=fs)
        assert evaluate_predicate("total_refunded_amount(payment_id='pay_001') == payment.amount", r) is False


class TestCreateRefundCalled:
    def _receipt(self, action_id: str, outcome: str = "success") -> AuditReceipt:
        return AuditReceipt(
            receipt_id="rec_1",
            workflow_id="wf_test",
            action_id=action_id,
            intended_transition="T_REFUND_CREATE",
            observed_transition="T_REFUND_CREATE",
            policy_decision="allow",
            pre_state_hash="aaa",
            post_state_hash="bbb",
            outcome=outcome,
        )

    def test_called_true(self):
        r = _make_result(audit_receipts=[self._receipt("create_refund_pay_001")])
        assert evaluate_predicate("create_refund.called == true", r) is True

    def test_called_false_no_receipts(self):
        r = _make_result()
        assert evaluate_predicate("create_refund.called == false", r) is True

    def test_called_false_with_receipt(self):
        r = _make_result(audit_receipts=[self._receipt("create_refund_pay_001")])
        assert evaluate_predicate("create_refund.called == false", r) is False


class TestEvalAllPredicates:
    def test_all_pass(self):
        fs = _make_final_state(
            refunds={"r1": _refund("pay_001")},
            tickets={"t1": {"status": "resolved"}},
        )
        r = _make_result(status="completed", final_state=fs)
        assert evaluate_predicates([
            "count_completed_refunds(payment_id='pay_001') == 1",
            "ticket.status == 'resolved'",
            "workflow.status == 'completed'",
        ], r) is True

    def test_one_fails(self):
        fs = _make_final_state(tickets={"t1": {"status": "new"}})
        r = _make_result(status="completed", final_state=fs)
        assert evaluate_predicates([
            "workflow.status == 'completed'",
            "ticket.status == 'resolved'",
        ], r) is False

    def test_unknown_predicate_passes(self):
        r = _make_result()
        assert evaluate_predicate("some.unknown.predicate == 'x'", r) is True
