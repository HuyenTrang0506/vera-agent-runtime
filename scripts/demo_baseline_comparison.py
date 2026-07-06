"""Live demo: VERA vs description-only baseline on support + finance benchmarks.

Run:
    python scripts/demo_baseline_comparison.py

Shows side-by-side metrics table for both domains. No flags needed.
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.eval.baselines import (
    run_description_only_baseline,
    run_finance_description_only_baseline,
)
from app.eval.reports import format_comparison_table
from app.eval.runner import run_benchmark
from scripts.run_eval import _comparison_table  # reuse existing delta logic

SUPPORT_BENCHMARK = str(ROOT / "data/benchmark/support_demo.jsonl")
FINANCE_BENCHMARK = str(ROOT / "data/benchmark/finance_demo.jsonl")

SEPARATOR = "=" * 62


def _run_finance_vera(benchmark_path: str, run_count: int) -> dict:
    import json
    from app.domains.finance.workflow import run_finance_workflow
    from app.eval.predicates import count_forbidden_violations, evaluate_predicates
    from app.models.evaluation import BenchmarkTask
    from app.models.approvals import ApprovalRecord
    from app.models.enums import ApprovalStatus

    task_rows = [
        json.loads(line)
        for line in Path(benchmark_path).read_text().splitlines()
        if line.strip()
    ]
    tasks = [BenchmarkTask.model_validate(row) for row in task_rows]
    tasks_out = []
    task_success_counts: dict[str, int] = {t.task_id: 0 for t in tasks}

    for _run_idx in range(run_count):
        for task, raw in zip(tasks, task_rows, strict=True):
            approval_record = None
            script = raw.get("approval_script")
            if script == "reject":
                approval_record = ApprovalRecord(
                    approval_id=f"apr_demo_{task.task_id}",
                    workflow_id=f"wf_demo_{task.task_id}",
                    status=ApprovalStatus.REJECTED,
                    requested_amount=0.0,
                    policy_rule_id="P_HIGH_VALUE_INVOICE_APPROVAL",
                    decided_by="demo_manager",
                )
            invoice_id = raw.get("invoice_id") or ""
            result = run_finance_workflow(
                fixture_id=task.fixture_id,
                invoice_id=invoice_id,
                approval_record=approval_record,
            )
            fsm = evaluate_predicates(task.expected_final_predicates, result)
            result = result.model_copy(update={"final_state_match": fsm})
            forbidden_violations = count_forbidden_violations(task.forbidden_predicates, result)
            if fsm and forbidden_violations == 0:
                task_success_counts[task.task_id] += 1
            tasks_out.append({
                "final_state_match": fsm,
                "forbidden_violations": forbidden_violations,
                "audit_receipts": len(result.audit_receipts),
            })

    num_tasks = len(tasks)
    total_runs = len(tasks_out)
    fsm_count = sum(1 for t in tasks_out if t["final_state_match"])
    success_count = sum(1 for t in tasks_out if t["final_state_match"] and t["forbidden_violations"] == 0)
    pass_k = (
        round(sum(1 for c in task_success_counts.values() if c == run_count) / num_tasks, 4)
        if num_tasks else 0.0
    )
    return {
        "pass_k": pass_k,
        "metrics": {
            "business_task_success_rate": round(success_count / total_runs, 4) if total_runs else 0.0,
            "final_state_exact_match_rate": round(fsm_count / total_runs, 4) if total_runs else 0.0,
            "forbidden_violation_count": sum(t["forbidden_violations"] for t in tasks_out),
            "audit_completeness_rate": round(
                sum(1 for t in tasks_out if t["audit_receipts"] > 0) / total_runs, 4
            ) if total_runs else 0.0,
        },
    }


def main() -> None:
    print(SEPARATOR)
    print("  VERA vs Baseline — Live Evidence Demo")
    print(SEPARATOR)

    # --- Support domain ---
    print("\nRunning support domain (5 scenarios × 1 run)...")
    vera_support = run_benchmark(SUPPORT_BENCHMARK, repeated_runs=1)
    baseline_support = run_description_only_baseline(SUPPORT_BENCHMARK, repeated_runs=1)
    comparison_support = _comparison_table(vera_support, baseline_support)
    print("\n" + format_comparison_table(comparison_support, title="SUPPORT DOMAIN"))

    # --- Finance domain ---
    print("\nRunning finance domain (3 scenarios × 1 run)...")
    vera_finance = _run_finance_vera(FINANCE_BENCHMARK, run_count=1)
    baseline_finance = run_finance_description_only_baseline(FINANCE_BENCHMARK, repeated_runs=1)
    comparison_finance = _comparison_table(vera_finance, baseline_finance)
    print("\n" + format_comparison_table(comparison_finance, title="FINANCE DOMAIN"))

    print(f"\n{SEPARATOR}")
    print("  What baseline gets wrong:")
    print("  - Duplicate invoice paid anyway    → forbidden violation")
    print("  - High-value rejection ignored     → no approval gate")
    print("  - Timeout after commit → retries   → duplicate payment")
    print("  - Audit trail                      → 0 receipts")
    print(SEPARATOR)


if __name__ == "__main__":
    main()
