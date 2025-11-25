# ============================================================
# SPDX-License-Identifier: GPL-3.0-or-later
# This program was generated as part of the AgentFoundry project.
# Copyright (C) 2025  John Brosnihan
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
# ============================================================
"""FastAPI application for the planner service."""

import os
from contextlib import asynccontextmanager
from typing import AsyncGenerator
from uuid import uuid4

from fastapi import Depends, FastAPI, Header, HTTPException, Request
from fastapi.responses import JSONResponse

from planner_service import __version__
from planner_service.auth import AuthContext, get_current_user
from planner_service.context_driver import get_context_driver
from planner_service.logging import configure_logging, get_logger
from planner_service.models import (
    ErrorDetail,
    ErrorResponse,
    HealthResponse,
    PlanningContext,
    PlanRequest,
    PlanResponse,
    ProjectContext,
    RepositoryPointer,
)
from planner_service.prompt_engine import get_prompt_engine


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
    # Generate a request_id for error tracking
    error_request_id = uuid4()
    error_response = ErrorResponse(
        error=ErrorDetail(
            code=f"HTTP_{exc.status_code}",
            message=str(exc.detail),
        ),
        request_id=error_request_id,
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


@app.get("/healthz", response_model=HealthResponse, tags=["health"])
async def healthz() -> HealthResponse:
    """Kubernetes-style health check endpoint.

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
async def create_plan(
    request: PlanRequest,
    auth: AuthContext = Depends(get_current_user),
) -> PlanResponse | JSONResponse:
    """Create a new planning request.

    This endpoint accepts a planning request, fetches repository context,
    invokes the prompt engine, and returns a plan response with tracking identifiers.

    Args:
        request: The plan request containing repository and user input.
        auth: The authentication context from the current user.

    Returns:
        A PlanResponse with request_id, run_id, and status on success.
        JSONResponse with structured error (including request_id only) on failure.
    """
    logger = get_logger(__name__)

    # Use provided request_id or generate a new one
    request_id = request.request_id or uuid4()
    repo_str = f"{request.repository.owner}/{request.repository.repo}"

    logger.info(
        "plan_request_received",
        request_id=str(request_id),
        repository=repo_str,
        repo_owner=request.repository.owner,
        repo_name=request.repository.repo,
        repo_ref=request.repository.ref,
        user_id=auth.user_id,
        outcome="pending",
    )

    # Step 1: Fetch context using context driver
    try:
        driver = get_context_driver()
        project_context = driver.fetch_context(request.repository)
    except FileNotFoundError as e:
        logger.error(
            "plan_request_context_failure",
            request_id=str(request_id),
            repository=repo_str,
            repo_owner=request.repository.owner,
            repo_name=request.repository.repo,
            repo_ref=request.repository.ref,
            user_id=auth.user_id,
            error=str(e),
            outcome="failure",
        )
        error_response = ErrorResponse(
            error=ErrorDetail(
                code="CONTEXT_DRIVER_ERROR",
                message=f"Failed to fetch repository context: {e}",
            ),
            request_id=request_id,
        )
        return JSONResponse(
            status_code=500,
            content=error_response.model_dump(mode="json", exclude_none=True),
        )
    except Exception as e:
        logger.error(
            "plan_request_context_failure",
            request_id=str(request_id),
            repository=repo_str,
            repo_owner=request.repository.owner,
            repo_name=request.repository.repo,
            repo_ref=request.repository.ref,
            user_id=auth.user_id,
            error=str(e),
            outcome="failure",
        )
        error_response = ErrorResponse(
            error=ErrorDetail(
                code="CONTEXT_DRIVER_ERROR",
                message=f"Unexpected error fetching context: {e}",
            ),
            request_id=request_id,
        )
        return JSONResponse(
            status_code=500,
            content=error_response.model_dump(mode="json", exclude_none=True),
        )

    # Step 2: Build PlanningContext
    planning_context = PlanningContext(
        project=project_context,
        user_input=request.user_input,
        session_id=str(request_id),
    )

    # Step 3: Invoke prompt engine
    try:
        prompt_engine = get_prompt_engine()
        engine_result = prompt_engine.run(planning_context)
    except Exception as e:
        logger.error(
            "plan_request_engine_failure",
            request_id=str(request_id),
            repository=repo_str,
            repo_owner=request.repository.owner,
            repo_name=request.repository.repo,
            repo_ref=request.repository.ref,
            user_id=auth.user_id,
            error=str(e),
            outcome="failure",
        )
        error_response = ErrorResponse(
            error=ErrorDetail(
                code="PROMPT_ENGINE_ERROR",
                message=f"Plan generation failed: {e}",
            ),
            request_id=request_id,
        )
        return JSONResponse(
            status_code=500,
            content=error_response.model_dump(mode="json", exclude_none=True),
        )

    # Step 4: Generate run_id (mirrors request_id for synchronous flow)
    run_id = request_id

    # Determine status from engine result
    engine_status = engine_result.get("status", "pending")
    status = "completed" if engine_status == "success" else engine_status

    # Determine outcome based on the computed status
    outcome = "success" if status == "completed" else "failure"

    logger.info(
        "plan_request_completed",
        request_id=str(request_id),
        run_id=str(run_id),
        repository=repo_str,
        repo_owner=request.repository.owner,
        repo_name=request.repository.repo,
        repo_ref=request.repository.ref,
        user_id=auth.user_id,
        outcome=outcome,
        status=status,
    )

    return PlanResponse(
        request_id=request_id,
        run_id=run_id,
        status=status,
        steps=None,
    )


# Stub authorization token for debug endpoint
DEBUG_AUTH_TOKEN = os.environ.get("DEBUG_AUTH_TOKEN", "debug-token-stub")


def _verify_debug_auth(authorization: str | None) -> None:
    """Verify authorization for debug endpoints.

    Args:
        authorization: The Authorization header value.

    Raises:
        HTTPException: If authorization is missing or invalid.
    """
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header required")

    # Expected format: "Bearer <token>"
    parts = authorization.split(" ", 1)
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(status_code=401, detail="Invalid authorization format")

    if parts[1] != DEBUG_AUTH_TOKEN:
        raise HTTPException(status_code=403, detail="Invalid token")


@app.post("/v1/debug/context", response_model=ProjectContext, tags=["debug"])
async def debug_context(
    repository: RepositoryPointer,
    authorization: str | None = Header(None),
) -> ProjectContext | JSONResponse:
    """Debug endpoint to fetch repository context.

    This endpoint uses the configured context driver to return
    ProjectContext for a given repository. Protected by auth stub.

    Args:
        repository: The repository to fetch context for.
        authorization: Bearer token for authentication.

    Returns:
        ProjectContext for the specified repository on success.
        JSONResponse with structured error (including request_id, no run_id)
        if fixtures are missing.
    """
    _verify_debug_auth(authorization)

    logger = get_logger(__name__)
    request_id = uuid4()

    logger.debug(
        "debug_context_request",
        request_id=str(request_id),
        repository=f"{repository.owner}/{repository.repo}",
    )

    driver = get_context_driver()
    try:
        return driver.fetch_context(repository)
    except FileNotFoundError as e:
        logger.error(
            "debug_context_fixture_missing",
            request_id=str(request_id),
            error=str(e),
        )
        error_response = ErrorResponse(
            error=ErrorDetail(
                code="FIXTURE_NOT_FOUND",
                message=str(e),
            ),
            request_id=request_id,
        )
        return JSONResponse(
            status_code=500,
            content=error_response.model_dump(mode="json", exclude_none=True),
        )
