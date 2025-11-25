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
"""Tests for the POST /v1/plan endpoint including auth, context driver, and prompt engine (AF v1.1)."""

from unittest.mock import patch
from uuid import UUID

import pytest
from fastapi.testclient import TestClient

from planner_service.api import app


@pytest.fixture
def client() -> TestClient:
    """Create a test client for the FastAPI app."""
    return TestClient(app)


def _make_user_input() -> dict:
    """Create a valid AF v1.1 user input payload."""
    return {
        "purpose": "Test query",
        "vision": "A completed test",
        "must": ["Pass all tests"],
        "dont": ["Fail"],
        "nice": ["Be fast"],
    }


class TestPlanEndpointAuth:
    """Tests for authentication in /v1/plan endpoint."""

    def test_plan_allows_missing_auth_header_with_stub_user(
        self, client: TestClient
    ) -> None:
        """Plan endpoint allows missing auth header (stub user for now)."""
        payload = {
            "repository": {"owner": "test-owner", "name": "test-repo"},
            "user_input": _make_user_input(),
        }
        response = client.post("/v1/plan", json=payload)
        # Should succeed with stub user
        assert response.status_code == 200

    def test_plan_accepts_bearer_token(self, client: TestClient) -> None:
        """Plan endpoint accepts Bearer token in Authorization header."""
        payload = {
            "repository": {"owner": "test-owner", "name": "test-repo"},
            "user_input": _make_user_input(),
        }
        response = client.post(
            "/v1/plan",
            json=payload,
            headers={"Authorization": "Bearer test-token-123"},
        )
        assert response.status_code == 200

    def test_plan_handles_invalid_auth_format_gracefully(
        self, client: TestClient
    ) -> None:
        """Plan endpoint handles invalid auth format with stub user."""
        payload = {
            "repository": {"owner": "test-owner", "name": "test-repo"},
            "user_input": _make_user_input(),
        }
        response = client.post(
            "/v1/plan",
            json=payload,
            headers={"Authorization": "InvalidFormat"},
        )
        # Should succeed with stub user
        assert response.status_code == 200


class TestPlanEndpointHappyPath:
    """Tests for successful /v1/plan requests."""

    def test_plan_returns_completed_status(self, client: TestClient) -> None:
        """Plan endpoint returns completed status when prompt engine succeeds."""
        payload = {
            "repository": {"owner": "test-owner", "name": "test-repo"},
            "user_input": _make_user_input(),
        }
        response = client.post("/v1/plan", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"

    def test_plan_returns_payload_on_success(self, client: TestClient) -> None:
        """Plan endpoint returns engine result in payload when completed."""
        payload = {
            "repository": {"owner": "test-owner", "name": "test-repo"},
            "user_input": _make_user_input(),
        }
        response = client.post("/v1/plan", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"
        assert data["payload"] is not None
        # Verify payload contains engine result fields
        assert "status" in data["payload"]
        assert data["payload"]["status"] == "success"
        assert "repository" in data["payload"]
        assert "prompt_preview" in data["payload"]

    def test_plan_returns_request_id_and_run_id(self, client: TestClient) -> None:
        """Plan endpoint returns valid request_id and run_id."""
        payload = {
            "repository": {"owner": "test-owner", "name": "test-repo"},
            "user_input": _make_user_input(),
        }
        response = client.post("/v1/plan", json=payload)
        data = response.json()

        request_id = UUID(data["request_id"])
        run_id = UUID(data["run_id"])
        assert request_id is not None
        assert run_id is not None
        # In sync flow, run_id mirrors request_id
        assert request_id == run_id

    def test_plan_echoes_client_provided_request_id(self, client: TestClient) -> None:
        """Plan endpoint echoes client-provided request_id."""
        client_request_id = "550e8400-e29b-41d4-a716-446655440000"
        payload = {
            "repository": {"owner": "test-owner", "name": "test-repo"},
            "user_input": _make_user_input(),
            "request_id": client_request_id,
        }
        response = client.post("/v1/plan", json=payload)
        data = response.json()

        assert data["request_id"] == client_request_id
        assert data["run_id"] == client_request_id  # Mirrors request_id


class TestPlanEndpointContextDriverFailure:
    """Tests for context driver failures in /v1/plan endpoint."""

    def test_plan_returns_5xx_on_context_driver_file_not_found(
        self, client: TestClient
    ) -> None:
        """Plan endpoint returns 500 when context driver fails with FileNotFoundError."""
        from planner_service.context_driver import StubContextDriver

        with patch.object(
            StubContextDriver,
            "fetch_context",
            side_effect=FileNotFoundError("Mock fixture missing"),
        ):
            payload = {
                "repository": {"owner": "test-owner", "name": "test-repo"},
                "user_input": _make_user_input(),
            }
            response = client.post("/v1/plan", json=payload)

            assert response.status_code == 500
            data = response.json()
            assert "error" in data
            assert data["error"]["code"] == "CONTEXT_DRIVER_ERROR"
            assert "request_id" in data
            assert "run_id" not in data  # No run_id on error

    def test_plan_returns_5xx_on_context_driver_unexpected_error(
        self, client: TestClient
    ) -> None:
        """Plan endpoint returns 500 when context driver fails with unexpected error."""
        from planner_service.context_driver import StubContextDriver

        with patch.object(
            StubContextDriver,
            "fetch_context",
            side_effect=RuntimeError("Unexpected error"),
        ):
            payload = {
                "repository": {"owner": "test-owner", "name": "test-repo"},
                "user_input": _make_user_input(),
            }
            response = client.post("/v1/plan", json=payload)

            assert response.status_code == 500
            data = response.json()
            assert data["error"]["code"] == "CONTEXT_DRIVER_ERROR"
            assert "request_id" in data
            assert "run_id" not in data


class TestPlanEndpointPromptEngineFailure:
    """Tests for prompt engine failures in /v1/plan endpoint."""

    def test_plan_returns_5xx_on_prompt_engine_failure(
        self, client: TestClient
    ) -> None:
        """Plan endpoint returns 500 when prompt engine fails."""
        from planner_service.prompt_engine import StubPromptEngine

        with patch.object(
            StubPromptEngine, "run", side_effect=RuntimeError("LLM unavailable")
        ):
            payload = {
                "repository": {"owner": "test-owner", "name": "test-repo"},
                "user_input": _make_user_input(),
            }
            response = client.post("/v1/plan", json=payload)

            assert response.status_code == 500
            data = response.json()
            assert "error" in data
            assert data["error"]["code"] == "PROMPT_ENGINE_ERROR"
            assert "request_id" in data
            assert "run_id" not in data  # No run_id on error

    def test_plan_preserves_request_id_on_prompt_engine_failure(
        self, client: TestClient
    ) -> None:
        """Plan endpoint preserves client request_id on prompt engine failure."""
        from planner_service.prompt_engine import StubPromptEngine

        client_request_id = "550e8400-e29b-41d4-a716-446655440000"
        with patch.object(
            StubPromptEngine, "run", side_effect=RuntimeError("LLM unavailable")
        ):
            payload = {
                "repository": {"owner": "test-owner", "name": "test-repo"},
                "user_input": _make_user_input(),
                "request_id": client_request_id,
            }
            response = client.post("/v1/plan", json=payload)

            assert response.status_code == 500
            data = response.json()
            assert data["request_id"] == client_request_id


class TestPlanEndpointPlanValidationFailure:
    """Tests for plan validation failures in /v1/plan endpoint."""

    def test_plan_returns_5xx_on_validation_failure(
        self, client: TestClient
    ) -> None:
        """Plan endpoint returns 500 when plan validation fails."""
        from planner_service.plan_validator import PlanValidationFailure, StubPlanValidator

        with patch.object(
            StubPlanValidator,
            "validate",
            side_effect=PlanValidationFailure(
                code="MISSING_REQUEST_ID",
                message="Payload missing required key: request_id",
            ),
        ):
            payload = {
                "repository": {"owner": "test-owner", "name": "test-repo"},
                "user_input": _make_user_input(),
            }
            response = client.post("/v1/plan", json=payload)

            assert response.status_code == 500
            data = response.json()
            assert "error" in data
            assert data["error"]["code"] == "MISSING_REQUEST_ID"
            assert "request_id" in data
            assert "run_id" not in data  # No run_id on error

    def test_plan_preserves_request_id_on_validation_failure(
        self, client: TestClient
    ) -> None:
        """Plan endpoint preserves client request_id on validation failure."""
        from planner_service.plan_validator import PlanValidationFailure, StubPlanValidator

        client_request_id = "550e8400-e29b-41d4-a716-446655440000"
        with patch.object(
            StubPlanValidator,
            "validate",
            side_effect=PlanValidationFailure(
                code="INVALID_PAYLOAD_TYPE",
                message="Expected dict payload, got NoneType",
            ),
        ):
            payload = {
                "repository": {"owner": "test-owner", "name": "test-repo"},
                "user_input": _make_user_input(),
                "request_id": client_request_id,
            }
            response = client.post("/v1/plan", json=payload)

            assert response.status_code == 500
            data = response.json()
            assert data["request_id"] == client_request_id
            assert data["error"]["code"] == "INVALID_PAYLOAD_TYPE"


class TestPlanEndpointValidation:
    """Tests for request validation in /v1/plan endpoint (AF v1.1)."""

    def test_plan_missing_repository_returns_422_with_request_id(
        self, client: TestClient
    ) -> None:
        """Plan endpoint returns 422 with request_id for missing repository."""
        payload = {"user_input": _make_user_input()}
        response = client.post("/v1/plan", json=payload)
        assert response.status_code == 422
        data = response.json()
        assert "error" in data
        assert data["error"]["code"] == "VALIDATION_ERROR"
        assert "request_id" in data
        assert "run_id" not in data  # No run_id on error

    def test_plan_missing_user_input_returns_422_with_request_id(
        self, client: TestClient
    ) -> None:
        """Plan endpoint returns 422 with request_id for missing user_input."""
        payload = {"repository": {"owner": "test-owner", "name": "test-repo"}}
        response = client.post("/v1/plan", json=payload)
        assert response.status_code == 422
        data = response.json()
        assert "error" in data
        assert data["error"]["code"] == "VALIDATION_ERROR"
        assert "request_id" in data
        assert "run_id" not in data  # No run_id on error

    def test_plan_validation_error_echoes_client_request_id(
        self, client: TestClient
    ) -> None:
        """Plan endpoint echoes client-provided request_id on validation errors."""
        client_request_id = "550e8400-e29b-41d4-a716-446655440000"
        payload = {
            "user_input": _make_user_input(),
            "request_id": client_request_id,
        }
        response = client.post("/v1/plan", json=payload)
        assert response.status_code == 422
        data = response.json()
        assert data["request_id"] == client_request_id
        assert "run_id" not in data

    def test_plan_rejects_empty_must_list_entries(self, client: TestClient) -> None:
        """Plan endpoint rejects empty strings in must list."""
        payload = {
            "repository": {"owner": "test-owner", "name": "test-repo"},
            "user_input": {
                "purpose": "Test",
                "vision": "Test vision",
                "must": ["Valid", ""],  # Empty string should fail
                "dont": ["Fail"],
                "nice": ["Be fast"],
            },
        }
        response = client.post("/v1/plan", json=payload)
        assert response.status_code == 422

    def test_plan_rejects_whitespace_only_entries(self, client: TestClient) -> None:
        """Plan endpoint rejects whitespace-only strings in lists."""
        payload = {
            "repository": {"owner": "test-owner", "name": "test-repo"},
            "user_input": {
                "purpose": "Test",
                "vision": "Test vision",
                "must": ["Valid", "   "],  # Whitespace only should fail
                "dont": ["Fail"],
                "nice": ["Be fast"],
            },
        }
        response = client.post("/v1/plan", json=payload)
        assert response.status_code == 422

    def test_plan_rejects_extra_user_input_keys(self, client: TestClient) -> None:
        """Plan endpoint rejects unexpected keys in user_input (AF v1.1)."""
        payload = {
            "repository": {"owner": "test-owner", "name": "test-repo"},
            "user_input": {
                "purpose": "Test",
                "vision": "Test vision",
                "must": ["Valid"],
                "dont": ["Fail"],
                "nice": ["Be fast"],
                "extra_key": "should fail",  # Extra key not allowed
            },
        }
        response = client.post("/v1/plan", json=payload)
        assert response.status_code == 422

    def test_plan_rejects_empty_purpose(self, client: TestClient) -> None:
        """Plan endpoint rejects empty purpose string."""
        payload = {
            "repository": {"owner": "test-owner", "name": "test-repo"},
            "user_input": {
                "purpose": "",  # Empty string should fail
                "vision": "Test vision",
                "must": ["Valid"],
                "dont": ["Fail"],
                "nice": ["Be fast"],
            },
        }
        response = client.post("/v1/plan", json=payload)
        assert response.status_code == 422

    def test_plan_rejects_whitespace_only_purpose(self, client: TestClient) -> None:
        """Plan endpoint rejects whitespace-only purpose string."""
        payload = {
            "repository": {"owner": "test-owner", "name": "test-repo"},
            "user_input": {
                "purpose": "   ",  # Whitespace only should fail
                "vision": "Test vision",
                "must": ["Valid"],
                "dont": ["Fail"],
                "nice": ["Be fast"],
            },
        }
        response = client.post("/v1/plan", json=payload)
        assert response.status_code == 422

    def test_plan_rejects_empty_vision(self, client: TestClient) -> None:
        """Plan endpoint rejects empty vision string."""
        payload = {
            "repository": {"owner": "test-owner", "name": "test-repo"},
            "user_input": {
                "purpose": "Test purpose",
                "vision": "",  # Empty string should fail
                "must": ["Valid"],
                "dont": ["Fail"],
                "nice": ["Be fast"],
            },
        }
        response = client.post("/v1/plan", json=payload)
        assert response.status_code == 422

    def test_plan_rejects_whitespace_only_vision(self, client: TestClient) -> None:
        """Plan endpoint rejects whitespace-only vision string."""
        payload = {
            "repository": {"owner": "test-owner", "name": "test-repo"},
            "user_input": {
                "purpose": "Test purpose",
                "vision": "   ",  # Whitespace only should fail
                "must": ["Valid"],
                "dont": ["Fail"],
                "nice": ["Be fast"],
            },
        }
        response = client.post("/v1/plan", json=payload)
        assert response.status_code == 422

    def test_plan_rejects_non_string_list_items(self, client: TestClient) -> None:
        """Plan endpoint rejects non-string items in lists (strict typing)."""
        payload = {
            "repository": {"owner": "test-owner", "name": "test-repo"},
            "user_input": {
                "purpose": "Test purpose",
                "vision": "Test vision",
                "must": [123],  # Non-string should fail with StrictStr
                "dont": ["Valid"],
                "nice": ["Be fast"],
            },
        }
        response = client.post("/v1/plan", json=payload)
        assert response.status_code == 422

    def test_plan_rejects_non_string_purpose_vision(self, client: TestClient) -> None:
        """Plan endpoint rejects non-string purpose/vision (strict typing)."""
        # Test non-string purpose
        payload = {
            "repository": {"owner": "test-owner", "name": "test-repo"},
            "user_input": {
                "purpose": 123,  # Non-string should fail with StrictStr
                "vision": "Test vision",
                "must": ["Required"],
                "dont": ["Avoid this"],
                "nice": ["Be fast"],
            },
        }
        response = client.post("/v1/plan", json=payload)
        assert response.status_code == 422

        # Test non-string vision
        payload = {
            "repository": {"owner": "test-owner", "name": "test-repo"},
            "user_input": {
                "purpose": "Test purpose",
                "vision": True,  # Non-string should fail with StrictStr
                "must": ["Required"],
                "dont": ["Avoid this"],
                "nice": ["Be fast"],
            },
        }
        response = client.post("/v1/plan", json=payload)
        assert response.status_code == 422


class TestHealthEndpoints:
    """Tests for health check endpoints."""

    def test_healthz_returns_healthy(self, client: TestClient) -> None:
        """Healthz endpoint returns healthy status."""
        response = client.get("/healthz")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "planner-service"
        assert "version" in data

    def test_health_and_healthz_return_same_response(
        self, client: TestClient
    ) -> None:
        """Both health endpoints return equivalent response."""
        health_response = client.get("/health")
        healthz_response = client.get("/healthz")

        assert health_response.status_code == healthz_response.status_code
        assert health_response.json() == healthz_response.json()


class TestAuthContextModel:
    """Tests for the AuthContext model."""

    def test_auth_context_creation(self) -> None:
        """AuthContext can be created with user_id."""
        from planner_service.auth import AuthContext

        auth = AuthContext(user_id="test-user")
        assert auth.user_id == "test-user"
        assert auth.token is None

    def test_auth_context_with_token(self) -> None:
        """AuthContext can be created with user_id and token."""
        from planner_service.auth import AuthContext

        auth = AuthContext(user_id="test-user", token="test-token")
        assert auth.user_id == "test-user"
        assert auth.token == "test-token"


class TestGetCurrentUserDependency:
    """Tests for the get_current_user dependency."""

    def test_returns_stub_user_without_header(self) -> None:
        """get_current_user returns stub user when no header provided."""
        from planner_service.auth import get_current_user

        auth = get_current_user(authorization=None)
        assert auth.user_id == "stub-user"
        assert auth.token is None

    def test_returns_stub_user_with_invalid_format(self) -> None:
        """get_current_user returns stub user for invalid format."""
        from planner_service.auth import get_current_user

        auth = get_current_user(authorization="InvalidFormat")
        assert auth.user_id == "stub-user"
        assert auth.token is None

    def test_returns_stub_user_with_valid_bearer_token(self) -> None:
        """get_current_user returns stub user with token for valid bearer format."""
        from planner_service.auth import get_current_user

        auth = get_current_user(authorization="Bearer my-token")
        assert auth.user_id == "stub-user"
        assert auth.token == "my-token"
