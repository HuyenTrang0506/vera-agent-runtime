"""State loading, snapshotting, and hashing."""

from hashlib import sha256
import json
from pathlib import Path
from typing import Any


def load_fixture(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def state_hash(state: dict[str, Any]) -> str:
    encoded = json.dumps(state, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return sha256(encoded).hexdigest()

