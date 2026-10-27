"""Anonymous metadata API only. No auth, session, quota, or AI execution routes."""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .models import Catalog, FoundationStatus, Liveness, Readiness
from .registry import CatalogRegistry, CatalogUnavailable, UNAVAILABLE_DETAIL
from .settings import Settings


def create_app(settings: Settings | None = None) -> FastAPI:
    configuration = settings if settings is not None else Settings.from_environment()
    registry = CatalogRegistry(configuration.catalog_path)
    application = FastAPI(
        title="Azure Foundry IRL — local catalog foundation",
        description="Synthetic public metadata only. Live demos are not deployed.",
        version="0.1.0",
        docs_url=None,
        redoc_url=None,
        openapi_url=None,
    )
    application.add_middleware(
        CORSMiddleware,
        allow_origins=list(configuration.allowed_origins),
        allow_credentials=False,
        allow_methods=["GET"],
        allow_headers=["Accept"],
    )

    @application.get("/healthz", response_model=Liveness)
    def healthz() -> Liveness:
        return Liveness()

    @application.get(
        "/readyz",
        response_model=Readiness,
        response_model_exclude_none=True,
        responses={503: {"model": Readiness}},
    )
    def readyz() -> Readiness | JSONResponse:
        try:
            registry.load()
        except CatalogUnavailable:
            return JSONResponse(
                status_code=503,
                content=Readiness(
                    status="not_ready",
                    detail=UNAVAILABLE_DETAIL,
                ).model_dump(exclude_none=True),
            )
        return Readiness(status="ready")

    @application.get("/api/catalog", response_model=Catalog)
    def catalog() -> Catalog:
        try:
            return registry.load()
        except CatalogUnavailable as exc:
            raise HTTPException(status_code=503, detail=UNAVAILABLE_DETAIL) from exc

    @application.get("/api/status", response_model=FoundationStatus)
    def status() -> FoundationStatus:
        return FoundationStatus()

    return application


app = create_app()
