"""Wire schemas for api/routers/audit_router.py."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel

from permissions_server.domain.entities import AuditAction, Role


class AuditLogEntryOut(BaseModel):
    id: str
    actor_id: str
    grantee_type: Literal["user", "team"]
    user_id: str | None
    team_id: str | None
    resource_id: str
    role: Role
    action: AuditAction
    timestamp: datetime


class AuditLogPageOut(BaseModel):
    items: list[AuditLogEntryOut]
    total: int
    page: int
    page_size: int
