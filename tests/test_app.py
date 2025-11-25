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
"""Unit and integration tests for the planner service."""

from uuid import UUID

import pytest
from fastapi.testclient import TestClient

from planner_service.api import app


@pytest.fixture
def client() -> TestClient:
    """Create a test client for the FastAPI app."""
    return TestClient(app)


class TestHealthEndpoint:
    """Tests for the health check endpoint."""

    def test_health_returns_healthy(self, client: TestClient) -> None:
        """Health endpoint returns healthy status."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "planner-service"
        assert "version" in data

    def test_health_includes_version(self, client: TestClient) -> None:
        """Health endpoint includes service version."""
        response = client.get("/health")
        data = response.json()
        assert data["version"] == "0.1.0"


class TestPlanEndpoint:
    """Tests for the /v1/plan endpoint."""

    def test_plan_returns_pending_status(self, client: TestClient) -> None:
        """Plan endpoint returns pending status for valid request."""
        payload = {
            "repository": {
                "owner": "test-owner",
                "repo": "test-repo",
            },
            "user_input": {
                "query": "Create a new feature",
            },
        }
        response = client.post("/v1/plan", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "pending"

    def test_plan_returns_request_and_run_ids(self, client: TestClient) -> None:
        """Plan endpoint returns valid request_id and run_id."""
        payload = {
            "repository": {
                "owner": "test-owner",
                "repo": "test-repo",
            },
            "user_input": {
                "query": "Create a new feature",
            },
        }
        response = client.post("/v1/plan", json=payload)
        data = response.json()

        # Verify both IDs are valid UUIDs
        request_id = UUID(data["request_id"])
        run_id = UUID(data["run_id"])
        assert request_id is not None
        assert run_id is not None
        # run_id should be different from request_id
        assert request_id != run_id

    def test_plan_echoes_provided_request_id(self, client: TestClient) -> None:
        """Plan endpoint echoes client-provided request_id."""
        client_request_id = "550e8400-e29b-41d4-a716-446655440000"
        payload = {
            "repository": {
                "owner": "test-owner",
                "repo": "test-repo",
            },
            "user_input": {
                "query": "Create a new feature",
            },
            "request_id": client_request_id,
        }
        response = client.post("/v1/plan", json=payload)
        data = response.json()
        assert data["request_id"] == client_request_id

    def test_plan_missing_repository_fails_validation(
        self, client: TestClient
    ) -> None:
        """Plan endpoint returns validation error for missing repository."""
        payload = {
            "user_input": {
                "query": "Create a new feature",
            },
        }
        response = client.post("/v1/plan", json=payload)
        assert response.status_code == 422
        data = response.json()
        # Validation errors should not include run_id
        assert "run_id" not in data

    def test_plan_missing_user_input_fails_validation(
        self, client: TestClient
    ) -> None:
        """Plan endpoint returns validation error for missing user_input."""
        payload = {
            "repository": {
                "owner": "test-owner",
                "repo": "test-repo",
            },
        }
        response = client.post("/v1/plan", json=payload)
        assert response.status_code == 422

    def test_plan_with_optional_fields(self, client: TestClient) -> None:
        """Plan endpoint accepts optional fields."""
        payload = {
            "repository": {
                "owner": "test-owner",
                "repo": "test-repo",
                "ref": "main",
            },
            "user_input": {
                "query": "Create a new feature",
                "context": "This is additional context",
            },
        }
        response = client.post("/v1/plan", json=payload)
        assert response.status_code == 200


class TestModels:
    """Tests for Pydantic models."""

    def test_repository_pointer_required_fields(self) -> None:
        """RepositoryPointer requires owner and repo."""
        from planner_service.models import RepositoryPointer

        pointer = RepositoryPointer(owner="test", repo="repo")
        assert pointer.owner == "test"
        assert pointer.repo == "repo"
        assert pointer.ref is None

    def test_plan_response_fields(self) -> None:
        """PlanResponse has correct field structure."""
        from uuid import uuid4

        from planner_service.models import PlanResponse

        response = PlanResponse(
            request_id=uuid4(),
            run_id=uuid4(),
            status="completed",
            steps=None,
        )
        assert response.status == "completed"


class TestAppInitialization:
    """Tests for app initialization."""

    def test_app_title(self) -> None:
        """App has correct title."""
        assert app.title == "Planner Service"

    def test_app_version(self) -> None:
        """App has correct version."""
        assert app.version == "0.1.0"


class TestLogging:
    """Tests for logging configuration."""

    def test_get_logger_returns_bound_logger(self) -> None:
        """get_logger returns a bound logger with service tag."""
        from planner_service.logging import get_logger

        logger = get_logger("test")
        assert logger is not None

    def test_configure_logging_does_not_raise(self) -> None:
        """configure_logging completes without error."""
        from planner_service.logging import configure_logging

        # Should not raise any exceptions
        configure_logging()
