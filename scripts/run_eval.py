"""Run SafeFlow evaluation benchmark."""

from argparse import ArgumentParser
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def main() -> None:
    from app.eval.baselines import run_description_only_baseline
    from app.eval.runner import run_benchmark

    parser = ArgumentParser()
    parser.add_argument("--benchmark", required=True)
    parser.add_argument("--repeated-runs", type=int, default=None)
    parser.add_argument("--include-baseline", action="store_true")
    args = parser.parse_args()
    result = run_benchmark(args.benchmark, repeated_runs=args.repeated_runs)
    if args.include_baseline:
        result["baseline"] = run_description_only_baseline(
            args.benchmark,
            repeated_runs=args.repeated_runs or 1,
        )
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
