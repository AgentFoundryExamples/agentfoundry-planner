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
"""Prompt engine abstraction for delegating plan generation to pluggable prompt logic."""

from typing import Protocol, runtime_checkable
from uuid import uuid4

from planner_service.logging import get_logger
from planner_service.models import PlanningContext


@runtime_checkable
class PromptEngine(Protocol):
    """Protocol defining the interface for prompt engines.

    A prompt engine is responsible for generating plan output from
    a planning context. Implementations may use LLMs, rule engines,
    or return static data for testing.
    """

    def run(self, ctx: PlanningContext) -> dict:
        """Generate plan output from the given planning context.

        Args:
            ctx: The planning context containing project and user input.

        Returns:
            A dictionary containing the plan output with keys:
            - request_id: Unique identifier for this request
            - repository: Repository metadata (owner, repo, ref)
            - status: Status of the plan generation ("success" or "failure")
            - prompt_preview: Preview of the prompt that would be sent (stub only)

        Raises:
            RuntimeError: If plan generation fails.
        """
        ...


class StubPromptEngine:
    """Stub implementation of PromptEngine returning deterministic payload.

    This engine returns predictable output for testing and development
    without making any network or LLM calls. It logs request metadata
    for debugging purposes.
    """

    def __init__(self) -> None:
        """Initialize the stub prompt engine."""
        self._logger = get_logger(__name__)

    def run(self, ctx: PlanningContext) -> dict:
        """Generate deterministic plan output from the given context.

        Args:
            ctx: The planning context containing project and user input.

        Returns:
            A dictionary with deterministic output including request_id,
            repository metadata, status, and a prompt preview.
        """
        request_id = str(uuid4())

        # Extract repository metadata from the first/primary project context
        repo = ctx.project.repository
        repository_metadata = {
            "owner": repo.owner,
            "repo": repo.repo,
            "ref": repo.ref,
        }

        # Log request metadata for debugging
        self._logger.info(
            "stub_prompt_engine_run",
            request_id=request_id,
            repository=f"{repo.owner}/{repo.repo}",
            session_id=ctx.session_id,
        )

        # Build deterministic prompt preview (does not expose real prompts)
        base_preview = f"[STUB] Planning request for {repo.owner}/{repo.repo}: "
        query = ctx.user_input.query
        if len(query) > 50:
            prompt_preview = f"{base_preview}{query[:50]}..."
        else:
            prompt_preview = f"{base_preview}{query}"

        return {
            "request_id": request_id,
            "repository": repository_metadata,
            "status": "success",
            "prompt_preview": prompt_preview,
        }


def get_prompt_engine() -> PromptEngine:
    """Factory function to get the appropriate prompt engine.

    Attempts to import and use the private backend (af_prompt_core)
    if available, falling back to StubPromptEngine on ImportError.

    Returns:
        An instance of PromptEngine (either private backend or stub).
    """
    logger = get_logger(__name__)

    try:
        # Attempt to import private backend
        from af_prompt_core import PromptEngineBackend  # type: ignore[import-not-found]

        logger.info("prompt_engine_selected", engine="af_prompt_core")
        return PromptEngineBackend()
    except ImportError:
        logger.info(
            "prompt_engine_fallback",
            engine="stub",
            reason="af_prompt_core not available",
        )
        return StubPromptEngine()
