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
    parser.add_argument("--report", action="store_true", help="Print ASCII comparison table instead of JSON")
    parser.add_argument(
        "--domain",
        choices=["support", "finance"],
        default="support",
        help="Domain for the benchmark (default: support)",
    )
    args = parser.parse_args()

    if args.domain == "finance":
        from app.eval.predicates import count_forbidden_violations, evaluate_predicates
        from app.models.evaluation import BenchmarkTask

        task_rows = [
            json.loads(line)
            for line in Path(args.benchmark).read_text().splitlines()
            if line.strip()
        ]
        # Validate each row eagerly — fail fast before any run starts
        tasks = [BenchmarkTask.model_validate(row) for row in task_rows]

        run_count = args.repeated_runs or 1
        tasks_out = []
        task_success_counts: dict[str, int] = {task.task_id: 0 for task in tasks}

        for run_idx in range(run_count):
            for task, raw in zip(tasks, task_rows, strict=True):
                approval_record = None
                approval_script = raw.get("approval_script")
                if approval_script == "reject":
                    approval_record = ApprovalRecord(
                        approval_id=f"apr_eval_{task.task_id}",
                        workflow_id=f"wf_eval_{task.task_id}",
                        status=ApprovalStatus.REJECTED,
                        requested_amount=0.0,
                        policy_rule_id="P_HIGH_VALUE_INVOICE_APPROVAL",
                        decided_by="eval_manager",
                    )
                elif approval_script == "approve":
                    approval_record = ApprovalRecord(
                        approval_id=f"apr_eval_{task.task_id}",
                        workflow_id=f"wf_eval_{task.task_id}",
                        status=ApprovalStatus.APPROVED,
                        requested_amount=0.0,
                        policy_rule_id="P_HIGH_VALUE_INVOICE_APPROVAL",
                        decided_by="eval_manager",
                    )

                invoice_id = raw.get("invoice_id") or ""
                result = run_finance_workflow(
                    fixture_id=task.fixture_id,
                    invoice_id=invoice_id,
                    approval_record=approval_record,
                )

                fsm = evaluate_predicates(task.expected_final_predicates, result)
                result = result.model_copy(update={"final_state_match": fsm})

                forbidden_violations = count_forbidden_violations(
                    task.forbidden_predicates, result
                )
                is_success = fsm and forbidden_violations == 0
                if is_success:
                    task_success_counts[task.task_id] += 1

                tasks_out.append(
                    {
                        "run_index": run_idx,
                        "task_id": task.task_id,
                        "fixture_id": task.fixture_id,
                        "status": result.status,
                        "policy_decision": result.policy_decision,
                        "final_state_match": fsm,
                        "forbidden_violations": forbidden_violations,
                        "audit_receipts": len(result.audit_receipts),
                    }
                )

        num_tasks = len(tasks)
        total_runs = len(tasks_out)
        fsm_count = sum(1 for t in tasks_out if t["final_state_match"])
        success_count = sum(1 for t in tasks_out if t["final_state_match"] and t["forbidden_violations"] == 0)
        pass_k = (
            round(sum(1 for c in task_success_counts.values() if c == run_count) / num_tasks, 4)
            if num_tasks else 0.0
        )

        output = {
            "domain": "finance",
            "benchmark_path": args.benchmark,
            "repeated_runs": run_count,
            "pass_k": pass_k,
            "metrics": {
                "total_tasks": total_runs,
                "task_count": num_tasks,
                "business_task_success_rate": round(success_count / total_runs, 4) if total_runs else 0.0,
                "forbidden_violation_count": sum(t["forbidden_violations"] for t in tasks_out),
                "final_state_exact_match_rate": round(fsm_count / total_runs, 4) if total_runs else 0.0,
                "audit_completeness_rate": round(
                    sum(1 for t in tasks_out if t["audit_receipts"] > 0) / total_runs, 4
                ) if total_runs else 0.0,
            },
            "tasks": tasks_out,
        }

        if args.include_baseline:
            from app.eval.baselines import run_finance_description_only_baseline
            baseline = run_finance_description_only_baseline(
                args.benchmark, repeated_runs=run_count
            )
            output["baseline"] = baseline
            output["comparison"] = _comparison_table(output, baseline)

        if args.report and args.include_baseline and "comparison" in output:
            from app.eval.reports import format_comparison_table
            print(format_comparison_table(output["comparison"], title="=== FINANCE DOMAIN: VERA vs Baseline ==="))
        else:
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

    if args.report and args.include_baseline and "comparison" in result:
        from app.eval.reports import format_comparison_table
        print(format_comparison_table(result["comparison"], title="=== SUPPORT DOMAIN: VERA vs Baseline ==="))
    else:
        print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
