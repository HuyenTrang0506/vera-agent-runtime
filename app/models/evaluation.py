"""Evaluation task and metric contracts."""

from pydantic import BaseModel, Field


class BenchmarkTask(BaseModel):
    task_id: str
    domain: str
    fixture_id: str
    request_text: str
    failure_mode: str | None = None
    expected_final_predicates: list[str] = Field(default_factory=list)
    forbidden_predicates: list[str] = Field(default_factory=list)

