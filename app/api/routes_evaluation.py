"""Evaluation API routes."""

from __future__ import annotations

import time
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.core.config import settings
from app.eval.baselines import run_description_only_baseline
from app.eval.runner import run_benchmark


def _comparison_table(sf: dict, bl: dict) -> dict:
    rows: dict = {}
    sf_m = sf.get("metrics", {})
    bl_m = bl.get("metrics", {})
    for key in sf_m:
        sv, bv = sf_m[key], bl_m.get(key)
        if bv is None:
            continue
        if isinstance(sv, float) and isinstance(bv, float):
            rows[key] = {"safeflow": sv, "baseline": bv, "delta": round(sv - bv, 4)}
        else:
            rows[key] = {"safeflow": sv, "baseline": bv}
    sf_pk, bl_pk = sf.get("pass_k"), bl.get("pass_k")
    if sf_pk is not None and bl_pk is not None:
        rows["pass_k"] = {"safeflow": sf_pk, "baseline": bl_pk, "delta": round(sf_pk - bl_pk, 4)}
    return rows

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
    pass_k: float | None = None
    metrics: dict[str, Any]
    repeated_run_summary: dict[str, Any]
    tasks: list[dict[str, Any]]
    comparison: dict[str, Any] | None = None


@router.post("/run", response_model=EvalRunResponse)
def run_evaluation(request: EvalRunRequest | None = None) -> EvalRunResponse:
    benchmark_path = (request.benchmark_path if request else None) or settings.benchmark_path
    repeated_runs = (request.repeated_runs if request else None)

    include_baseline = request.include_baseline if request else False

    try:
        result = run_benchmark(benchmark_path, repeated_runs=repeated_runs)
        if include_baseline:
            baseline = run_description_only_baseline(
                benchmark_path, repeated_runs=repeated_runs or 1
            )
            result["baseline"] = baseline
            result["comparison"] = _comparison_table(result, baseline)
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
        pass_k=result.get("pass_k"),
        metrics=result["metrics"],
        repeated_run_summary=result["repeated_run_summary"],
        tasks=result["tasks"],
        comparison=result.get("comparison"),
    )


@router.get("/latest", response_model=EvalRunResponse | None)
def get_latest_evaluation() -> EvalRunResponse | None:
    if not _eval_store:
        return None
    run_id = max(_eval_store, key=lambda k: _eval_store[k].get("run_id", k))
    stored = _eval_store[run_id]
    return EvalRunResponse(
        run_id=run_id,
        status="completed",
        benchmark_path=stored["benchmark_path"],
        repeated_runs=stored["repeated_runs"],
        pass_k=stored.get("pass_k"),
        metrics=stored["metrics"],
        repeated_run_summary=stored["repeated_run_summary"],
        tasks=stored["tasks"],
        comparison=stored.get("comparison"),
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
        pass_k=stored.get("pass_k"),
        metrics=stored["metrics"],
        repeated_run_summary=stored["repeated_run_summary"],
        tasks=stored["tasks"],
        comparison=stored.get("comparison"),
    )
