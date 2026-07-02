"""Audit SafeFlow benchmark and fixture diversity."""

from argparse import ArgumentParser
from collections import Counter
import json
from pathlib import Path


REQUIRED_SCENARIOS = {
    "happy": 5,
    "timeout_after_commit": 4,
    "high_value_approve": 3,
    "high_value_reject": 3,
    "no_duplicate": 3,
    "tool_mismatch": 2,
    "already_refunded": 2,
    "missing_order_id": 2,
    "wrong_order_reference": 2,
    "partial_refund": 2,
    "concurrent_duplicate_workflow": 2,
    "prompt_injection": 2,
}


def load_jsonl(path: Path) -> list[dict]:
    rows = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError as exc:
            raise SystemExit(f"{path}:{line_number} invalid JSON: {exc}") from exc
    return rows


def scenario_for(task: dict) -> str:
    task_id = task.get("task_id", "")
    if "timeout_after_commit" in task_id:
        return "timeout_after_commit"
    if "high_value_approve" in task_id:
        return "high_value_approve"
    if "high_value_reject" in task_id:
        return "high_value_reject"
    if "no_duplicate" in task_id:
        return "no_duplicate"
    if "tool_mismatch" in task_id:
        return "tool_mismatch"
    if "already_refunded" in task_id:
        return "already_refunded"
    if "missing_order_id" in task_id:
        return "missing_order_id"
    if "wrong_order_reference" in task_id:
        return "wrong_order_reference"
    if "partial_refund" in task_id:
        return "partial_refund"
    if "concurrent_duplicate_workflow" in task_id:
        return "concurrent_duplicate_workflow"
    if "prompt_injection" in task_id:
        return "prompt_injection"
    if "happy" in task_id:
        return "happy"
    return "unknown"


def audit(benchmark_path: Path, fixtures_root: Path) -> tuple[list[str], dict]:
    tasks = load_jsonl(benchmark_path)
    warnings = []
    errors = []
    scenarios = Counter(scenario_for(task) for task in tasks)
    failure_modes = Counter(task.get("failure_mode", "missing") for task in tasks)
    approval_scripts = Counter(str(task.get("approval_script")) for task in tasks)
    request_texts = Counter(task.get("request_text", "") for task in tasks)
    complexity_flags: Counter[str] = Counter()

    task_ids = [task.get("task_id") for task in tasks]
    duplicate_task_ids = [task_id for task_id, count in Counter(task_ids).items() if count > 1]
    if duplicate_task_ids:
        errors.append(f"duplicate task ids: {duplicate_task_ids[:5]}")

    required_keys = {
        "task_id",
        "domain",
        "fixture_id",
        "request_text",
        "failure_mode",
        "expected_final_predicates",
        "forbidden_predicates",
    }
    for task in tasks:
        missing = sorted(required_keys - set(task))
        if missing:
            errors.append(f"{task.get('task_id', '<unknown>')} missing keys: {missing}")
        if not task.get("expected_final_predicates"):
            errors.append(f"{task.get('task_id')} has no expected_final_predicates")
        if not task.get("forbidden_predicates"):
            errors.append(f"{task.get('task_id')} has no forbidden_predicates")

        fixture_id = task.get("fixture_id")
        fixture_matches = list(fixtures_root.glob(f"**/{fixture_id}.json"))
        if not fixture_matches:
            errors.append(f"{task.get('task_id')} missing fixture {fixture_id}")
            continue
        fixture = json.loads(fixture_matches[0].read_text(encoding="utf-8"))
        for key in ["fixture_id", "state", "expected_extraction"]:
            if key not in fixture:
                errors.append(f"{fixture_id} fixture missing `{key}`")
        complexity_flags.update(fixture.get("complexity_flags", []))

    if len(tasks) < 20:
        warnings.append(f"benchmark has {len(tasks)} tasks; P0 target is at least 20")

    for scenario, minimum in REQUIRED_SCENARIOS.items():
        if scenarios[scenario] < minimum:
            warnings.append(
                f"scenario `{scenario}` has {scenarios[scenario]} tasks; target is {minimum}"
            )

    if "unknown" in scenarios:
        warnings.append(f"unknown scenario tasks: {scenarios['unknown']}")

    if len(request_texts) < min(6, len(tasks)):
        warnings.append(
            f"request language has only {len(request_texts)} unique texts; target is at least 6"
        )

    if len(tasks) >= 20 and not complexity_flags:
        warnings.append("no fixture complexity flags found; state complexity may be too simple")

    summary = {
        "tasks": len(tasks),
        "scenarios": dict(sorted(scenarios.items())),
        "failure_modes": dict(sorted(failure_modes.items())),
        "approval_scripts": dict(sorted(approval_scripts.items())),
        "unique_request_texts": len(request_texts),
        "complexity_flags": dict(sorted(complexity_flags.items())),
        "errors": errors,
        "warnings": warnings,
    }
    return errors + warnings, summary


def main() -> None:
    parser = ArgumentParser()
    parser.add_argument("--benchmark", default="data/benchmark/support_demo.jsonl")
    parser.add_argument("--fixtures-root", default="data/fixtures")
    args = parser.parse_args()

    issues, summary = audit(Path(args.benchmark), Path(args.fixtures_root))
    print(json.dumps(summary, indent=2, sort_keys=True))
    if any(summary["errors"]):
        raise SystemExit(1)
    if issues:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
