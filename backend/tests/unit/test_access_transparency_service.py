import pytest

from permissions_server.domain.entities import AuthenticatedUser, Grantee, GranteeType, Role
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


async def test_check_access_succeeds_when_actor_is_manager(access_transparency_service, grant_repo):
    actor_grantee = Grantee(GranteeType.USER, user_id=ACTOR.id)
    await grant_repo.upsert_grant(actor_grantee, MAP_ID, Role.MANAGER, granted_by="seed")
    await grant_repo.upsert_grant(SUBJECT_GRANTEE, MAP_ID, Role.VIEWER, granted_by="mgr")

    sources = await access_transparency_service.check_access(ACTOR, SUBJECT_ID, MAP_ID)
    assert any(s.role is Role.VIEWER for s in sources)
