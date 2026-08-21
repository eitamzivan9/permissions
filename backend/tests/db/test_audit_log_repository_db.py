"""Exercises SqlAlchemyAuditLogRepository against real Postgres, including
_pagination.paginate (via list_for_resource/list_for_actor) and the
newest-first ordering the append-only log relies on."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import uuid4

from permissions_server.domain.entities import AuditAction, AuditLogEntry, Grantee, GranteeType, Role


def _entry(*, resource_id: str, actor_id: str, when: datetime) -> AuditLogEntry:
    return AuditLogEntry(
        id=uuid4().hex,
        actor_id=actor_id,
        grantee=Grantee(GranteeType.USER, user_id="u999"),
        resource_id=resource_id,
        role=Role.EDITOR,
        action=AuditAction.GRANT,
        timestamp=when,
    )


async def test_append_then_list_for_resource(audit_log_repo):
    now = datetime.now(timezone.utc)
    await audit_log_repo.append(_entry(resource_id="ws-1", actor_id="u000", when=now))

    page = await audit_log_repo.list_for_resource("ws-1", page=1, page_size=10)
    assert page.total == 1
    assert page.items[0].resource_id == "ws-1"


async def test_list_for_resource_orders_newest_first(audit_log_repo):
    now = datetime.now(timezone.utc)
    older = _entry(resource_id="ws-1", actor_id="u000", when=now - timedelta(minutes=5))
    newer = _entry(resource_id="ws-1", actor_id="u000", when=now)
    await audit_log_repo.append(older)
    await audit_log_repo.append(newer)

    page = await audit_log_repo.list_for_resource("ws-1", page=1, page_size=10)
    assert [e.id for e in page.items] == [newer.id, older.id]


async def test_list_for_actor_filters_by_actor(audit_log_repo):
    now = datetime.now(timezone.utc)
    mine = _entry(resource_id="ws-1", actor_id="u001", when=now)
    someone_elses = _entry(resource_id="ws-1", actor_id="u002", when=now)
    await audit_log_repo.append(mine)
    await audit_log_repo.append(someone_elses)

    page = await audit_log_repo.list_for_actor("u001", page=1, page_size=10)
    assert [e.id for e in page.items] == [mine.id]


async def test_list_for_resource_paginates(audit_log_repo):
    now = datetime.now(timezone.utc)
    for i in range(5):
        await audit_log_repo.append(
            _entry(resource_id="ws-1", actor_id="u000", when=now - timedelta(minutes=i))
        )

    page = await audit_log_repo.list_for_resource("ws-1", page=1, page_size=2)
    assert len(page.items) == 2
    assert page.total == 5
