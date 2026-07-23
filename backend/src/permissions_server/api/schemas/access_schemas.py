from __future__ import annotations

from typing import Literal

from pydantic import BaseModel

from permissions_server.domain.entities import Role, SystemRole


class AccessSourceOut(BaseModel):
    grantee_type: Literal["user", "team"] | None
    user_id: str | None
    team_id: str | None
    system_role: SystemRole | None
    origin_resource_id: str | None
    role: Role
    is_effective: bool
