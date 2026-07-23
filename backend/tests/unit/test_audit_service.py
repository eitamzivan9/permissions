from permissions_server.domain.entities import AuditAction, AuthenticatedUser, Grantee, GranteeType, Role

MAP_ID = "map-city-roads"
ACTOR = AuthenticatedUser(id="u001", name="Dana Whitfield", email="dana.whitfield@geoteam.example")
GRANTEE = Grantee(GranteeType.USER, user_id="u016")


async def test_record_grant_and_revoke_then_history_for_resource(audit_service):
    await audit_service.record_grant(ACTOR, GRANTEE, MAP_ID, Role.EDITOR)
    await audit_service.record_revoke(ACTOR, GRANTEE, MAP_ID, Role.EDITOR)

    page = await audit_service.history_for_resource(MAP_ID, page=1, page_size=10)
    assert page.total == 2
    # newest first
    assert page.items[0].action is AuditAction.REVOKE
    assert page.items[1].action is AuditAction.GRANT


async def test_history_for_actor(audit_service):
    await audit_service.record_grant(ACTOR, GRANTEE, MAP_ID, Role.VIEWER)
    page = await audit_service.history_for_actor(ACTOR.id, page=1, page_size=10)
    assert page.total == 1
    assert page.items[0].actor_id == ACTOR.id


async def test_record_role_change(audit_service):
    await audit_service.record_role_change(ACTOR, GRANTEE, MAP_ID, Role.MANAGER)
    page = await audit_service.history_for_resource(MAP_ID, page=1, page_size=10)
    assert page.total == 1
    assert page.items[0].action is AuditAction.ROLE_CHANGE
    assert page.items[0].role is Role.MANAGER
