"""FastAPI application for the planner service."""

from contextlib import asynccontextmanager
from typing import AsyncGenerator
from uuid import uuid4

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse

from planner_service import __version__
from planner_service.logging import configure_logging, get_logger
from planner_service.models import (
    ErrorDetail,
    ErrorResponse,
    HealthResponse,
    PlanRequest,
    PlanResponse,
)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan handler for startup/shutdown events."""
    configure_logging()
    logger = get_logger(__name__)
    logger.info("planner_service_starting", version=__version__)
    yield
    logger.info("planner_service_shutting_down")


app = FastAPI(
    title="Planner Service",
    description="FastAPI planner service for Agent Foundry",
    version=__version__,
    lifespan=lifespan,
)


@app.exception_handler(HTTPException)
async def http_exception_handler(
    request: Request, exc: HTTPException
) -> JSONResponse:
    """Handle HTTP exceptions with structured error response."""
    error_response = ErrorResponse(
        error=ErrorDetail(
            code=f"HTTP_{exc.status_code}",
            message=str(exc.detail),
        ),
        request_id=None,
    )
    return JSONResponse(
        status_code=exc.status_code,
        content=error_response.model_dump(mode="json", exclude_none=True),
    )


@app.get("/health", response_model=HealthResponse, tags=["health"])
async def health_check() -> HealthResponse:
    """Health check endpoint for Cloud Run.

    Returns service health status. Always returns healthy status
    to ensure the endpoint is available even when downstream
    services are unavailable.
    """
    return HealthResponse(
        status="healthy",
        service="planner-service",
        version=__version__,
    )


@app.post("/v1/plan", response_model=PlanResponse, tags=["planning"])
async def create_plan(request: PlanRequest) -> PlanResponse:
    """Create a new planning request.

    This endpoint accepts a planning request and returns a pending
    plan response with request and run identifiers for tracking.

    Args:
        request: The plan request containing repository and user input.

    Returns:
        A PlanResponse with request_id, run_id, and pending status.
    """
    logger = get_logger(__name__)

    # Use provided request_id or generate a new one
    request_id = request.request_id or uuid4()
    run_id = uuid4()

    logger.info(
        "plan_request_received",
        request_id=str(request_id),
        run_id=str(run_id),
        repository=f"{request.repository.owner}/{request.repository.repo}",
    )

    # Return pending response (business logic not implemented yet)
    return PlanResponse(
        request_id=request_id,
        run_id=run_id,
        status="pending",
        steps=None,
    )
