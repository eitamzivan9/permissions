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
    if await is_within_actors_personal_workspace(resource_repository, actor_id, resource_id):
        return True
    return await org_hierarchy.is_manager_of(actor_id, grantee.user_id)


async def is_within_actors_personal_workspace(
    resource_repository: ResourceRepository, actor_id: str, resource_id: str
) -> bool:
    """A personal workspace's owner has full authority over its whole
    subtree, regardless of the org chart — it's their own sandbox, not
    something they manage by reporting-line authority. Only a Workspace can
    be a tree root, so path[0] (root-first) is the personal workspace itself
    whenever one exists on this path."""
    path = await resource_repository.path_to_root(resource_id)
    return bool(path) and path[0].owner_id == actor_id
