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
"""Tests for prompt engine abstraction and stub implementation."""

import builtins
from unittest.mock import MagicMock, patch

import pytest

from planner_service.models import (
    PlanningContext,
    ProjectContext,
    RepositoryPointer,
    UserInput,
)
from planner_service.prompt_engine import (
    PromptEngine,
    StubPromptEngine,
    get_prompt_engine,
)


@pytest.fixture
def sample_planning_context() -> PlanningContext:
    """Create a sample planning context for tests."""
    return PlanningContext(
        project=ProjectContext(
            repository=RepositoryPointer(
                owner="test-owner",
                repo="test-repo",
                ref="main",
            ),
            default_branch="main",
            languages=["python"],
        ),
        user_input=UserInput(
            query="Create a new feature for user authentication",
            context="Additional context about the feature",
        ),
        session_id="test-session-123",
    )


class TestPromptEngineProtocol:
    """Tests for the PromptEngine protocol."""

    def test_stub_engine_implements_protocol(self) -> None:
        """StubPromptEngine implements PromptEngine protocol."""
        engine = StubPromptEngine()
        assert isinstance(engine, PromptEngine)

    def test_protocol_has_run_method(self) -> None:
        """PromptEngine protocol defines run method."""
        assert hasattr(PromptEngine, "run")


class TestStubPromptEngine:
    """Tests for the StubPromptEngine implementation."""

    def test_run_returns_dict_with_required_keys(
        self, sample_planning_context: PlanningContext
    ) -> None:
        """run returns a dict with all required keys."""
        engine = StubPromptEngine()
        result = engine.run(sample_planning_context)

        assert "request_id" in result
        assert "repository" in result
        assert "status" in result
        assert "prompt_preview" in result

    def test_run_returns_success_status(
        self, sample_planning_context: PlanningContext
    ) -> None:
        """run returns success status for valid input."""
        engine = StubPromptEngine()
        result = engine.run(sample_planning_context)

        assert result["status"] == "success"

    def test_run_returns_repository_metadata(
        self, sample_planning_context: PlanningContext
    ) -> None:
        """run includes repository metadata in output."""
        engine = StubPromptEngine()
        result = engine.run(sample_planning_context)

        repo = result["repository"]
        assert repo["owner"] == "test-owner"
        assert repo["repo"] == "test-repo"
        assert repo["ref"] == "main"

    def test_run_returns_unique_request_id(
        self, sample_planning_context: PlanningContext
    ) -> None:
        """run returns unique request_id for each call."""
        engine = StubPromptEngine()
        result1 = engine.run(sample_planning_context)
        result2 = engine.run(sample_planning_context)

        assert result1["request_id"] != result2["request_id"]

    def test_run_returns_prompt_preview(
        self, sample_planning_context: PlanningContext
    ) -> None:
        """run returns a prompt preview without exposing real prompts."""
        engine = StubPromptEngine()
        result = engine.run(sample_planning_context)

        preview = result["prompt_preview"]
        assert "[STUB]" in preview
        assert "test-owner/test-repo" in preview
        assert "user authentication" in preview

    def test_run_truncates_long_queries_in_preview(self) -> None:
        """run truncates long queries in prompt preview."""
        long_query = "A" * 100
        ctx = PlanningContext(
            project=ProjectContext(
                repository=RepositoryPointer(owner="owner", repo="repo", ref=None),
            ),
            user_input=UserInput(query=long_query),
        )

        engine = StubPromptEngine()
        result = engine.run(ctx)

        preview = result["prompt_preview"]
        assert "..." in preview

    def test_run_handles_none_ref(self) -> None:
        """run handles repository without ref."""
        ctx = PlanningContext(
            project=ProjectContext(
                repository=RepositoryPointer(owner="owner", repo="repo", ref=None),
            ),
            user_input=UserInput(query="Test query"),
        )

        engine = StubPromptEngine()
        result = engine.run(ctx)

        assert result["repository"]["ref"] is None

    def test_run_deterministic_output_structure(
        self, sample_planning_context: PlanningContext
    ) -> None:
        """run returns consistent output structure across calls."""
        engine = StubPromptEngine()
        result1 = engine.run(sample_planning_context)
        result2 = engine.run(sample_planning_context)

        # Same structure and values except request_id
        assert result1["status"] == result2["status"]
        assert result1["repository"] == result2["repository"]
        # prompt_preview should be same for same input
        assert result1["prompt_preview"] == result2["prompt_preview"]

    def test_run_logs_request_metadata(
        self, sample_planning_context: PlanningContext
    ) -> None:
        """run logs request metadata for debugging."""
        with patch("planner_service.prompt_engine.get_logger") as mock_get_logger:
            mock_logger = MagicMock()
            mock_get_logger.return_value = mock_logger

            engine = StubPromptEngine()
            result = engine.run(sample_planning_context)

            mock_logger.info.assert_called_once()
            call_args = mock_logger.info.call_args
            assert call_args[0][0] == "stub_prompt_engine_run"
            assert call_args[1]["repository"] == "test-owner/test-repo"
            assert call_args[1]["session_id"] == "test-session-123"


class TestGetPromptEngineFactory:
    """Tests for the get_prompt_engine factory function."""

    def test_returns_stub_engine_when_private_unavailable(self) -> None:
        """Factory returns StubPromptEngine when af_prompt_core is not available."""
        engine = get_prompt_engine()

        assert isinstance(engine, StubPromptEngine)

    def test_uses_private_backend_when_available(self) -> None:
        """Factory uses private backend when successfully imported."""
        mock_engine_instance = MagicMock()
        mock_prompt_engine_backend = MagicMock(return_value=mock_engine_instance)

        # Create a mock module with the expected class
        mock_module = MagicMock()
        mock_module.PromptEngineBackend = mock_prompt_engine_backend

        original_import = builtins.__import__

        def mock_import(name, *args, **kwargs):
            if name == "af_prompt_core":
                return mock_module
            return original_import(name, *args, **kwargs)

        with patch.object(builtins, "__import__", side_effect=mock_import):
            engine = get_prompt_engine()
            assert engine is mock_engine_instance
            mock_prompt_engine_backend.assert_called_once()

    def test_logs_fallback_on_import_error(self) -> None:
        """Factory logs when falling back to stub engine."""
        with patch("planner_service.prompt_engine.get_logger") as mock_get_logger:
            mock_logger = MagicMock()
            mock_get_logger.return_value = mock_logger

            get_prompt_engine()

            mock_logger.info.assert_called_with(
                "prompt_engine_fallback",
                engine="stub",
                reason="af_prompt_core not available",
            )

    def test_logs_when_private_backend_selected(self) -> None:
        """Factory logs when private backend is successfully selected."""
        mock_engine_instance = MagicMock()
        mock_prompt_engine_backend = MagicMock(return_value=mock_engine_instance)

        mock_module = MagicMock()
        mock_module.PromptEngineBackend = mock_prompt_engine_backend

        original_import = builtins.__import__

        def mock_import(name, *args, **kwargs):
            if name == "af_prompt_core":
                return mock_module
            return original_import(name, *args, **kwargs)

        with (
            patch.object(builtins, "__import__", side_effect=mock_import),
            patch("planner_service.prompt_engine.get_logger") as mock_get_logger,
        ):
            mock_logger = MagicMock()
            mock_get_logger.return_value = mock_logger

            get_prompt_engine()

            mock_logger.info.assert_called_with(
                "prompt_engine_selected",
                engine="af_prompt_core",
            )


class TestMultipleProjectContextHandling:
    """Tests for handling multiple ProjectContext entries."""

    def test_uses_first_project_context(self) -> None:
        """Stub uses the project context from the PlanningContext."""
        ctx = PlanningContext(
            project=ProjectContext(
                repository=RepositoryPointer(
                    owner="first-owner",
                    repo="first-repo",
                    ref="feature-1",
                ),
            ),
            user_input=UserInput(query="Test query"),
        )

        engine = StubPromptEngine()
        result = engine.run(ctx)

        # Should use the project context
        assert result["repository"]["owner"] == "first-owner"
        assert result["repository"]["repo"] == "first-repo"
        assert result["repository"]["ref"] == "feature-1"
