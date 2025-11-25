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
"""Pydantic models for the planner service contract."""

from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class RepositoryPointer(BaseModel):
    """Reference to a specific repository location."""

    owner: str = Field(..., description="Repository owner (user or organization)")
    repo: str = Field(..., description="Repository name")
    ref: Optional[str] = Field(
        None, description="Git ref (branch, tag, or commit SHA)"
    )


class UserInput(BaseModel):
    """User-provided input for the planning request."""

    query: str = Field(..., description="The user's planning query or request")
    context: Optional[str] = Field(
        None, description="Additional context provided by the user"
    )


class ProjectContext(BaseModel):
    """Context about the project being planned."""

    repository: RepositoryPointer
    default_branch: Optional[str] = Field(
        None, description="Default branch of the repository"
    )
    languages: Optional[list[str]] = Field(
        None, description="Primary programming languages in the repository"
    )


class PlanningContext(BaseModel):
    """Full context for a planning operation."""

    project: ProjectContext
    user_input: UserInput
    session_id: Optional[str] = Field(
        None, description="Session identifier for tracking related requests"
    )


class PlanRequest(BaseModel):
    """Request model for the /v1/plan endpoint."""

    repository: RepositoryPointer
    user_input: UserInput
    request_id: Optional[UUID] = Field(
        None,
        description="Client-provided request ID for idempotency and tracking",
    )


class PlanStep(BaseModel):
    """A single step in a generated plan."""

    step_number: int = Field(..., description="Order of this step in the plan")
    description: str = Field(..., description="Description of what this step does")
    rationale: Optional[str] = Field(
        None, description="Explanation of why this step is needed"
    )


class PlanResponse(BaseModel):
    """Response model for a successful plan generation."""

    request_id: UUID = Field(
        ..., description="Request ID (echoed from request or server-generated)"
    )
    run_id: UUID = Field(
        ..., description="Unique identifier for this planning run"
    )
    status: str = Field(
        default="pending", description="Status of the planning operation"
    )
    steps: Optional[list[PlanStep]] = Field(
        None, description="Generated plan steps (when status is 'completed')"
    )


class ErrorDetail(BaseModel):
    """Detailed error information."""

    code: str = Field(..., description="Error code for programmatic handling")
    message: str = Field(..., description="Human-readable error message")
    field: Optional[str] = Field(
        None, description="Field that caused the error, if applicable"
    )


class ErrorResponse(BaseModel):
    """Response model for error cases."""

    error: ErrorDetail
    request_id: Optional[UUID] = Field(
        None,
        description="Request ID if available (omitted for validation errors)",
    )


class HealthResponse(BaseModel):
    """Response model for health check endpoint."""

    status: str = Field(..., description="Health status (healthy/unhealthy)")
    service: str = Field(..., description="Service name")
    version: str = Field(..., description="Service version")
