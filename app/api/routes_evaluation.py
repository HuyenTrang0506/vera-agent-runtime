"""Evaluation API routes."""

from fastapi import APIRouter

router = APIRouter(prefix="/evaluation", tags=["evaluation"])


@router.post("/run")
def run_evaluation() -> dict[str, str]:
    return {"run_id": "eval_placeholder", "status": "not_implemented"}


@router.get("/{run_id}")
def get_evaluation(run_id: str) -> dict[str, str]:
    return {"run_id": run_id, "status": "not_implemented"}

