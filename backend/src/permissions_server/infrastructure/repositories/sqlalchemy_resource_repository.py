from __future__ import annotations

from uuid import uuid4

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from permissions_server.domain.entities import Resource, ResourceType
from permissions_server.domain.ports.entity_repository import Page
from permissions_server.infrastructure.db.models import ResourceModel
from permissions_server.infrastructure.db.types import sanitize_label
from permissions_server.infrastructure.repositories._pagination import paginate


def _to_domain(model: ResourceModel) -> Resource:
    return Resource(
        id=model.id,
        type=model.type,
        name=model.name,
        parent_id=model.parent_id,
        inherits_from_parent=model.inherits_from_parent,
        owner_id=model.owner_id,
    )


class SqlAlchemyResourceRepository:
    def __init__(self, sessionmaker: async_sessionmaker[AsyncSession]) -> None:
        self._sessionmaker = sessionmaker

    async def get_by_id(self, entity_id: str) -> Resource | None:
        async with self._sessionmaker() as session:
            model = await session.get(ResourceModel, entity_id)
            return _to_domain(model) if model else None

    async def list_page(self, *, search: str | None, page: int, page_size: int) -> Page[Resource]:
        async with self._sessionmaker() as session:
            stmt = select(ResourceModel)
            if search:
                stmt = stmt.where(ResourceModel.name.ilike(f"%{search}%"))
            stmt = stmt.order_by(ResourceModel.name)
            rows, total = await paginate(session, stmt, page=page, page_size=page_size)
            return Page(
                items=[_to_domain(r) for r in rows], total=total, page=page, page_size=page_size
            )

    async def children_of(self, resource_id: str) -> list[Resource]:
        async with self._sessionmaker() as session:
            stmt = (
                select(ResourceModel)
                .where(ResourceModel.parent_id == resource_id)
                .order_by(ResourceModel.name)
            )
            rows = (await session.execute(stmt)).scalars().all()
            return [_to_domain(r) for r in rows]

    async def path_to_root(self, resource_id: str) -> list[Resource]:
        async with self._sessionmaker() as session:
            leaf = await session.get(ResourceModel, resource_id)
            if leaf is None:
                return []
            # One indexed ltree containment query instead of an O(depth)
            # parent_id walk: every ancestor (inclusive) is a row whose path
            # is a prefix of the leaf's path.
            result = await session.execute(
                text(
                    "SELECT id, type, name, parent_id, inherits_from_parent, owner_id "
                    "FROM resources WHERE path @> CAST(:leaf_path AS ltree) "
                    "ORDER BY nlevel(path)"
                ),
                {"leaf_path": leaf.path},
            )
            return [
                Resource(
                    id=row.id,
                    type=ResourceType(row.type),
                    name=row.name,
                    parent_id=row.parent_id,
                    inherits_from_parent=row.inherits_from_parent,
                    owner_id=row.owner_id,
                )
                for row in result
            ]

    async def list_by_type(
        self, resource_type: ResourceType, *, page: int, page_size: int, pinned_id: str | None = None
    ) -> Page[Resource]:
        async with self._sessionmaker() as session:
            stmt = select(ResourceModel).where(ResourceModel.type == resource_type)
            if pinned_id is not None:
                stmt = stmt.order_by((ResourceModel.id == pinned_id).desc(), ResourceModel.name)
            else:
                stmt = stmt.order_by(ResourceModel.name)
            rows, total = await paginate(session, stmt, page=page, page_size=page_size)
            return Page(
                items=[_to_domain(r) for r in rows], total=total, page=page, page_size=page_size
            )

    async def create(
        self,
        *,
        type: ResourceType,
        name: str,
        parent_id: str | None,
        inherits_from_parent: bool = True,
        owner_id: str | None = None,
    ) -> Resource:
        new_id = uuid4().hex
        async with self._sessionmaker() as session:
            parent_path: str | None = None
            if parent_id is not None:
                parent = await session.get(ResourceModel, parent_id)
                parent_path = parent.path if parent else None
            label = sanitize_label(new_id)
            path = f"{parent_path}.{label}" if parent_path else label

            model = ResourceModel(
                id=new_id,
                type=type,
                name=name,
                parent_id=parent_id,
                inherits_from_parent=inherits_from_parent,
                path=path,
                owner_id=owner_id,
            )
            session.add(model)
            await session.commit()
            return _to_domain(model)

    async def set_inherits_from_parent(self, resource_id: str, value: bool) -> Resource:
        async with self._sessionmaker() as session:
            model = await session.get(ResourceModel, resource_id)
            if model is None:
                raise KeyError(resource_id)
            model.inherits_from_parent = value
            await session.commit()
            return _to_domain(model)

    async def find_workspace_by_owner(self, owner_id: str) -> Resource | None:
        async with self._sessionmaker() as session:
            stmt = select(ResourceModel).where(
                ResourceModel.type == ResourceType.WORKSPACE,
                ResourceModel.owner_id == owner_id,
            )
            model = (await session.execute(stmt)).scalar_one_or_none()
            return _to_domain(model) if model else None

    async def move(self, resource_id: str, new_parent_id: str) -> Resource:
        async with self._sessionmaker() as session:
            resource = await session.get(ResourceModel, resource_id)
            if resource is None:
                raise KeyError(resource_id)
            new_parent = await session.get(ResourceModel, new_parent_id)
            if new_parent is None:
                raise KeyError(new_parent_id)

            old_path = resource.path
            new_path = f"{new_parent.path}.{sanitize_label(resource.id)}"

            # Reattach every descendant's subtree in one statement: strip the
            # prefix up to and including the moved node (subpath(path,
            # nlevel(old_path))) and reattach it under new_path. The moved
            # node's own row is excluded here (id != :resource_id) and
            # updated directly below via the ORM instead, so both writes
            # commit together in one transaction — no orphaned or duplicated
            # descendants on partial failure.
            await session.execute(
                text(
                    "UPDATE resources "
                    "SET path = CAST(:new_path AS ltree) "
                    "  || subpath(path, nlevel(CAST(:old_path AS ltree))) "
                    "WHERE path <@ CAST(:old_path AS ltree) AND id != :resource_id"
                ),
                {"new_path": new_path, "old_path": old_path, "resource_id": resource_id},
            )
            resource.parent_id = new_parent_id
            resource.path = new_path
            await session.commit()
            await session.refresh(resource)
            return _to_domain(resource)

    async def descendant_ids(self, resource_id: str) -> list[str]:
        async with self._sessionmaker() as session:
            leaf = await session.get(ResourceModel, resource_id)
            if leaf is None:
                return []
            result = await session.execute(
                text("SELECT id FROM resources WHERE path <@ CAST(:leaf_path AS ltree)"),
                {"leaf_path": leaf.path},
            )
            return [row.id for row in result]

    async def delete(self, resource_id: str) -> None:
        async with self._sessionmaker() as session:
            leaf = await session.get(ResourceModel, resource_id)
            if leaf is None:
                return
            await session.execute(
                text("DELETE FROM resources WHERE path <@ CAST(:leaf_path AS ltree)"),
                {"leaf_path": leaf.path},
            )
            await session.commit()
