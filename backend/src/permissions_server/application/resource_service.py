"""Orchestrates every resource-creation flow (child creation, personal
workspace get-or-create, superuser team-workspace creation) and move — each
is validate -> authorize -> write -> auto-grant, so this lives here rather
than duplicated per-flow in a router."""

from __future__ import annotations

from permissions_server.application.access_resolver import AccessResolver
from permissions_server.application.permission_grant_service import PermissionGrantService
from permissions_server.domain.entities import (
    AuthenticatedUser,
    Resource,
    ResourceType,
    Role,
    SystemRole,
    is_organizational,
    is_valid_child,
    role_rank,
)
from permissions_server.domain.errors import ConflictError, ForbiddenError, NotFoundError
from permissions_server.domain.ports.grant_repository import PermissionGrantRepository
from permissions_server.domain.ports.resource_repository import ResourceRepository
from permissions_server.domain.ports.restriction_repository import RestrictionRepository


class ResourceService:
    def __init__(
        self,
        resource_repository: ResourceRepository,
        access_resolver: AccessResolver,
        permission_grant_service: PermissionGrantService,
        grant_repository: PermissionGrantRepository,
        restriction_repository: RestrictionRepository,
    ) -> None:
        self._resource_repository = resource_repository
        self._access_resolver = access_resolver
        self._permission_grant_service = permission_grant_service
        self._grant_repository = grant_repository
        self._restriction_repository = restriction_repository

    async def create_child(
        self, actor: AuthenticatedUser, *, type: ResourceType, name: str, parent_id: str
    ) -> Resource:
        """Editor+ at the parent may add a child under it — 'editor can edit
        content'. The creator becomes that child's Admin ('admin is whoever
        published it'); hierarchy from there ('admin at a map is admin at its
        layers') falls out of AccessResolver's existing nearest-ancestor-wins
        climb, no special-case code needed."""
        parent = await self._resource_repository.get_by_id(parent_id)
        if parent is None:
            raise NotFoundError(f"no resource with id {parent_id}")
        if not is_valid_child(parent.type, type):
            raise ConflictError(f"{type.value} cannot be a child of {parent.type.value}")

        actor_role = await self._access_resolver.effective_role(parent_id, user_id=actor.id)
        if actor_role is None or role_rank(actor_role) < role_rank(Role.EDITOR):
            raise ForbiddenError(f"{actor.id} may not create a child of {parent_id}")

        resource = await self._resource_repository.create(type=type, name=name, parent_id=parent_id)
        await self._permission_grant_service.bootstrap_admin_grant(actor, actor.id, resource.id)
        return resource

    async def get_or_create_my_workspace(self, actor: AuthenticatedUser) -> Resource:
        """Lazy personal workspace: any authenticated user may fetch (or, on
        first call, create) their own sandbox, self-admin by construction.
        Idempotent — repeat calls return the same resource."""
        existing = await self._resource_repository.find_workspace_by_owner(actor.id)
        if existing is not None:
            return existing

        resource = await self._resource_repository.create(
            type=ResourceType.WORKSPACE,
            name=f"{actor.name}'s Workspace",
            parent_id=None,
            owner_id=actor.id,
        )
        await self._permission_grant_service.bootstrap_admin_grant(actor, actor.id, resource.id)
        return resource

    async def create_team_workspace(
        self, actor: AuthenticatedUser, *, name: str, admin_user_id: str
    ) -> Resource:
        """Superuser-only. The specified admin_user_id — not necessarily the
        caller — ends up Admin on the new workspace."""
        snapshot = await self._access_resolver.snapshot_for_user(actor.id)
        if SystemRole.SUPER_EDITOR not in snapshot.system_roles:
            raise ForbiddenError(f"{actor.id} may not create a team workspace")

        resource = await self._resource_repository.create(
            type=ResourceType.WORKSPACE, name=name, parent_id=None
        )
        await self._permission_grant_service.bootstrap_admin_grant(
            actor, admin_user_id, resource.id
        )
        return resource

    async def move(
        self, actor: AuthenticatedUser, resource_id: str, new_parent_id: str
    ) -> Resource:
        """Actor must be Admin (hierarchical) at the resource being moved and
        Editor+ at the destination. Both checks go through the same
        restriction-aware AccessResolver, so a restricted destination or
        source blocks the move for free."""
        resource = await self._resource_repository.get_by_id(resource_id)
        if resource is None:
            raise NotFoundError(f"no resource with id {resource_id}")
        destination = await self._resource_repository.get_by_id(new_parent_id)
        if destination is None:
            raise NotFoundError(f"no resource with id {new_parent_id}")
        if not is_valid_child(destination.type, resource.type):
            raise ConflictError(
                f"{resource.type.value} cannot be a child of {destination.type.value}"
            )

        destination_ancestors = await self._resource_repository.path_to_root(new_parent_id)
        if any(ancestor.id == resource_id for ancestor in destination_ancestors):
            raise ConflictError("cannot move a resource into its own subtree")

        source_role = await self._access_resolver.effective_role(resource_id, user_id=actor.id)
        if source_role is not Role.ADMIN:
            raise ForbiddenError(f"{actor.id} is not Admin at {resource_id}")

        dest_role = await self._access_resolver.effective_role(new_parent_id, user_id=actor.id)
        if dest_role is None or role_rank(dest_role) < role_rank(Role.EDITOR):
            raise ForbiddenError(f"{actor.id} is not Editor+ at {new_parent_id}")

        return await self._resource_repository.move(resource_id, new_parent_id)

    async def delete(self, actor: AuthenticatedUser, resource_id: str) -> None:
        """Admin-only, same rank as move()'s source-resource check — deleting
        is at least as destructive as moving one away. For organizational
        types (Workspace/Folder/Group) this only ever removes a single empty
        node — see is_organizational(). Map/Layer keep the original
        unconditional-cascade behavior: every grant and restriction anywhere
        in the subtree is cleaned up first (no FK-cascade from resources onto
        those tables), then the resource rows themselves, in one pass, never
        a second near-copy path per resource type."""
        resource = await self._resource_repository.get_by_id(resource_id)
        if resource is None:
            raise NotFoundError(f"no resource with id {resource_id}")

        actor_role = await self._access_resolver.effective_role(resource_id, user_id=actor.id)
        if actor_role is not Role.ADMIN:
            raise ForbiddenError(f"{actor.id} is not Admin at {resource_id}")

        if is_organizational(resource.type):
            children = await self._resource_repository.children_of(resource_id)
            if children:
                raise ConflictError(
                    f"{resource_id} has {len(children)} child resource(s); "
                    "remove them before deleting"
                )

        ids = await self._resource_repository.descendant_ids(resource_id)
        await self._grant_repository.delete_grants_for_resource_ids(ids)
        await self._restriction_repository.delete_restrictions_for_resource_ids(ids)
        await self._resource_repository.delete(resource_id)
