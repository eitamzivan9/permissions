"""Builds the searchable, paginated resource catalog for the UI. Visibility
stays universal by explicit design choice (see plan.md): every resource is
shown to every user, annotated with their own effective role, including no
role at all — never filtered by access. ONE deliberate exception (confirmed
2026-07-31): another user's personal workspace (and everything inside it) is
hidden entirely from a caller who can't reach any of it — everyone still sees
their OWN personal workspace, and every non-personal (team/shared) resource
stays universally visible regardless of access, unchanged."""

from __future__ import annotations

from dataclasses import dataclass

from permissions_server.application.access_resolver import AccessResolver, AccessSnapshot
from permissions_server.domain.entities import Resource, ResourceType, Role, role_rank
from permissions_server.domain.ports.entity_repository import Page
from permissions_server.domain.ports.resource_repository import ResourceRepository


@dataclass(frozen=True, slots=True)
class CatalogItem:
    id: str
    type: ResourceType
    name: str
    effective_role: Role | None
    can_manage: bool
    can_fetch: bool
    """True if the caller has a role at this node OR at any descendant — e.g.
    a Map with no role of its own is still fetchable if the caller can see
    just one Layer inside it, since the map has to be fetched to render that
    layer at all. Bubbles up from children; never just this node's own role."""
    children: list["CatalogItem"]


@dataclass(frozen=True, slots=True)
class ExternalAccessItem:
    id: str
    name: str
    role: Role | None


class CatalogService:
    def __init__(
        self, resource_repository: ResourceRepository, access_resolver: AccessResolver
    ) -> None:
        self._resource_repository = resource_repository
        self._access_resolver = access_resolver

    async def get_catalog(
        self, user_id: str, *, search: str | None, page: int, page_size: int
    ) -> Page[CatalogItem]:
        """No search: paginate over top-level Workspaces, each with its full
        subtree nested inside. With search: paginate over every resource (any
        type, any depth) whose name matches, each returned as a top-level
        item with its own full subtree — the same 'search finds a resource,
        return it with everything under it' shape the old flat map search
        had, generalized to N levels. Either way nothing is filtered by
        access; only `effective_role`/`can_manage` vary per caller.

        No-search only: the caller's own personal workspace (if they have one)
        is always pinned first, so it's visible without hunting for it in the
        alphabetical/paginated list — confirmed 2026-07-31."""
        snapshot = await self._access_resolver.snapshot_for_user(user_id)

        if search:
            resource_page = await self._resource_repository.list_page(
                search=search, page=page, page_size=page_size
            )
        else:
            my_workspace = await self._resource_repository.find_workspace_by_owner(user_id)
            resource_page = await self._resource_repository.list_by_type(
                ResourceType.WORKSPACE,
                page=page,
                page_size=page_size,
                pinned_id=my_workspace.id if my_workspace else None,
            )

        # Same "may return fewer than page_size" pattern as get_external_access
        # below: total/page reflect the unfiltered universe from the repo,
        # items are filtered afterward (here, someone else's personal
        # workspace the caller can't reach anywhere inside — see module
        # docstring). node.can_fetch already means "reachable at this node OR
        # any descendant," which is exactly the right test — a caller with an
        # explicit grant deep inside someone else's workspace can still reach
        # (and see) that specific branch, not just an all-or-nothing gate.
        items = []
        for resource in resource_page.items:
            node = await self._build_node(resource, snapshot)
            if await self._is_hidden_other_personal_workspace(resource, user_id, node.can_fetch):
                continue
            items.append(node)

        return Page(
            items=items,
            total=resource_page.total,
            page=resource_page.page,
            page_size=resource_page.page_size,
        )

    async def _is_hidden_other_personal_workspace(
        self, resource: Resource, user_id: str, can_fetch: bool
    ) -> bool:
        if can_fetch:
            return False
        if resource.type is ResourceType.WORKSPACE:
            root = resource
        else:
            path = await self._resource_repository.path_to_root(resource.id)
            root = path[0] if path else resource
        return root.owner_id is not None and root.owner_id != user_id

    async def _build_node(self, resource: Resource, snapshot: AccessSnapshot) -> CatalogItem:
        effective_role = await self._access_resolver.effective_role(resource.id, snapshot=snapshot)
        child_resources = await self._resource_repository.children_of(resource.id)
        children = [await self._build_node(child, snapshot) for child in child_resources]
        return CatalogItem(
            id=resource.id,
            type=resource.type,
            name=resource.name,
            effective_role=effective_role,
            can_manage=effective_role is not None
            and role_rank(effective_role) >= role_rank(Role.MANAGER),
            can_fetch=effective_role is not None or any(child.can_fetch for child in children),
            children=children,
        )

    async def get_external_access(
        self, user_id: str, *, page: int, page_size: int
    ) -> Page[ExternalAccessItem]:
        """Flat view for /external/v1/my-access: only Maps the caller can
        actually reach — matches the docx's Q1 'which maps can this user
        see'. A Map counts as reachable if it has its own role OR any Layer
        inside it does (same can_fetch bubbling as get_catalog — reuses
        _build_node rather than re-deriving reachability here). Paginates
        over the full universe of Maps, so total/page reflect all maps, not
        the filtered count — a page's items may hold fewer than page_size
        entries if some maps in that page are unreachable to this caller."""
        map_page = await self._resource_repository.list_by_type(
            ResourceType.MAP, page=page, page_size=page_size
        )
        snapshot = await self._access_resolver.snapshot_for_user(user_id)

        items: list[ExternalAccessItem] = []
        for map_resource in map_page.items:
            node = await self._build_node(map_resource, snapshot)
            if node.can_fetch:
                items.append(
                    ExternalAccessItem(id=node.id, name=node.name, role=node.effective_role)
                )

        return Page(
            items=items, total=map_page.total, page=map_page.page, page_size=map_page.page_size
        )
