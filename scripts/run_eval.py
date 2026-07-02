"""Run SafeFlow evaluation benchmark."""

from argparse import ArgumentParser
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def main() -> None:
    from app.eval.runner import run_benchmark

    parser = ArgumentParser()
    parser.add_argument("--benchmark", required=True)
    args = parser.parse_args()
    print(run_benchmark(args.benchmark))


if __name__ == "__main__":
    main()
