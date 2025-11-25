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
"""Plan validator abstraction for validating prompt engine output (AF v1.1).

The validator sits between the PromptEngine and response serialization,
ensuring candidate payloads meet structural requirements before being
sent to clients.
"""

from typing import Protocol, runtime_checkable

from planner_service.logging import get_logger
from planner_service.models import PlanningContext


class PlanValidationFailure(Exception):
    """Exception raised when plan validation fails.

    Carries machine-readable code and human-readable message for
    structured error responses.
    """

    def __init__(self, code: str, message: str) -> None:
        """Initialize the validation failure.

        Args:
            code: Machine-readable error code for programmatic handling.
            message: Human-readable error message for debugging.
        """
        super().__init__(message)
        self.code = code
        self.message = message


@runtime_checkable
class PlanValidator(Protocol):
    """Protocol defining the interface for plan validators.

    A plan validator is responsible for validating candidate payloads
    from the prompt engine before they are serialized and sent to clients.
    """

    def validate(self, ctx: PlanningContext, candidate_payload: object) -> dict:
        """Validate the candidate payload from the prompt engine.

        Args:
            ctx: The planning context for the current request.
            candidate_payload: The raw payload from the prompt engine.

        Returns:
            The validated payload as a dict, unchanged if valid.

        Raises:
            PlanValidationFailure: If the payload fails validation.
        """
        ...


class StubPlanValidator:
    """Stub implementation of PlanValidator enforcing basic structure.

    This validator ensures candidate payloads are dicts containing
    required keys (request_id and plan_version). It does not perform
    deep validation of field values beyond type checking.
    """

    def validate(self, ctx: PlanningContext, candidate_payload: object) -> dict:
        """Validate the candidate payload structure.

        Args:
            ctx: The planning context for the current request.
            candidate_payload: The raw payload from the prompt engine.

        Returns:
            The validated payload as a dict.

        Raises:
            PlanValidationFailure: If the payload is not a dict or
                is missing required keys.
        """
        # Check that candidate_payload is a dict
        if not isinstance(candidate_payload, dict):
            payload_type = type(candidate_payload).__name__
            raise PlanValidationFailure(
                code="INVALID_PAYLOAD_TYPE",
                message=f"Expected dict payload, got {payload_type}",
            )

        # Check for required keys
        if "request_id" not in candidate_payload:
            raise PlanValidationFailure(
                code="MISSING_REQUEST_ID",
                message="Payload missing required key: request_id",
            )

        if "plan_version" not in candidate_payload:
            raise PlanValidationFailure(
                code="MISSING_PLAN_VERSION",
                message="Payload missing required key: plan_version",
            )

        # Validate request_id is a string
        request_id = candidate_payload["request_id"]
        if not isinstance(request_id, str):
            request_id_type = type(request_id).__name__
            raise PlanValidationFailure(
                code="INVALID_REQUEST_ID_TYPE",
                message=f"request_id must be a string, got {request_id_type}",
            )

        # Validate plan_version is a string
        plan_version = candidate_payload["plan_version"]
        if not isinstance(plan_version, str):
            plan_version_type = type(plan_version).__name__
            raise PlanValidationFailure(
                code="INVALID_PLAN_VERSION_TYPE",
                message=f"plan_version must be a string, got {plan_version_type}",
            )

        return candidate_payload


def get_plan_validator() -> PlanValidator:
    """Factory function to get the appropriate plan validator.

    Attempts to import and use a private backend (af_plan_validator)
    if available, falling back to StubPlanValidator on ImportError.

    Returns:
        An instance of PlanValidator (either private backend or stub).
    """
    logger = get_logger(__name__)

    try:
        # Attempt to import private backend
        from af_plan_validator import PlanValidatorBackend  # type: ignore[import-not-found]

        logger.info("plan_validator_selected", validator="af_plan_validator")
        return PlanValidatorBackend()
    except ImportError:
        logger.info(
            "plan_validator_fallback",
            validator="stub",
            reason="af_plan_validator not available",
        )
        return StubPlanValidator()
