"""Run SafeFlow evaluation benchmark."""

from argparse import ArgumentParser
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def main() -> None:
    from app.eval.runner import run_benchmark

    parser = ArgumentParser()
    parser.add_argument("--benchmark", required=True)
    parser.add_argument("--repeated-runs", type=int, default=None)
    args = parser.parse_args()
    result = run_benchmark(args.benchmark, repeated_runs=args.repeated_runs)
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
