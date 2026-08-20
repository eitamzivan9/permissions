"""Storage contract for the Workspace/Folder/Map/Group/Layer resource tree."""

from __future__ import annotations

from typing import Protocol

from permissions_server.domain.entities import Resource, ResourceType
from permissions_server.domain.ports.entity_repository import EntityRepository, Page


class ResourceRepository(EntityRepository[Resource], Protocol):
    async def children_of(self, resource_id: str) -> list[Resource]:
        """Direct children only, one level down."""
        ...

    async def path_to_root(self, resource_id: str) -> list[Resource]:
        """[root, ..., resource itself] — root-first, inclusive. Single-element
        list for a Workspace. This is the hook a Phase-2 ltree adapter turns
        into one indexed query; kept list-returning so Phase 1's O(depth) walk
        is a drop-in swap later, not a shape change."""
        ...

    async def list_by_type(
        self, resource_type: ResourceType, *, page: int, page_size: int, pinned_id: str | None = None
    ) -> Page[Resource]:
        """All resources of one type (e.g. every Workspace, or every Map),
        for the catalog's top-level pagination and /external/v1/my-access.
        `pinned_id`, if given and present in the result set, sorts that one
        resource first (page 1) ahead of the normal name ordering — used by
        CatalogService to always surface the caller's own personal workspace
        first, without disturbing pagination for anyone else (a real total
        order over the whole set, not a page-1-only splice)."""
        ...

    async def create(
        self,
        *,
        type: ResourceType,
        name: str,
        parent_id: str | None,
        inherits_from_parent: bool = True,
        owner_id: str | None = None,
    ) -> Resource:
        """Persists a new node. Parent/child type legality (is_valid_child) is
        the CALLER's job, not this repo's — the repo only knows how to store
        a row."""
        ...

    async def set_inherits_from_parent(self, resource_id: str, value: bool) -> Resource:
        """Flip the inheritance-barrier flag on an existing resource (see
        Resource.inherits_from_parent) without touching any grant."""
        ...

    async def find_workspace_by_owner(self, owner_id: str) -> Resource | None:
        """The caller's personal workspace (a WORKSPACE with owner_id set to
        them), or None if they've never lazily created one yet."""
        ...

    async def move(self, resource_id: str, new_parent_id: str) -> Resource:
        """Reparents resource_id (and implicitly its whole subtree) under
        new_parent_id. Legality (is_valid_child) and cycle-safety are the
        CALLER's job, matching create()'s existing contract."""
        ...

    async def descendant_ids(self, resource_id: str) -> list[str]:
        """resource_id itself plus every descendant's id, inclusive. Read-only
        — the CALLER uses this to clean up grants/restrictions referencing
        the subtree *before* calling delete(), since those rows have no
        FK-cascade onto resources."""
        ...

    async def delete(self, resource_id: str) -> None:
        """Removes resource_id and its entire subtree. The CALLER is
        responsible for first deleting any grants/restrictions referencing
        descendant_ids(resource_id) — this method only touches resource
        rows, matching create()'s "this repo only knows how to store a row"
        contract."""
        ...
