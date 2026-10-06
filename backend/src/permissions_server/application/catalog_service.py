"""Builds the searchable, paginated resource catalog for the UI. A caller
only sees what they can reach (confirmed 2026-10-06 — replaces the earlier
universal-visibility design): a resource appears iff its can_fetch is true,
i.e. the caller has a role there OR at any descendant. The ancestors of a
reachable resource therefore still appear (with no role of their own) so the
tree shows where it lives; everything else is hidden. The caller's own
personal workspace is always shown. System-role holders reach everything, so
nothing is hidden from them."""

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
    """Only children with can_fetch=True — unreachable branches are pruned."""


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
        """No search: paginate over top-level Workspaces, each with its
        (pruned) subtree nested inside. With search: paginate over every
        visible resource (any type, any depth) whose name matches, each
        returned as a top-level item with its own pruned subtree.

        No-search only: the caller's own personal workspace (if they have one)
        is always pinned first, so it's visible without hunting for it in the
        alphabetical/paginated list — confirmed 2026-07-31."""
        snapshot = await self._access_resolver.snapshot_for_user(user_id)
        my_workspace = await self._resource_repository.find_workspace_by_owner(user_id)
        pinned_id = my_workspace.id if my_workspace else None

        if self._access_resolver.reaches_everything(snapshot):
            return await self._unfiltered_page(snapshot, search, pinned_id, page, page_size)

        items = await self._reachable_items(snapshot, search, my_workspace)
        start = (page - 1) * page_size
        return Page(
            items=items[start : start + page_size],
            total=len(items),
            page=page,
            page_size=page_size,
        )

    async def _unfiltered_page(
        self,
        snapshot: AccessSnapshot,
        search: str | None,
        pinned_id: str | None,
        page: int,
        page_size: int,
    ) -> Page[CatalogItem]:
        """Nothing is hidden from this caller, so the repository's own
        pagination over the whole tree is already exact."""
        if search:
            resource_page = await self._resource_repository.list_page(
                search=search, page=page, page_size=page_size
            )
        else:
            resource_page = await self._resource_repository.list_by_type(
                ResourceType.WORKSPACE, page=page, page_size=page_size, pinned_id=pinned_id
            )
        return Page(
            items=[await self._build_node(r, snapshot) for r in resource_page.items],
            total=resource_page.total,
            page=resource_page.page,
            page_size=resource_page.page_size,
        )

    async def _reachable_items(
        self, snapshot: AccessSnapshot, search: str | None, my_workspace: Resource | None
    ) -> list[CatalogItem]:
        """Every visible top-level item, sorted. Starts from the caller's
        access anchors (their own grants/whitelist entries — bounded by what
        they hold, not by the size of the tree) rather than scanning every
        workspace, so pagination over the result is exact."""
        pinned_id = my_workspace.id if my_workspace else None
        root_resources = {my_workspace.id: my_workspace} if my_workspace else {}
        for anchor_id in await self._access_resolver.access_anchor_ids(snapshot):
            path = await self._resource_repository.path_to_root(anchor_id)
            if path:
                root_resources[path[0].id] = path[0]

        roots: list[CatalogItem] = []
        for resource in root_resources.values():
            node = await self._build_node(resource, snapshot)
            if node.can_fetch or node.id == pinned_id:
                roots.append(node)

        if not search:
            return sorted(roots, key=lambda n: (n.id != pinned_id, n.name))

        # Same case-insensitive substring match the repositories' list_page uses.
        query = search.lower()
        matches = [n for n in self._flatten(roots) if query in n.name.lower()]
        return sorted(matches, key=lambda n: n.name)

    @classmethod
    def _flatten(cls, nodes: list[CatalogItem]) -> list[CatalogItem]:
        flat: list[CatalogItem] = []
        for node in nodes:
            flat.append(node)
            flat.extend(cls._flatten(node.children))
        return flat

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
            children=[child for child in children if child.can_fetch],
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
