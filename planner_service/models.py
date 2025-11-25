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
"""Pydantic models for the planner service contract (AF v1.1)."""

from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, StrictStr, ValidationInfo, field_validator


def _validate_non_empty_string(value: str, field_name: str = "field") -> str:
    """Validate that a string is non-empty and not whitespace-only.

    Args:
        value: String to validate.
        field_name: Name of the field being validated for error messages.

    Returns:
        The validated string.

    Raises:
        ValueError: If the string is empty or contains only whitespace.
    """
    if not value or not value.strip():
        raise ValueError(f"'{field_name}' must be a non-empty string")
    return value


def _validate_non_empty_strings(value: list[str], field_name: str = "list") -> list[str]:
    """Validate that a list contains only non-empty, non-whitespace strings.

    Args:
        value: List of strings to validate.
        field_name: Name of the field being validated for error messages.

    Returns:
        The validated list.

    Raises:
        ValueError: If any string is empty or contains only whitespace.
    """
    for i, item in enumerate(value):
        if not item or not item.strip():
            raise ValueError(
                f"'{field_name}' item at index {i} must be a non-empty string"
            )
    return value


class RepositoryPointer(BaseModel):
    """Reference to a specific repository location (AF v1.1).

    The canonical coordinate for a repository consists of owner, name, and ref.
    """

    model_config = ConfigDict(extra="forbid")

    owner: str = Field(..., description="Repository owner (user or organization)")
    name: str = Field(..., description="Repository name")
    ref: str = Field(
        default="refs/heads/main",
        description="Git ref (branch, tag, or commit SHA)",
    )


class UserInput(BaseModel):
    """User-provided input for the planning request (AF v1.1).

    Enforces exactly five keys with strict typing and validation for string lists.
    Uses StrictStr to reject non-string values without coercion.
    """

    model_config = ConfigDict(extra="forbid")

    purpose: str = Field(
        ..., description="The purpose or goal of the planning request"
    )
    vision: str = Field(
        ..., description="The desired end state or vision for the project"
    )
    must: list[StrictStr] = Field(
        ..., description="List of requirements that must be fulfilled"
    )
    dont: list[StrictStr] = Field(
        ..., description="List of constraints or things to avoid"
    )
    nice: list[StrictStr] = Field(
        ..., description="List of nice-to-have features or improvements"
    )

    @field_validator("purpose", "vision")
    @classmethod
    def validate_string_fields(cls, v: str, info: ValidationInfo) -> str:
        """Validate that string fields are non-empty."""
        return _validate_non_empty_string(v, info.field_name)

    @field_validator("must", "dont", "nice")
    @classmethod
    def validate_string_lists(cls, v: list[str], info: ValidationInfo) -> list[str]:
        """Validate that list entries are non-empty strings."""
        return _validate_non_empty_strings(v, info.field_name)


class ProjectContext(BaseModel):
    """Internal artifact carrier for project context (AF v1.1).

    Contains repository coordinates and optional artifact JSON strings.
    Decoupled from request types for internal runtime use.
    """

    model_config = ConfigDict(extra="forbid")

    repo_owner: str = Field(..., description="Repository owner (user or organization)")
    repo_name: str = Field(..., description="Repository name")
    ref: str = Field(
        default="refs/heads/main",
        description="Git ref (branch, tag, or commit SHA)",
    )
    tree_json: Optional[str] = Field(
        None, description="JSON string containing repository tree structure"
    )
    dependency_json: Optional[str] = Field(
        None, description="JSON string containing dependency information"
    )
    summary_json: Optional[str] = Field(
        None, description="JSON string containing repository summary"
    )


class PlanningContext(BaseModel):
    """Full context for a planning operation (AF v1.1).

    Links request_id, UserInput, and a list of ProjectContext entries.
    """

    model_config = ConfigDict(extra="forbid")

    request_id: UUID = Field(
        ..., description="Request identifier for tracking"
    )
    user_input: UserInput = Field(..., description="User's planning input")
    projects: list[ProjectContext] = Field(
        ..., description="List of project contexts for planning"
    )


class PlanRequest(BaseModel):
    """Request model for the /v1/plan endpoint (AF v1.1)."""

    model_config = ConfigDict(extra="forbid")

    repository: RepositoryPointer = Field(..., description="Target repository")
    user_input: UserInput = Field(..., description="User's planning input")
    request_id: Optional[UUID] = Field(
        None,
        description="Client-provided request ID for idempotency and tracking",
    )


class PlanStep(BaseModel):
    """A single step in a generated plan."""

    model_config = ConfigDict(extra="forbid")

    step_number: int = Field(..., description="Order of this step in the plan")
    description: str = Field(..., description="Description of what this step does")
    rationale: Optional[str] = Field(
        None, description="Explanation of why this step is needed"
    )


class PlanResponse(BaseModel):
    """Response model for a successful plan generation (AF v1.1).

    Includes status/payload/run_id rules per the stricter contract.
    """

    model_config = ConfigDict(extra="forbid")

    request_id: UUID = Field(
        ..., description="Request ID (echoed from request or server-generated)"
    )
    run_id: UUID = Field(
        ..., description="Unique identifier for this planning run"
    )
    status: str = Field(
        default="pending", description="Status of the planning operation"
    )
    payload: Optional[dict] = Field(
        None, description="Plan payload (when status is 'completed')"
    )


class ErrorDetail(BaseModel):
    """Detailed error information."""

    model_config = ConfigDict(extra="forbid")

    code: str = Field(..., description="Error code for programmatic handling")
    message: str = Field(..., description="Human-readable error message")
    field: Optional[str] = Field(
        None, description="Field that caused the error, if applicable"
    )


class ErrorResponse(BaseModel):
    """Response model for error cases (AF v1.1).

    Error responses include request_id but omit run_id to indicate no run was created.
    """

    model_config = ConfigDict(extra="forbid")

    error: ErrorDetail
    request_id: UUID = Field(
        ...,
        description="Request ID (echoed from request or server-generated)",
    )


class HealthResponse(BaseModel):
    """Response model for health check endpoint."""

    model_config = ConfigDict(extra="forbid")

    status: str = Field(..., description="Health status (healthy/unhealthy)")
    service: str = Field(..., description="Service name")
    version: str = Field(..., description="Service version")
