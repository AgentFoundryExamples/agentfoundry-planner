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
"""Context driver abstraction for fetching repository context."""

import json
from importlib import resources
from typing import Protocol, runtime_checkable

from planner_service.logging import get_logger
from planner_service.models import ProjectContext, RepositoryPointer


@runtime_checkable
class ContextDriver(Protocol):
    """Protocol defining the interface for context drivers.

    A context driver is responsible for fetching project context
    information for a given repository.
    """

    def fetch_context(self, repo: RepositoryPointer) -> ProjectContext:
        """Fetch project context for the given repository.

        Args:
            repo: The repository to fetch context for.

        Returns:
            ProjectContext containing repository metadata.

        Raises:
            FileNotFoundError: If required fixture/resource is missing.
            ValueError: If repository cannot be found or is invalid.
        """
        ...


class StubContextDriver:
    """Stub implementation of ContextDriver using bundled JSON fixtures.

    This driver returns deterministic mock data for testing and development
    without making actual GitHub API calls.
    """

    def __init__(self) -> None:
        """Initialize the stub driver and load fixtures."""
        self._fixtures: dict | None = None
        self._logger = get_logger(__name__)

    def _load_fixtures(self) -> dict:
        """Load mock context fixtures from bundled resource.

        Returns:
            Dictionary containing mock context data.

        Raises:
            FileNotFoundError: If the fixture file is missing.
        """
        if self._fixtures is not None:
            return self._fixtures

        try:
            fixture_path = resources.files("planner_service.resources").joinpath(
                "mock_context.json"
            )
            with fixture_path.open("r") as f:
                self._fixtures = json.load(f)
            return self._fixtures
        except FileNotFoundError as e:
            self._logger.error(
                "fixture_file_missing",
                error=str(e),
            )
            raise FileNotFoundError(
                "Mock context fixture file not found: mock_context.json"
            ) from e

    def fetch_context(self, repo: RepositoryPointer) -> ProjectContext:
        """Fetch project context from mock fixtures.

        Args:
            repo: The repository to fetch context for.

        Returns:
            ProjectContext with mock data from fixtures.
        """
        fixtures = self._load_fixtures()
        repo_key = f"{repo.owner}/{repo.repo}"

        # Check for specific repository data
        if repo_key in fixtures.get("repositories", {}):
            repo_data = fixtures["repositories"][repo_key]
        else:
            # Fall back to default mock data
            repo_data = fixtures.get("default", {})
            self._logger.debug(
                "using_default_mock_context",
                repository=repo_key,
            )

        return ProjectContext(
            repository=repo,
            default_branch=repo_data.get("default_branch"),
            languages=repo_data.get("languages"),
        )


def get_context_driver() -> ContextDriver:
    """Factory function to get the appropriate context driver.

    Attempts to import and use the private backend (af_github_core)
    if available, falling back to StubContextDriver on ImportError.

    Returns:
        An instance of ContextDriver (either private backend or stub).
    """
    logger = get_logger(__name__)

    try:
        # Attempt to import private backend
        from af_github_core import GitHubContextDriver  # type: ignore[import-not-found]

        logger.info("context_driver_selected", driver="af_github_core")
        return GitHubContextDriver()
    except ImportError:
        logger.info(
            "context_driver_fallback",
            driver="stub",
            reason="af_github_core not available",
        )
        return StubContextDriver()
