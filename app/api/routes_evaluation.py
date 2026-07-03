"""Evaluation API routes."""

from __future__ import annotations

import time
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.core.config import settings
from app.eval.runner import run_benchmark

router = APIRouter(prefix="/evaluation", tags=["evaluation"])

_eval_store: dict[str, dict[str, Any]] = {}


class EvalRunRequest(BaseModel):
    benchmark_path: str | None = None
    repeated_runs: int | None = None
    include_baseline: bool = False


class EvalRunResponse(BaseModel):
    run_id: str
    status: str
    benchmark_path: str
    repeated_runs: int
    metrics: dict[str, Any]
    repeated_run_summary: dict[str, Any]
    tasks: list[dict[str, Any]]


@router.post("/run", response_model=EvalRunResponse)
def run_evaluation(request: EvalRunRequest | None = None) -> EvalRunResponse:
    benchmark_path = (request.benchmark_path if request else None) or settings.benchmark_path
    repeated_runs = (request.repeated_runs if request else None)

    try:
        result = run_benchmark(benchmark_path, repeated_runs=repeated_runs)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    run_id = f"eval_{int(time.time() * 1000)}"
    result["run_id"] = run_id
    _eval_store[run_id] = result

    return EvalRunResponse(
        run_id=run_id,
        status="completed",
        benchmark_path=result["benchmark_path"],
        repeated_runs=result["repeated_runs"],
        metrics=result["metrics"],
        repeated_run_summary=result["repeated_run_summary"],
        tasks=result["tasks"],
    )


@router.get("/{run_id}", response_model=EvalRunResponse)
def get_evaluation(run_id: str) -> EvalRunResponse:
    stored = _eval_store.get(run_id)
    if stored is None:
        raise HTTPException(status_code=404, detail=f"Evaluation run {run_id!r} not found")
    return EvalRunResponse(
        run_id=run_id,
        status="completed",
        benchmark_path=stored["benchmark_path"],
        repeated_runs=stored["repeated_runs"],
        metrics=stored["metrics"],
        repeated_run_summary=stored["repeated_run_summary"],
        tasks=stored["tasks"],
    )
