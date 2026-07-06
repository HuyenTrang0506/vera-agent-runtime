"""Evaluation report rendering."""

from typing import Any

_METRIC_LABELS: dict[str, str] = {
    "business_task_success_rate": "Business Task Success Rate",
    "final_state_exact_match_rate": "Final State Exact Match",
    "desired_transition_match_rate": "Desired Transition Match",
    "audit_completeness_rate": "Audit Completeness",
    "approval_recall": "Approval Recall",
    "rejection_compliance_rate": "Rejection Compliance",
    "forbidden_transition_count": "Forbidden Transitions",
    "forbidden_violation_count": "Forbidden Violations",
    "duplicate_refund_count": "Duplicate Refunds",
    "pass_k": "Pass^k (reliability)",
}


def format_comparison_table(comparison: dict[str, Any], title: str = "") -> str:
    """Render comparison dict as a demo-friendly ASCII table.

    comparison keys: metric_name -> {vera/safeflow: val, baseline: val, delta: val}
    """
    col_metric = 36
    col_val = 10

    header_metric = "Metric"
    header_vera = "VERA"
    header_base = "Baseline"
    header_delta = "Delta"

    lines: list[str] = []
    if title:
        lines.append(title)
        lines.append("=" * (col_metric + col_val * 3 + 2))

    lines.append(
        f"{'Metric':<{col_metric}} {'VERA':>{col_val}} {'Baseline':>{col_val}} {'Delta':>{col_val}}"
    )
    lines.append("-" * (col_metric + col_val * 3 + 2))

    for key, vals in comparison.items():
        label = _METRIC_LABELS.get(key, key)
        vera_val = vals.get("safeflow") if "safeflow" in vals else vals.get("vera")
        base_val = vals.get("baseline")
        delta = vals.get("delta")

        vera_str = _fmt(vera_val)
        base_str = _fmt(base_val)
        delta_str = _fmt_delta(delta)

        lines.append(
            f"{label:<{col_metric}} {vera_str:>{col_val}} {base_str:>{col_val}} {delta_str:>{col_val}}"
        )

    return "\n".join(lines)


def _fmt(val: Any) -> str:
    if val is None:
        return "—"
    if isinstance(val, float):
        return f"{val:.4f}"
    return str(val)


def _fmt_delta(val: Any) -> str:
    if val is None:
        return ""
    if isinstance(val, float):
        sign = "+" if val > 0 else ""
        return f"{sign}{val:.4f}"
    return str(val)


def summarize_results() -> dict[str, str]:
    return {"status": "not_implemented"}
