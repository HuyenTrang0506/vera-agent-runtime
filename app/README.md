# App Structure

SafeFlow backend code lives here.

- `api/`: FastAPI route boundary.
- `core/`: env-backed config, IDs, logging.
- `models/`: Pydantic contracts and enums.
- `services/`: shared workflow, policy, state, audit, and evaluation services.
- `domains/support/`: P0 customer-support domain tools and workflows.
- `registries/`: tool metadata.
- `eval/`: metrics, baselines, benchmark runner, reports.

See `docs/development/code_structure.md` before adding new modules.

