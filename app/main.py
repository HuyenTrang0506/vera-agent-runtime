"""FastAPI entrypoint for SafeFlow."""

from fastapi import FastAPI

from app.api.routes_approvals import router as approvals_router
from app.api.routes_audit import router as audit_router
from app.api.routes_evaluation import router as evaluation_router
from app.api.routes_workflows import router as workflows_router


def create_app() -> FastAPI:
    app = FastAPI(title="SafeFlow", version="0.1.0")
    app.include_router(workflows_router)
    app.include_router(approvals_router)
    app.include_router(audit_router)
    app.include_router(evaluation_router)
    return app


app = create_app()
