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
                    "SELECT id, type, name, parent_id, inherits_from_parent "
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
                )
                for row in result
            ]

    async def list_by_type(
        self, resource_type: ResourceType, *, page: int, page_size: int
    ) -> Page[Resource]:
        async with self._sessionmaker() as session:
            stmt = (
                select(ResourceModel)
                .where(ResourceModel.type == resource_type)
                .order_by(ResourceModel.name)
            )
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
