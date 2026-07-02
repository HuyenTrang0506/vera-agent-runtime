"""State loading, snapshotting, and hashing."""

from hashlib import sha256
import json
from pathlib import Path
from typing import Any

from pydantic import BaseModel

from app.core.config import settings
from app.models.state import SupportFixture, SupportState


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
