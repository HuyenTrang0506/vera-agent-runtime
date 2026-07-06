"""Load YAML tool registries into ToolMetadata objects."""

from pathlib import Path

import yaml

from app.models.tools import ToolMetadata


def load_tool_registry(yaml_path: str | Path) -> dict[str, ToolMetadata]:
    data = yaml.safe_load(Path(yaml_path).read_text())
    return {name: ToolMetadata(name=name, **spec) for name, spec in data.items()}
