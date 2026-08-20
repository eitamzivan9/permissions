import pytest

from permissions_server.application.access_transparency_service import GranteeInfo
from permissions_server.domain.entities import (
    AuthenticatedUser,
    Grantee,
    GranteeType,
    Role,
    SystemRole,
)
from permissions_server.domain.errors import ForbiddenError

MAP_ID = "map-city-roads"
SUBJECT_ID = "u016"
ACTOR = AuthenticatedUser(id="u001", name="Dana Whitfield", email="dana.whitfield@geoteam.example")
SUBJECT_GRANTEE = Grantee(GranteeType.USER, user_id=SUBJECT_ID)


async def test_explain_access_empty_when_no_grant(access_transparency_service):
    sources = await access_transparency_service.explain_access(SUBJECT_ID, MAP_ID)
    assert sources == []


async def test_explain_access_marks_the_winning_source_effective(
    access_transparency_service, grant_repo
):
    team_grantee = Grantee(GranteeType.TEAM, team_id="team-north-ops")
    await grant_repo.upsert_grant(team_grantee, MAP_ID, Role.VIEWER, granted_by="mgr")
    await grant_repo.upsert_grant(SUBJECT_GRANTEE, MAP_ID, Role.ADMIN, granted_by="mgr")

    sources = await access_transparency_service.explain_access(SUBJECT_ID, MAP_ID)
    assert len(sources) == 2
    effective = [s for s in sources if s.is_effective]
    assert len(effective) == 1
    assert effective[0].role is Role.ADMIN
    assert effective[0].grantee == SUBJECT_GRANTEE


async def test_check_access_forbidden_when_actor_lacks_manager_role(
    access_transparency_service, grant_repo
):
    await grant_repo.upsert_grant(SUBJECT_GRANTEE, MAP_ID, Role.VIEWER, granted_by="mgr")
    with pytest.raises(ForbiddenError):
        await access_transparency_service.check_access(ACTOR, SUBJECT_ID, MAP_ID)


async def test_explain_access_includes_system_role_source(
    access_transparency_service, system_role_repo
):
    await system_role_repo.grant_system_role(SUBJECT_ID, SystemRole.SUPER_EDITOR, granted_by="root")
    sources = await access_transparency_service.explain_access(SUBJECT_ID, MAP_ID)
    assert len(sources) == 1
    assert sources[0].grantee is None
    assert sources[0].system_role is SystemRole.SUPER_EDITOR
    assert sources[0].role is Role.ADMIN
    assert sources[0].is_effective is True


async def test_check_access_succeeds_when_actor_is_manager(access_transparency_service, grant_repo):
    actor_grantee = Grantee(GranteeType.USER, user_id=ACTOR.id)
    await grant_repo.upsert_grant(actor_grantee, MAP_ID, Role.MANAGER, granted_by="seed")
    await grant_repo.upsert_grant(SUBJECT_GRANTEE, MAP_ID, Role.VIEWER, granted_by="mgr")

    sources = await access_transparency_service.check_access(ACTOR, SUBJECT_ID, MAP_ID)
    assert any(s.role is Role.VIEWER for s in sources)


# --- list_admins: "who do I ask" ---


async def test_list_admins_empty_with_no_grants(access_transparency_service):
    assert await access_transparency_service.list_admins(MAP_ID) == []


async def test_list_admins_resolves_user_display_name(access_transparency_service, grant_repo):
    await grant_repo.upsert_grant(SUBJECT_GRANTEE, MAP_ID, Role.ADMIN, granted_by="mgr")
    infos = await access_transparency_service.list_admins(MAP_ID)
    assert len(infos) == 1
    assert infos[0].grantee_type is GranteeType.USER
    assert infos[0].id == SUBJECT_ID
    assert infos[0].name == "Ana Beltran"  # mock_users.json fixture, u016


async def test_list_admins_resolves_team_display_name(access_transparency_service, grant_repo):
    team_grantee = Grantee(GranteeType.TEAM, team_id="team-north-ops")
    await grant_repo.upsert_grant(team_grantee, MAP_ID, Role.ADMIN, granted_by="mgr")
    infos = await access_transparency_service.list_admins(MAP_ID)
    assert len(infos) == 1
    assert infos[0].grantee_type is GranteeType.TEAM
    assert infos[0].id == "team-north-ops"
    assert infos[0].name == "North Region Ops"  # seed_data.TEAMS


async def test_list_admins_falls_back_to_id_when_directory_lookup_misses(
    access_transparency_service, grant_repo
):
    """A grant can outlive its grantee's directory record (e.g. a since-
    removed mock user) — list_admins must degrade to the raw id rather than
    error, since this is a display-only convenience, not an authorization
    check."""
    ghost = Grantee(GranteeType.USER, user_id="u-does-not-exist")
    await grant_repo.upsert_grant(ghost, MAP_ID, Role.ADMIN, granted_by="mgr")
    infos = await access_transparency_service.list_admins(MAP_ID)
    assert infos == [GranteeInfo(GranteeType.USER, "u-does-not-exist", "u-does-not-exist")]
