import pytest

from permissions_server.application.access_resolver import AccessResolver
from permissions_server.application.access_transparency_service import AccessTransparencyService
from permissions_server.application.audit_service import AuditService
from permissions_server.application.auth_service import AuthService
from permissions_server.application.catalog_service import CatalogService
from permissions_server.application.permission_grant_service import PermissionGrantService
from permissions_server.infrastructure.auth.adfs_auth_mock_issuer import AdfsAuthMockTokenIssuer
from permissions_server.infrastructure.auth.mock_org_hierarchy import MockOrgHierarchy
from permissions_server.infrastructure.auth.mock_user_directory import MockUserDirectory
from permissions_server.infrastructure.memory.in_memory_audit_log_repository import (
    InMemoryAuditLogRepository,
)
from permissions_server.application.resource_service import ResourceService
from permissions_server.application.restriction_service import RestrictionService
from permissions_server.infrastructure.memory.in_memory_grant_repository import InMemoryGrantRepository
from permissions_server.infrastructure.memory.in_memory_resource_repository import (
    InMemoryResourceRepository,
)
from permissions_server.infrastructure.memory.in_memory_restriction_repository import (
    InMemoryRestrictionRepository,
)
from permissions_server.infrastructure.memory.in_memory_system_role_repository import (
    InMemorySystemRoleRepository,
)
from permissions_server.infrastructure.memory.in_memory_team_repository import InMemoryTeamRepository


@pytest.fixture
def resource_repo():
    return InMemoryResourceRepository()


@pytest.fixture
def team_repo():
    return InMemoryTeamRepository()


@pytest.fixture
def grant_repo():
    return InMemoryGrantRepository()


@pytest.fixture
def system_role_repo():
    return InMemorySystemRoleRepository()


@pytest.fixture
def audit_log_repo():
    return InMemoryAuditLogRepository()


@pytest.fixture
def restriction_repo():
    return InMemoryRestrictionRepository()


@pytest.fixture
def user_directory():
    return MockUserDirectory()


@pytest.fixture
def org_hierarchy():
    return MockOrgHierarchy()


@pytest.fixture
def access_resolver(resource_repo, grant_repo, team_repo, system_role_repo, restriction_repo):
    return AccessResolver(
        resource_repo, grant_repo, team_repo, system_role_repo, restriction_repo
    )


@pytest.fixture
def audit_service(audit_log_repo):
    return AuditService(audit_log_repo)


@pytest.fixture
def permission_grant_service(
    grant_repo, access_resolver, org_hierarchy, user_directory, audit_service, resource_repo
):
    return PermissionGrantService(
        grant_repo, access_resolver, org_hierarchy, user_directory, audit_service, resource_repo
    )


@pytest.fixture
def catalog_service(resource_repo, access_resolver):
    return CatalogService(resource_repo, access_resolver)


@pytest.fixture
def access_transparency_service(access_resolver, user_directory, team_repo):
    return AccessTransparencyService(access_resolver, user_directory, team_repo)


@pytest.fixture
def auth_service(user_directory):
    return AuthService(user_directory, AdfsAuthMockTokenIssuer())


@pytest.fixture
def restriction_service(restriction_repo, access_resolver, org_hierarchy, audit_service, resource_repo):
    return RestrictionService(
        restriction_repo, access_resolver, org_hierarchy, audit_service, resource_repo
    )


@pytest.fixture
def resource_service(resource_repo, access_resolver, permission_grant_service, grant_repo, restriction_repo):
    return ResourceService(
        resource_repo, access_resolver, permission_grant_service, grant_repo, restriction_repo
    )
