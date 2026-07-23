from __future__ import annotations

from permissions_server.infrastructure.auth._mock_users_fixture import load_mock_users


class MockOrgHierarchy:
    async def is_manager_of(self, manager_id: str, subject_id: str) -> bool:
        records = {r["id"]: r for r in load_mock_users()}
        current = records.get(subject_id)
        visited: set[str] = set()

        while current is not None:
            next_manager_id = current["manager_id"]
            if next_manager_id is None or next_manager_id in visited:
                return False
            if next_manager_id == manager_id:
                return True
            visited.add(next_manager_id)
            current = records.get(next_manager_id)

        return False

    async def subordinates_of(self, manager_id: str) -> list[str]:
        children_by_manager: dict[str, list[str]] = {}
        for record in load_mock_users():
            if record["manager_id"] is not None:
                children_by_manager.setdefault(record["manager_id"], []).append(
                    record["id"]
                )

        result: list[str] = []
        visited: set[str] = set()
        stack = list(children_by_manager.get(manager_id, []))
        while stack:
            user_id = stack.pop()
            if user_id in visited:
                continue
            visited.add(user_id)
            result.append(user_id)
            stack.extend(children_by_manager.get(user_id, []))

        return result
