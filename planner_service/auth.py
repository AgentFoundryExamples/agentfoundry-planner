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
"""Authentication context and dependency for the planner service."""

from typing import Optional

from fastapi import Header
from pydantic import BaseModel, Field

from planner_service.logging import get_logger


class AuthContext(BaseModel):
    """Authentication context for the current request."""

    user_id: str = Field(..., description="Authenticated user identifier")
    token: Optional[str] = Field(None, description="Authentication token (if provided)")


def get_current_user(
    authorization: Optional[str] = Header(None),
) -> AuthContext:
    """Parse Authorization header and return authentication context.

    This is a stub implementation that returns a default user if no
    Authorization header is provided. In production, this would validate
    the token and extract the user identity.

    Args:
        authorization: The Authorization header value.

    Returns:
        AuthContext with user_id (stub user if header missing).
    """
    logger = get_logger(__name__)

    if not authorization:
        logger.warning(
            "auth_header_missing",
            message="Authorization header missing, using stub user for now",
        )
        return AuthContext(user_id="stub-user", token=None)

    # Expected format: "Bearer <token>"
    parts = authorization.split(" ", 1)
    if len(parts) != 2 or parts[0].lower() != "bearer":
        logger.warning(
            "auth_header_invalid_format",
            message="Invalid authorization format, using stub user",
        )
        return AuthContext(user_id="stub-user", token=None)

    token = parts[1]
    # Stub implementation: extract user from token or use default
    # In production, this would validate the token and extract user identity
    logger.debug("auth_token_received", token_length=len(token))
    return AuthContext(user_id="stub-user", token=token)
