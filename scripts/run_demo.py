"""Run a deterministic SafeFlow demo fixture."""

from argparse import ArgumentParser
import json

from app.services.action_controller import run_support_workflow


def main() -> None:
    parser = ArgumentParser()
    parser.add_argument("--fixture", required=True)
    parser.add_argument("--request-text", default=None)
    args = parser.parse_args()
    result = run_support_workflow(fixture_id=args.fixture, request_text=args.request_text)
    print(json.dumps(result.model_dump(mode="json"), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
