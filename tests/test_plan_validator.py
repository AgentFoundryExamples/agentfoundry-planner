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
"""Tests for plan validator abstraction and stub implementation (AF v1.1)."""

from uuid import uuid4

import pytest

from planner_service.models import (
    PlanningContext,
    ProjectContext,
    UserInput,
)
from planner_service.plan_validator import (
    PlanValidationFailure,
    PlanValidator,
    StubPlanValidator,
)


@pytest.fixture
def sample_planning_context() -> PlanningContext:
    """Create a sample planning context for tests (AF v1.1)."""
    return PlanningContext(
        request_id=uuid4(),
        user_input=UserInput(
            purpose="Create a new feature for user authentication",
            vision="A fully functional auth system",
            must=["Implement login", "Implement logout"],
            dont=["Use deprecated APIs"],
            nice=["Add remember me feature"],
        ),
        projects=[
            ProjectContext(
                repo_owner="test-owner",
                repo_name="test-repo",
                ref="refs/heads/main",
            ),
        ],
    )


@pytest.fixture
def valid_payload() -> dict:
    """Create a valid payload for tests."""
    return {
        "request_id": str(uuid4()),
        "plan_version": "1.0.0",
        "status": "success",
    }


class TestPlanValidationFailure:
    """Tests for the PlanValidationFailure exception."""

    def test_carries_code_and_message(self) -> None:
        """PlanValidationFailure carries code and message attributes."""
        exc = PlanValidationFailure(code="TEST_CODE", message="Test message")

        assert exc.code == "TEST_CODE"
        assert exc.message == "Test message"

    def test_inherits_from_exception(self) -> None:
        """PlanValidationFailure inherits from Exception."""
        exc = PlanValidationFailure(code="TEST_CODE", message="Test message")

        assert isinstance(exc, Exception)

    def test_str_representation_is_message(self) -> None:
        """PlanValidationFailure string representation is the message."""
        exc = PlanValidationFailure(code="TEST_CODE", message="Test message")

        assert str(exc) == "Test message"

    def test_can_be_raised_and_caught(self) -> None:
        """PlanValidationFailure can be raised and caught."""
        with pytest.raises(PlanValidationFailure) as exc_info:
            raise PlanValidationFailure(code="RAISED_CODE", message="Raised message")

        assert exc_info.value.code == "RAISED_CODE"
        assert exc_info.value.message == "Raised message"

    def test_unknown_code_serializes_predictably(self) -> None:
        """Unknown codes still serialize predictably."""
        exc = PlanValidationFailure(
            code="UNKNOWN_CUSTOM_CODE",
            message="Some unknown error occurred",
        )

        # Should be able to serialize the code and message to a dict
        error_dict = {"code": exc.code, "message": exc.message}
        assert error_dict["code"] == "UNKNOWN_CUSTOM_CODE"
        assert error_dict["message"] == "Some unknown error occurred"


class TestPlanValidatorProtocol:
    """Tests for the PlanValidator protocol."""

    def test_stub_validator_implements_protocol(self) -> None:
        """StubPlanValidator implements PlanValidator protocol."""
        validator = StubPlanValidator()
        assert isinstance(validator, PlanValidator)

    def test_protocol_has_validate_method(self) -> None:
        """PlanValidator protocol defines validate method."""
        assert hasattr(PlanValidator, "validate")


class TestStubPlanValidatorHappyPath:
    """Tests for StubPlanValidator success cases."""

    def test_validate_returns_payload_unchanged_on_success(
        self,
        sample_planning_context: PlanningContext,
        valid_payload: dict,
    ) -> None:
        """validate returns the payload unchanged when valid."""
        validator = StubPlanValidator()

        result = validator.validate(sample_planning_context, valid_payload)

        assert result == valid_payload

    def test_validate_accepts_minimal_valid_payload(
        self,
        sample_planning_context: PlanningContext,
    ) -> None:
        """validate accepts a minimal payload with only required keys."""
        validator = StubPlanValidator()
        minimal_payload = {
            "request_id": "test-request-id",
            "plan_version": "1.0.0",
        }

        result = validator.validate(sample_planning_context, minimal_payload)

        assert result == minimal_payload

    def test_validate_accepts_payload_with_extra_keys(
        self,
        sample_planning_context: PlanningContext,
    ) -> None:
        """validate accepts payloads with additional keys beyond required."""
        validator = StubPlanValidator()
        payload_with_extras = {
            "request_id": "test-request-id",
            "plan_version": "1.0.0",
            "extra_key": "extra_value",
            "another_key": 123,
        }

        result = validator.validate(sample_planning_context, payload_with_extras)

        assert result == payload_with_extras


class TestStubPlanValidatorFailureCases:
    """Tests for StubPlanValidator failure cases."""

    def test_validate_raises_on_none_payload(
        self,
        sample_planning_context: PlanningContext,
    ) -> None:
        """validate raises PlanValidationFailure on None payload."""
        validator = StubPlanValidator()

        with pytest.raises(PlanValidationFailure) as exc_info:
            validator.validate(sample_planning_context, None)

        assert exc_info.value.code == "INVALID_PAYLOAD_TYPE"
        assert "NoneType" in exc_info.value.message

    def test_validate_raises_on_string_payload(
        self,
        sample_planning_context: PlanningContext,
    ) -> None:
        """validate raises PlanValidationFailure on string payload."""
        validator = StubPlanValidator()

        with pytest.raises(PlanValidationFailure) as exc_info:
            validator.validate(sample_planning_context, "not a dict")

        assert exc_info.value.code == "INVALID_PAYLOAD_TYPE"
        assert "str" in exc_info.value.message

    def test_validate_raises_on_list_payload(
        self,
        sample_planning_context: PlanningContext,
    ) -> None:
        """validate raises PlanValidationFailure on list payload."""
        validator = StubPlanValidator()

        with pytest.raises(PlanValidationFailure) as exc_info:
            validator.validate(sample_planning_context, ["not", "a", "dict"])

        assert exc_info.value.code == "INVALID_PAYLOAD_TYPE"
        assert "list" in exc_info.value.message

    def test_validate_raises_on_missing_request_id(
        self,
        sample_planning_context: PlanningContext,
    ) -> None:
        """validate raises PlanValidationFailure when request_id is missing."""
        validator = StubPlanValidator()
        payload = {"plan_version": "1.0.0"}

        with pytest.raises(PlanValidationFailure) as exc_info:
            validator.validate(sample_planning_context, payload)

        assert exc_info.value.code == "MISSING_REQUEST_ID"
        assert "request_id" in exc_info.value.message

    def test_validate_raises_on_missing_plan_version(
        self,
        sample_planning_context: PlanningContext,
    ) -> None:
        """validate raises PlanValidationFailure when plan_version is missing."""
        validator = StubPlanValidator()
        payload = {"request_id": "test-id"}

        with pytest.raises(PlanValidationFailure) as exc_info:
            validator.validate(sample_planning_context, payload)

        assert exc_info.value.code == "MISSING_PLAN_VERSION"
        assert "plan_version" in exc_info.value.message

    def test_validate_raises_on_non_string_request_id(
        self,
        sample_planning_context: PlanningContext,
    ) -> None:
        """validate raises PlanValidationFailure when request_id is not a string."""
        validator = StubPlanValidator()
        payload = {
            "request_id": uuid4(),  # UUID object instead of string
            "plan_version": "1.0.0",
        }

        with pytest.raises(PlanValidationFailure) as exc_info:
            validator.validate(sample_planning_context, payload)

        assert exc_info.value.code == "INVALID_REQUEST_ID_TYPE"
        assert "UUID" in exc_info.value.message

    def test_validate_raises_on_integer_request_id(
        self,
        sample_planning_context: PlanningContext,
    ) -> None:
        """validate raises PlanValidationFailure when request_id is an integer."""
        validator = StubPlanValidator()
        payload = {
            "request_id": 12345,
            "plan_version": "1.0.0",
        }

        with pytest.raises(PlanValidationFailure) as exc_info:
            validator.validate(sample_planning_context, payload)

        assert exc_info.value.code == "INVALID_REQUEST_ID_TYPE"
        assert "int" in exc_info.value.message

    def test_validate_raises_on_non_string_plan_version(
        self,
        sample_planning_context: PlanningContext,
    ) -> None:
        """validate raises PlanValidationFailure when plan_version is not a string."""
        validator = StubPlanValidator()
        payload = {
            "request_id": "test-id",
            "plan_version": 1.0,  # float instead of string
        }

        with pytest.raises(PlanValidationFailure) as exc_info:
            validator.validate(sample_planning_context, payload)

        assert exc_info.value.code == "INVALID_PLAN_VERSION_TYPE"
        assert "float" in exc_info.value.message

    def test_validate_raises_on_empty_dict(
        self,
        sample_planning_context: PlanningContext,
    ) -> None:
        """validate raises PlanValidationFailure on empty dict."""
        validator = StubPlanValidator()

        with pytest.raises(PlanValidationFailure) as exc_info:
            validator.validate(sample_planning_context, {})

        # Should fail on missing request_id first
        assert exc_info.value.code == "MISSING_REQUEST_ID"


class TestPlanValidationFailureMetadata:
    """Tests ensuring exception metadata propagates correctly."""

    def test_exception_metadata_accessible_after_raise(
        self,
        sample_planning_context: PlanningContext,
    ) -> None:
        """Exception metadata is accessible after catching."""
        validator = StubPlanValidator()

        with pytest.raises(PlanValidationFailure) as exc_info:
            validator.validate(sample_planning_context, None)

        # Metadata should be accessible
        assert exc_info.value.code == "INVALID_PAYLOAD_TYPE"
        assert "NoneType" in exc_info.value.message
        # Should be able to build error response
        error_response = {
            "error": {
                "code": exc_info.value.code,
                "message": exc_info.value.message,
            }
        }
        assert error_response["error"]["code"] == "INVALID_PAYLOAD_TYPE"

    def test_exception_preserves_original_message_in_args(self) -> None:
        """Exception preserves message in args for standard Exception behavior."""
        exc = PlanValidationFailure(code="TEST", message="Original message")

        assert exc.args == ("Original message",)
