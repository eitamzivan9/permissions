"""Shared by PermissionGrantService.can_manage and RestrictionService's own
delegation check, so the 'Team grantees skip the org-chart check, User
grantees require it (unless the resource is the actor's own personal
workspace)' rule exists exactly once (DIP: both depend only on the
OrgHierarchy/ResourceRepository ports, never on each other)."""

from __future__ import annotations

from permissions_server.domain.entities import Grantee, GranteeType
from permissions_server.domain.ports.org_hierarchy import OrgHierarchy
from permissions_server.domain.ports.resource_repository import ResourceRepository


async def grantee_passes_org_chart_check(
    org_hierarchy: OrgHierarchy,
    resource_repository: ResourceRepository,
    actor_id: str,
    grantee: Grantee,
    resource_id: str,
) -> bool:
    if grantee.grantee_type is GranteeType.TEAM:
        return True
    assert grantee.user_id is not None
    if grantee.user_id == actor_id:
        # Nobody is their own org-chart manager (is_manager_of(x, x) is
        # always False), but that's not the intent of the org-chart rule —
        # it exists to gate delegation to OTHER people. An actor managing
        # their own entry (e.g. self-listing on a restriction whitelist)
        # isn't delegation at all, so the org-chart check doesn't apply.
        # Role-rank gates (Manager+/Admin) still apply unchanged wherever
        # this is called from.
        return True
    if await is_within_actors_personal_workspace(resource_repository, actor_id, resource_id):
        return True
    return await org_hierarchy.is_manager_of(actor_id, grantee.user_id)


async def is_within_actors_personal_workspace(
    resource_repository: ResourceRepository, actor_id: str, resource_id: str
) -> bool:
    """A personal workspace's owner has full authority over its whole
    subtree, regardless of the org chart — it's their own sandbox, not
    something they manage by reporting-line authority."""
    return await personal_workspace_owner_id(resource_repository, resource_id) == actor_id


async def personal_workspace_owner_id(
    resource_repository: ResourceRepository, resource_id: str
) -> str | None:
    """The owner of the personal workspace resource_id lives in, or None if
    it's in a team/shared workspace. Only a Workspace can be a tree root, so
    path[0] (root-first) is the personal workspace itself whenever one
    exists on this path."""
    path = await resource_repository.path_to_root(resource_id)
    return path[0].owner_id if path else None
