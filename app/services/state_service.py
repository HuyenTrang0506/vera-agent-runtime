"""State loading, snapshotting, and hashing."""

from hashlib import sha256
import json
from pathlib import Path
from typing import Any

from pydantic import BaseModel

from app.core.config import settings
from app.models.finance import FinanceFixture
from app.models.state import SupportFixture, SupportState
from app.models.workflow import WorkflowRunResult


def load_fixture(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def support_fixture_path(fixture: str | Path) -> Path:
    path = Path(fixture)
    if path.suffix == ".json" or path.exists():
        return path

    support_path = Path(settings.fixtures_dir) / "support" / f"{fixture}.json"
    if support_path.exists():
        return support_path

    generated_path = Path(settings.fixtures_dir) / "support_generated" / f"{fixture}.json"
    if generated_path.exists():
        return generated_path

    return support_path


def load_support_fixture(fixture: str | Path) -> SupportFixture:
    path = support_fixture_path(fixture)
    payload = load_fixture(path)
    return SupportFixture.model_validate(payload)


def finance_fixture_path(fixture: str | Path) -> Path:
    path = Path(fixture)
    if path.suffix == ".json" or path.exists():
        return path
    return Path(settings.fixtures_dir) / "finance" / f"{fixture}.json"


def load_finance_fixture(fixture: str | Path) -> FinanceFixture:
    path = finance_fixture_path(fixture)
    payload = load_fixture(path)
    return FinanceFixture.model_validate(payload)


def runtime_state_from_fixture(fixture: SupportFixture) -> SupportState:
    return fixture.state.model_copy(deep=True)


def snapshot_state(state: SupportState | BaseModel | dict[str, Any]) -> dict[str, Any]:
    if isinstance(state, dict):
        return json.loads(json.dumps(state))
    return state.model_dump(mode="json")


def state_hash(state: SupportState | BaseModel | dict[str, Any]) -> str:
    encoded = json.dumps(snapshot_state(state), sort_keys=True, separators=(",", ":")).encode(
        "utf-8"
    )
    return sha256(encoded).hexdigest()


def workflow_result_path(workflow_id: str) -> Path:
    return Path(settings.results_dir) / f"{workflow_id}.json"


def save_workflow_result(result: WorkflowRunResult) -> Path:
    results_dir = Path(settings.results_dir)
    results_dir.mkdir(parents=True, exist_ok=True)
    path = workflow_result_path(result.workflow_id)
    path.write_text(
        json.dumps(result.model_dump(mode="json"), indent=2, sort_keys=True),
        encoding="utf-8",
    )
    return path


def load_workflow_result(workflow_id: str) -> WorkflowRunResult | None:
    path = workflow_result_path(workflow_id)
    if not path.exists():
        return None
    return WorkflowRunResult.model_validate_json(path.read_text(encoding="utf-8"))
