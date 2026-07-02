"""Validate that the SafeFlow scaffold is ready before feature work."""

from pathlib import Path
import json


REQUIRED_PATHS = [
    "AGENTS.md",
    ".env.example",
    "pyproject.toml",
    "app/main.py",
    "app/models/state.py",
    "app/models/extraction.py",
    "app/services/action_controller.py",
    "app/domains/support/tools.py",
    "app/registries/support_tools.yaml",
    "data/fixtures/support/support_refund_happy_001.json",
    "data/benchmark/support_demo.jsonl",
    "data/results/.gitkeep",
    "scripts/run_demo.py",
    "scripts/run_eval.py",
    "scripts/generate_synthetic_support_data.py",
    "scripts/build_demo_benchmark.py",
    "scripts/audit_test_data.py",
    "Dockerfile",
    "docker-compose.yml",
    "tests/unit/test_state_service.py",
    "ui/package.json",
    "ui/src/App.tsx",
]


def validate_required_paths() -> list[str]:
    missing = []
    for raw_path in REQUIRED_PATHS:
        if not Path(raw_path).exists():
            missing.append(raw_path)
    return missing


def validate_fixture() -> list[str]:
    errors = []
    fixture_path = Path("data/fixtures/support/support_refund_happy_001.json")
    if not fixture_path.exists():
        return ["missing support_refund_happy_001 fixture"]

    payload = json.loads(fixture_path.read_text(encoding="utf-8"))
    for key in ["fixture_id", "state", "expected_extraction"]:
        if key not in payload:
            errors.append(f"fixture missing `{key}`")
    return errors


def validate_benchmark() -> list[str]:
    errors = []
    benchmark_path = Path("data/benchmark/support_demo.jsonl")
    if not benchmark_path.exists():
        return ["missing support_demo.jsonl benchmark"]

    lines = [line for line in benchmark_path.read_text(encoding="utf-8").splitlines() if line]
    if not lines:
        errors.append("benchmark has no tasks")
    for index, line in enumerate(lines, start=1):
        try:
            task = json.loads(line)
        except json.JSONDecodeError as exc:
            errors.append(f"benchmark line {index} invalid JSON: {exc}")
            continue
        for key in ["task_id", "domain", "fixture_id", "request_text"]:
            if key not in task:
                errors.append(f"benchmark line {index} missing `{key}`")
    return errors


def main() -> None:
    errors = []
    missing = validate_required_paths()
    errors.extend(f"missing path: {path}" for path in missing)
    errors.extend(validate_fixture())
    errors.extend(validate_benchmark())

    if errors:
        print("SafeFlow setup check failed:")
        for error in errors:
            print(f"- {error}")
        raise SystemExit(1)

    print("SafeFlow setup check passed.")


if __name__ == "__main__":
    main()
