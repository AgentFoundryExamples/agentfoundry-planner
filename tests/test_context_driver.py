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
"""Tests for context driver abstraction and stub implementation (AF v1.1)."""

import builtins
import sys
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from planner_service.api import app
from planner_service.context_driver import (
    ContextDriver,
    StubContextDriver,
    get_context_driver,
)
from planner_service.models import RepositoryPointer


@pytest.fixture
def client() -> TestClient:
    """Create a test client for the FastAPI app."""
    return TestClient(app)


class TestContextDriverProtocol:
    """Tests for the ContextDriver protocol."""

    def test_stub_driver_implements_protocol(self) -> None:
        """StubContextDriver implements ContextDriver protocol."""
        driver = StubContextDriver()
        assert isinstance(driver, ContextDriver)

    def test_protocol_has_fetch_context_method(self) -> None:
        """ContextDriver protocol defines fetch_context method."""
        # Protocol should define fetch_context
        assert hasattr(ContextDriver, "fetch_context")


class TestStubContextDriver:
    """Tests for the StubContextDriver implementation (AF v1.1)."""

    def test_fetch_context_returns_project_context(self) -> None:
        """fetch_context returns a valid ProjectContext."""
        driver = StubContextDriver()
        repo = RepositoryPointer(owner="test-owner", name="test-repo")

        context = driver.fetch_context(repo)

        assert context.repo_owner == "test-owner"
        assert context.repo_name == "test-repo"

    def test_fetch_context_uses_default_for_unknown_repo(self) -> None:
        """fetch_context returns default data for unknown repository."""
        driver = StubContextDriver()
        repo = RepositoryPointer(owner="unknown", name="unknown-repo")

        context = driver.fetch_context(repo)

        # Should have repo coordinates
        assert context.repo_owner == "unknown"
        assert context.repo_name == "unknown-repo"
        assert context.ref == "refs/heads/main"  # Default ref

    def test_fetch_context_deterministic_output(self) -> None:
        """fetch_context returns consistent results across calls."""
        driver = StubContextDriver()
        repo = RepositoryPointer(owner="example-org", name="example-repo")

        context1 = driver.fetch_context(repo)
        context2 = driver.fetch_context(repo)

        assert context1.repo_owner == context2.repo_owner
        assert context1.repo_name == context2.repo_name

    def test_fetch_context_includes_repository_pointer(self) -> None:
        """fetch_context includes original repository in response."""
        driver = StubContextDriver()
        repo = RepositoryPointer(
            owner="my-org", name="my-repo", ref="refs/heads/feature"
        )

        context = driver.fetch_context(repo)

        assert context.repo_owner == "my-org"
        assert context.repo_name == "my-repo"
        assert context.ref == "refs/heads/feature"


class TestGetContextDriverFactory:
    """Tests for the get_context_driver factory function."""

    def test_returns_stub_driver_when_private_unavailable(self) -> None:
        """Factory returns StubContextDriver when af_github_core is not available."""
        driver = get_context_driver()

        assert isinstance(driver, StubContextDriver)

    def test_attempts_private_backend_import(self) -> None:
        """Factory attempts to import af_github_core first."""
        with patch.dict(sys.modules, {"af_github_core": None}):
            # This should still fall back to stub since module is None
            driver = get_context_driver()
            assert isinstance(driver, StubContextDriver)

    def test_uses_private_backend_when_available(self) -> None:
        """Factory uses private backend when successfully imported."""
        mock_driver_instance = MagicMock()
        mock_github_context_driver = MagicMock(return_value=mock_driver_instance)

        # Create a mock module with the expected class
        mock_module = MagicMock()
        mock_module.GitHubContextDriver = mock_github_context_driver

        original_import = builtins.__import__

        def mock_import(name, *args, **kwargs):
            if name == "af_github_core":
                return mock_module
            return original_import(name, *args, **kwargs)

        with patch.object(builtins, "__import__", side_effect=mock_import):
            driver = get_context_driver()
            assert driver is mock_driver_instance
            mock_github_context_driver.assert_called_once()

    def test_logs_fallback_on_import_error(self) -> None:
        """Factory logs when falling back to stub driver."""
        with patch("planner_service.context_driver.get_logger") as mock_get_logger:
            mock_logger = MagicMock()
            mock_get_logger.return_value = mock_logger

            get_context_driver()

            # Should have logged the fallback
            mock_logger.info.assert_called_with(
                "context_driver_fallback",
                driver="stub",
                reason="af_github_core not available",
            )


class TestDebugContextEndpoint:
    """Tests for the /v1/debug/context endpoint (AF v1.1)."""

    def test_debug_context_requires_auth(self, client: TestClient) -> None:
        """Debug endpoint requires authorization header."""
        payload = {"owner": "test", "name": "test-repo"}
        response = client.post("/v1/debug/context", json=payload)

        assert response.status_code == 401
        assert "Authorization header required" in response.json()["error"]["message"]

    def test_debug_context_rejects_invalid_auth_format(
        self, client: TestClient
    ) -> None:
        """Debug endpoint rejects malformed authorization header."""
        payload = {"owner": "test", "name": "test-repo"}
        response = client.post(
            "/v1/debug/context",
            json=payload,
            headers={"Authorization": "InvalidFormat"},
        )

        assert response.status_code == 401
        assert "Invalid authorization format" in response.json()["error"]["message"]

    def test_debug_context_rejects_wrong_token(self, client: TestClient) -> None:
        """Debug endpoint rejects incorrect token."""
        payload = {"owner": "test", "name": "test-repo"}
        response = client.post(
            "/v1/debug/context",
            json=payload,
            headers={"Authorization": "Bearer wrong-token"},
        )

        assert response.status_code == 403
        assert "Invalid token" in response.json()["error"]["message"]

    def test_debug_context_returns_context_with_valid_auth(
        self, client: TestClient
    ) -> None:
        """Debug endpoint returns ProjectContext with valid auth."""
        payload = {"owner": "test-owner", "name": "test-repo"}
        response = client.post(
            "/v1/debug/context",
            json=payload,
            headers={"Authorization": "Bearer debug-token-stub"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["repo_owner"] == "test-owner"
        assert data["repo_name"] == "test-repo"

    def test_debug_context_uses_default_for_unknown_repo(
        self, client: TestClient
    ) -> None:
        """Debug endpoint returns default context for unknown repository."""
        payload = {"owner": "unknown", "name": "unknown-repo"}
        response = client.post(
            "/v1/debug/context",
            json=payload,
            headers={"Authorization": "Bearer debug-token-stub"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["repo_owner"] == "unknown"
        assert data["repo_name"] == "unknown-repo"
        assert data["ref"] == "refs/heads/main"

    def test_debug_context_accepts_optional_ref(self, client: TestClient) -> None:
        """Debug endpoint accepts optional ref in repository pointer."""
        payload = {
            "owner": "test-owner",
            "name": "test-repo",
            "ref": "refs/heads/feature",
        }
        response = client.post(
            "/v1/debug/context",
            json=payload,
            headers={"Authorization": "Bearer debug-token-stub"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["ref"] == "refs/heads/feature"

    def test_debug_context_returns_structured_error_on_missing_fixture(
        self, client: TestClient
    ) -> None:
        """Debug endpoint returns structured error when fixture file is missing."""
        # Mock the fixture loading to raise FileNotFoundError
        with patch.object(
            StubContextDriver,
            "_load_fixtures",
            side_effect=FileNotFoundError(
                "Mock context fixture file not found: mock_context.json"
            ),
        ):
            payload = {"owner": "test", "name": "test-repo"}
            response = client.post(
                "/v1/debug/context",
                json=payload,
                headers={"Authorization": "Bearer debug-token-stub"},
            )

            assert response.status_code == 500
            data = response.json()
            # Should have structured error with request_id but no run_id
            assert "error" in data
            assert data["error"]["code"] == "FIXTURE_NOT_FOUND"
            assert "mock_context.json" in data["error"]["message"]
            assert "request_id" in data
            assert "run_id" not in data
