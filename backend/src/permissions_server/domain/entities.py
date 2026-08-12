"""Pure domain entities. No FastAPI/SQLAlchemy imports allowed here."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class ResourceType(str, Enum):
    WORKSPACE = "workspace"
    FOLDER = "folder"
    MAP = "map"
    GROUP = "group"
    LAYER = "layer"


# Structural legality for the resource tree. Lives here, not in a repository or
# service, because it's a pure, stateless fact about the domain (OCP: a new
# resource type extends this dict, nothing that reads it needs to change).
_ALLOWED_CHILD_TYPES: dict[ResourceType, frozenset[ResourceType]] = {
    ResourceType.WORKSPACE: frozenset(
        {ResourceType.FOLDER, ResourceType.MAP, ResourceType.LAYER}
    ),
    ResourceType.FOLDER: frozenset(
        {ResourceType.FOLDER, ResourceType.MAP, ResourceType.LAYER}
    ),
    ResourceType.MAP: frozenset({ResourceType.GROUP, ResourceType.LAYER}),
    ResourceType.GROUP: frozenset({ResourceType.GROUP, ResourceType.LAYER}),
    ResourceType.LAYER: frozenset(),  # always a leaf
}


def is_valid_child(parent_type: ResourceType | None, child_type: ResourceType) -> bool:
    if parent_type is None:
        return child_type is ResourceType.WORKSPACE
    return child_type in _ALLOWED_CHILD_TYPES[parent_type]


# Types this permissions server treats as its own organizational structure —
# deleting one is a real, permanent removal, but only once it's empty (never a
# bulk-wipe of whatever's nested under it). Deliberately hand-listed rather than
# derived from _ALLOWED_CHILD_TYPES: Map is structurally capable of holding
# children too (Group/Layer), but Map/Layer represent data this server doesn't
# own — their deletion stays the existing unconditional-cascade path, since real
# deletion of that data is meant to be driven by the system that owns it, not by
# an empty-check here. Don't "simplify" this into bool(_ALLOWED_CHILD_TYPES[t]).
_ORGANIZATIONAL_TYPES: frozenset[ResourceType] = frozenset(
    {ResourceType.WORKSPACE, ResourceType.FOLDER, ResourceType.GROUP}
)


def is_organizational(resource_type: ResourceType) -> bool:
    return resource_type in _ORGANIZATIONAL_TYPES


@dataclass(frozen=True, slots=True)
class Resource:
    """One shape for all 5 resource kinds — no separate Map/Layer dataclasses.
    parent_id is None only for a Workspace (a tree root)."""

    id: str
    type: ResourceType
    name: str
    parent_id: str | None
    inherits_from_parent: bool = True
    """False cuts AccessResolver's ancestor climb at this node: this resource
    and everything below it get no role from anything above it (unless
    granted directly here or lower) — a per-resource inheritance barrier,
    independent of any specific grant or grantee."""
    owner_id: str | None = None
    """Set only for a lazily-created personal workspace — the user id whose
    workspace this is. None for every other resource, including
    superuser-created team workspaces (those get an assigned admin grant,
    not an owner)."""


class Role(str, Enum):
    VIEWER = "viewer"
    EDITOR = "editor"
    MANAGER = "manager"
    ADMIN = "admin"


_ROLE_RANK: dict[Role, int] = {
    Role.VIEWER: 1,
    Role.EDITOR: 2,
    Role.MANAGER: 3,
    Role.ADMIN: 4,
}


def role_rank(role: Role) -> int:
    return _ROLE_RANK[role]


class SystemRole(str, Enum):
    """System-wide bypass roles — no resource_id, never resource-scoped."""

    SUPER_EDITOR = "super_editor"
    SUPER_VIEWER = "super_viewer"


class GranteeType(str, Enum):
    USER = "user"
    TEAM = "team"


@dataclass(frozen=True, slots=True)
class Grantee:
    """A user-scope grantee (team_id=None) or a team-scope grantee (user_id=None)."""

    grantee_type: GranteeType
    user_id: str | None = None
    team_id: str | None = None

    def __post_init__(self) -> None:
        is_user = self.grantee_type is GranteeType.USER
        has_user_id = self.user_id is not None
        has_team_id = self.team_id is not None
        if is_user != has_user_id or is_user == has_team_id:
            raise ValueError(
                "Grantee must set exactly user_id (USER) xor team_id (TEAM), matching grantee_type"
            )


@dataclass(frozen=True, slots=True)
class Team:
    """No member list here — membership is mutable, queryable state owned by
    TeamRepository, not baked into this frozen entity."""

    id: str
    name: str


@dataclass(frozen=True, slots=True)
class PermissionGrant:
    grantee: Grantee
    resource_id: str
    role: Role
    granted_by: str


@dataclass(frozen=True, slots=True)
class Restriction:
    """A whitelist entry, not an additive grant. Same shape as PermissionGrant
    but a deliberately distinct type: a resource with any Restriction rows
    becomes gated — only grantees listed here get any access at/below it,
    overriding even an Admin grant, unless the actor is SUPER_EDITOR. See
    AccessResolver.effective_role for the exact precedence."""

    grantee: Grantee
    resource_id: str
    role: Role
    granted_by: str


class AuditAction(str, Enum):
    GRANT = "grant"
    REVOKE = "revoke"
    ROLE_CHANGE = "role_change"
    RESTRICT = "restrict"
    UNRESTRICT = "unrestrict"
    RESTRICTION_ROLE_CHANGE = "restriction_role_change"


@dataclass(frozen=True, slots=True)
class AuditLogEntry:
    id: str
    actor_id: str
    grantee: Grantee
    resource_id: str
    role: Role
    action: AuditAction
    timestamp: datetime


@dataclass(frozen=True, slots=True)
class AuthenticatedUser:
    id: str
    name: str
    email: str
