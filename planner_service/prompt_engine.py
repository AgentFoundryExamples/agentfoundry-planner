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
"""Prompt engine abstraction for delegating plan generation to pluggable prompt logic (AF v1.1)."""

from typing import Protocol, runtime_checkable

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
            - plan_version: Version of the plan output schema
            - repository: Repository metadata (owner, name, ref)
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
            ctx: The planning context containing project and user input (AF v1.1).

        Returns:
            A dictionary with deterministic output including request_id,
            plan_version (af/1.1-stub), repository metadata, mirrored context
            and user_input data, status, and a prompt preview.
        """
        # Use the request_id from the PlanningContext to maintain consistency
        request_id = str(ctx.request_id)

        # Extract repository metadata from the first/primary project context
        project = ctx.projects[0] if ctx.projects else None
        if project:
            repository_metadata = {
                "owner": project.repo_owner,
                "name": project.repo_name,
                "ref": project.ref,
            }
            repo_str = f"{project.repo_owner}/{project.repo_name}"
        else:
            repository_metadata = {"owner": "", "name": "", "ref": ""}
            repo_str = "unknown/unknown"

        # Log request metadata for debugging
        self._logger.info(
            "stub_prompt_engine_run",
            request_id=request_id,
            repository=repo_str,
        )

        # Build deterministic prompt preview (does not expose real prompts)
        base_preview = f"[STUB] Planning request for {repo_str}: "
        purpose = ctx.user_input.purpose
        if len(purpose) > 50:
            prompt_preview = f"{base_preview}{purpose[:50]}..."
        else:
            prompt_preview = f"{base_preview}{purpose}"

        # Mirror user_input data for validator inspection
        user_input_mirror = {
            "purpose": ctx.user_input.purpose,
            "vision": ctx.user_input.vision,
            "must": list(ctx.user_input.must),
            "dont": list(ctx.user_input.dont),
            "nice": list(ctx.user_input.nice),
        }

        # Mirror context data (projects list) for validator inspection
        context_mirror = [
            {
                "repo_owner": p.repo_owner,
                "repo_name": p.repo_name,
                "ref": p.ref,
                "tree_json": p.tree_json,
                "dependency_json": p.dependency_json,
                "summary_json": p.summary_json,
            }
            for p in ctx.projects
        ]

        return {
            "request_id": request_id,
            "plan_version": "af/1.1-stub",
            "repository": repository_metadata,
            "user_input": user_input_mirror,
            "context": context_mirror,
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
