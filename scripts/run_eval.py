"""Run SafeFlow evaluation benchmark."""

from argparse import ArgumentParser
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def _comparison_table(safeflow: dict, baseline: dict) -> dict:
    """Produce a side-by-side delta for every shared metric."""
    sf = safeflow.get("metrics", {})
    bl = baseline.get("metrics", {})
    rows = {}
    for key in sf:
        sf_val = sf[key]
        bl_val = bl.get(key)
        if bl_val is None:
            continue
        if isinstance(sf_val, float) and isinstance(bl_val, float):
            delta = round(sf_val - bl_val, 4)
            rows[key] = {"safeflow": sf_val, "baseline": bl_val, "delta": delta}
        else:
            rows[key] = {"safeflow": sf_val, "baseline": bl_val}
    # pass^k comparison
    sf_pk = safeflow.get("pass_k")
    bl_pk = baseline.get("pass_k")
    if sf_pk is not None and bl_pk is not None:
        rows["pass_k"] = {
            "safeflow": sf_pk,
            "baseline": bl_pk,
            "delta": round(sf_pk - bl_pk, 4),
        }
    return rows


def main() -> None:
    from app.eval.baselines import run_description_only_baseline
    from app.eval.runner import run_benchmark
    from app.domains.finance.workflow import run_finance_workflow
    from app.models.approvals import ApprovalRecord
    from app.models.enums import ApprovalStatus

    parser = ArgumentParser(description="VERA evaluation CLI")
    parser.add_argument("--benchmark", required=True, help="Path to JSONL benchmark file")
    parser.add_argument("--repeated-runs", type=int, default=None)
    parser.add_argument("--include-baseline", action="store_true")
    parser.add_argument(
        "--domain",
        choices=["support", "finance"],
        default="support",
        help="Domain for the benchmark (default: support)",
    )
    args = parser.parse_args()

    if args.domain == "finance":
        # Finance benchmark runs inline — no full runner yet, just task-by-task
        rows = []
        for line in Path(args.benchmark).read_text().splitlines():
            line = line.strip()
            if line:
                rows.append(json.loads(line))

        run_count = args.repeated_runs or 1
        tasks_out = []
        for run_idx in range(run_count):
            for row in rows:
                approval_record = None
                if row.get("approval_script") == "reject":
                    approval_record = ApprovalRecord(
                        approval_id=f"apr_eval_{row['task_id']}",
                        workflow_id=f"wf_eval_{row['task_id']}",
                        status=ApprovalStatus.REJECTED,
                        requested_amount=0.0,
                        policy_rule_id="P_HIGH_VALUE_INVOICE_APPROVAL",
                        decided_by="eval_manager",
                    )
                elif row.get("approval_script") == "approve":
                    approval_record = ApprovalRecord(
                        approval_id=f"apr_eval_{row['task_id']}",
                        workflow_id=f"wf_eval_{row['task_id']}",
                        status=ApprovalStatus.APPROVED,
                        requested_amount=0.0,
                        policy_rule_id="P_HIGH_VALUE_INVOICE_APPROVAL",
                        decided_by="eval_manager",
                    )

                result = run_finance_workflow(
                    fixture_id=row["fixture_id"],
                    invoice_id=row["invoice_id"],
                    approval_record=approval_record,
                )

                expected = row.get("expected_final_predicates", [])
                from app.eval.predicates import evaluate_predicate, count_forbidden_violations

                fsm = all(evaluate_predicate(p, result) for p in expected)
                forbidden_violations = count_forbidden_violations(
                    row.get("forbidden_predicates", []), result
                )

                tasks_out.append(
                    {
                        "run_index": run_idx,
                        "task_id": row["task_id"],
                        "fixture_id": row["fixture_id"],
                        "status": result.status,
                        "policy_decision": result.policy_decision,
                        "final_state_match": fsm,
                        "forbidden_violations": forbidden_violations,
                        "audit_receipts": len(result.audit_receipts),
                    }
                )

        total = len(tasks_out)
        success = sum(
            1 for t in tasks_out
            if t["final_state_match"] and t["forbidden_violations"] == 0
        )
        output = {
            "domain": "finance",
            "benchmark_path": args.benchmark,
            "repeated_runs": run_count,
            "metrics": {
                "total_tasks": total,
                "business_task_success_rate": round(success / total, 4) if total else 0.0,
                "forbidden_violation_count": sum(t["forbidden_violations"] for t in tasks_out),
                "final_state_exact_match_rate": round(
                    sum(1 for t in tasks_out if t["final_state_match"]) / total, 4
                ) if total else 0.0,
            },
            "tasks": tasks_out,
        }
        print(json.dumps(output, indent=2, sort_keys=True))
        return

    # Support domain (default)
    result = run_benchmark(args.benchmark, repeated_runs=args.repeated_runs)

    if args.include_baseline:
        baseline = run_description_only_baseline(
            args.benchmark,
            repeated_runs=args.repeated_runs or 1,
        )
        result["baseline"] = baseline
        result["comparison"] = _comparison_table(result, baseline)

    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
