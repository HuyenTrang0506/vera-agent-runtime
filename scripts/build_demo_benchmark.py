"""Build a balanced 20-case P0 demo benchmark from a larger benchmark."""

from argparse import ArgumentParser
from collections import defaultdict
import json
from pathlib import Path

from audit_test_data import REQUIRED_SCENARIOS, scenario_for


def load_jsonl(path: Path) -> list[dict]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def main() -> None:
    parser = ArgumentParser()
    parser.add_argument("--source", default="data/benchmark/support_large_120.jsonl")
    parser.add_argument("--output", default="data/benchmark/support_demo.jsonl")
    args = parser.parse_args()

    grouped: dict[str, list[dict]] = defaultdict(list)
    for task in load_jsonl(Path(args.source)):
        grouped[scenario_for(task)].append(task)

    selected = []
    for scenario, count in REQUIRED_SCENARIOS.items():
        candidates = grouped.get(scenario, [])
        if len(candidates) < count:
            raise SystemExit(f"Not enough `{scenario}` tasks: have {len(candidates)}, need {count}")
        selected.extend(candidates[:count])

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8") as handle:
        for task in selected:
            handle.write(json.dumps(task, sort_keys=True) + "\n")

    print({"source": args.source, "output": args.output, "tasks": len(selected)})


if __name__ == "__main__":
    main()
