"""Run a deterministic VERA finance demo fixture."""

from argparse import ArgumentParser
import json

from app.domains.finance.workflow import run_finance_workflow
from app.models.approvals import ApprovalRecord
from app.models.enums import ApprovalStatus


def main() -> None:
    parser = ArgumentParser(description="VERA finance duplicate-invoice demo")
    parser.add_argument("--fixture", required=True, help="Finance fixture ID")
    parser.add_argument("--invoice-id", required=True, help="Invoice ID to process")
    parser.add_argument(
        "--approval",
        choices=["approve", "reject"],
        default=None,
        help="Pre-supply an approval decision (simulates manager action)",
    )
    args = parser.parse_args()

    approval_record: ApprovalRecord | None = None
    if args.approval == "reject":
        approval_record = ApprovalRecord(
            approval_id="apr_demo",
            workflow_id="wf_demo",
            status=ApprovalStatus.REJECTED,
            requested_amount=0.0,
            policy_rule_id="P_HIGH_VALUE_INVOICE_APPROVAL",
            decided_by="demo_manager",
        )
    elif args.approval == "approve":
        approval_record = ApprovalRecord(
            approval_id="apr_demo",
            workflow_id="wf_demo",
            status=ApprovalStatus.APPROVED,
            requested_amount=0.0,
            policy_rule_id="P_HIGH_VALUE_INVOICE_APPROVAL",
            decided_by="demo_manager",
        )

    result = run_finance_workflow(
        fixture_id=args.fixture,
        invoice_id=args.invoice_id,
        approval_record=approval_record,
    )
    print(json.dumps(result.model_dump(mode="json"), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
