# Scripts

CLI utilities for setup, data generation, audit, demo, and evaluation.

- `check_setup.py`: scaffold readiness check.
- `generate_synthetic_support_data.py`: synthetic fixture and benchmark generator.
- `build_demo_benchmark.py`: balanced demo benchmark builder.
- `audit_test_data.py`: benchmark quality audit.
- `run_demo.py`: demo runner.
- `run_eval.py`: evaluation runner.
- `seed_fixtures.py`: fixture seed placeholder.

Scripts should call `app/` modules where possible and must not duplicate core business logic.

