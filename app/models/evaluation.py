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
    # Explicit approval intent — avoids inferring from fixture naming convention.
    # approval_script already controls the injected ApprovalRecord; these flags
    # tell the metrics layer whether to score approval recall / rejection compliance.
    expects_approval: bool | None = None
    expects_rejection_compliance: bool | None = None

