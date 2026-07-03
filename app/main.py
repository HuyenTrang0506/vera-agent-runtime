"""FastAPI entrypoint for SafeFlow."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes_approvals import router as approvals_router
from app.api.routes_audit import router as audit_router
from app.api.routes_evaluation import router as evaluation_router
from app.api.routes_workflows import router as workflows_router
from app.core.config import settings


def create_app() -> FastAPI:
    app = FastAPI(title="VERA", version="0.1.0")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(settings.cors_origins),
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(workflows_router)
    app.include_router(approvals_router)
    app.include_router(audit_router)
    app.include_router(evaluation_router)
    return app


app = create_app()
