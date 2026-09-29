# Graph Report - premissions  (2026-09-29)

## Corpus Check
- 163 files · ~63,271 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 1434 nodes · 2932 edges · 115 communities (103 shown, 12 thin omitted)
- Extraction: 80% EXTRACTED · 20% INFERRED · 0% AMBIGUOUS · INFERRED: 600 edges (avg confidence: 0.67)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `cafacbaf`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- Frontend React App
- Permission Grant Domain & Tests
- Catalog API & Schemas
- Grants Router & DI Wiring
- Frontend Package Dependencies
- Backend Integration Tests
- In-Memory Repositories
- Frontend TS App Config
- Mock Org & User Directory
- Frontend TS Node Config
- Architecture & Phase Overview
- App Bootstrap & JWT Issuer
- Auth Service & Token Issuer
- Auth Domain Ports
- Auth API Router & Schemas
- Service Design Cross-References
- Error Handling
- Access Resolution Logic
- JWT Validator & Auth Tests
- SOLID Principles (Docs)
- Frontend Entry Point Docs
- Frontend Lint Config
- Data Model & Repository Docs
- Icon Sprite Assets
- Delegation Rule Docs
- Frontend Stack Docs
- External API Docs
- Frontend TS Root Config
- Seed Data
- Mock Users Docs
- Favicon Asset
- Backend Package Metadata
- Page
- SystemRole
- set_grant
- test_access_resolver.py
- test_catalog_service.py
- lifespan
- is_valid_child
- get_my_access
- InMemoryTeamRepository
- PermissionGrantRepository
- unit/conftest.py
- env.py
- build_engine_and_sessionmaker
- get_catalog
- AdfsAuthMockTokenIssuer
- tests/conftest.py
- Role
- AccessTransparencyService
- check_access
- .__init__
- TeamModel
- SystemRoleModel
- AuthContext.tsx
- RestrictionService
- lifespan
- InMemorySystemRoleRepository
- auth_headers
- audit_for_resource
- RoleBadge.tsx
- UserDirectory
- AccessTransparencyService
- test_restrictions.py
- MockOrgHierarchy
- load_mock_users
- Resource
- test_delete_resource.py
- TeamModel
- InMemorySystemRoleRepository
- test_move.py
- OrgHierarchy
- TokenValidator
- get_catalog
- .upsert_grant
- SystemRoleRepository
- get_my_access
- InMemoryTeamRepository
- test_auth_flow.py
- _entry
- InMemoryEntityRepository
- Base
- AuditLogRepository
- .__init__
- docker-entrypoint.sh
- EntityRepository
- test_catalog.py
- ApiError
- Base
- ConflictError
- .__init__
- Database Reference — Permissions Server
- env.py
- CI/CD Setup — Remaining Manual Step
- Quick start (always DB/Postgres mode)

## God Nodes (most connected - your core abstractions)
1. `Grantee` - 107 edges
2. `AuthenticatedUser` - 78 edges
3. `login_as()` - 69 edges
4. `auth_headers()` - 55 edges
5. `AccessResolver` - 44 edges
6. `Role` - 41 edges
7. `ResourceRepository` - 39 edges
8. `get_current_user()` - 32 edges
9. `Page` - 32 edges
10. `AuditService` - 28 edges

## Surprising Connections (you probably didn't know these)
- `access_resolver()` --calls--> `AccessResolver`  [INFERRED]
  backend/tests/unit/conftest.py → backend/src/permissions_server/application/access_resolver.py
- `access_transparency_service()` --calls--> `AccessTransparencyService`  [INFERRED]
  backend/tests/unit/conftest.py → backend/src/permissions_server/application/access_transparency_service.py
- `audit_service()` --calls--> `AuditService`  [INFERRED]
  backend/tests/unit/conftest.py → backend/src/permissions_server/application/audit_service.py
- `catalog_service()` --calls--> `CatalogService`  [INFERRED]
  backend/tests/unit/conftest.py → backend/src/permissions_server/application/catalog_service.py
- `permission_grant_service()` --calls--> `PermissionGrantService`  [INFERRED]
  backend/tests/unit/conftest.py → backend/src/permissions_server/application/permission_grant_service.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **SOLID Principles Group** — claude_solid, claude_srp, claude_ocp, claude_lsp, claude_isp, claude_dip [EXTRACTED 1.00]

## Communities (115 total, 12 thin omitted)

### Community 0 - "Frontend React App"
Cohesion: 0.09
Nodes (37): buildQueryString(), CatalogPage, CreateResourceParams, CreateTeamWorkspaceParams, DeleteGrantParams, deleteRestriction(), DeleteRestrictionParams, ErrorBody (+29 more)

### Community 1 - "Permission Grant Domain & Tests"
Cohesion: 0.21
Nodes (14): _make_admin(), Removing the LAST restriction row overall is always allowed, even if     it's A, Row-count can't distinguish 'added once' from 'upserted twice' (same     key ju, The orphan case the guard exists for: removing the last Admin entry     while t, test_first_restriction_auto_whitelists_the_acting_admin(), test_first_restriction_does_not_duplicate_when_actor_restricts_self(), test_revoke_admin_restriction_succeeds_when_another_admin_remains(), test_revoke_last_admin_restriction_is_conflict_when_other_entries_remain() (+6 more)

### Community 2 - "Catalog API & Schemas"
Cohesion: 0.33
Nodes (4): Protocol, Validates bearer tokens — mocked now, real ADFS OIDC validation later., Validates a bearer token and returns who it belongs to.      Phase 2 swap poin, TokenValidator

### Community 3 - "Grants Router & DI Wiring"
Cohesion: 0.32
Nodes (19): get_access_resolver(), get_access_transparency_service(), get_audit_log_repository(), get_audit_service(), get_catalog_service(), get_grant_repository(), get_org_hierarchy(), get_permission_grant_service() (+11 more)

### Community 4 - "Frontend Package Dependencies"
Cohesion: 0.05
Nodes (38): dependencies, react, react-dom, react-router-dom, devDependencies, oxlint, tailwindcss, @tailwindcss/vite (+30 more)

### Community 5 - "Backend Integration Tests"
Cohesion: 0.25
Nodes (17): login_as(), _grant_team(), _grant_user(), Remove access' (frontend) must work for an ordinary Viewer with no     Manager/, The org-chart delegation check exists for shared resources managed by     repor, test_delegation_forbidden_across_org_branches(), test_grant_target_of_nonexistent_resource_is_404(), test_grant_without_manager_role_is_forbidden() (+9 more)

### Community 6 - "In-Memory Repositories"
Cohesion: 0.21
Nodes (4): InMemoryResourceRepository, Resource, ResourceType, In-memory ResourceRepository — Phase 1 storage, used when PERMISSIONS_DATABASE_U

### Community 7 - "Frontend TS App Config"
Cohesion: 0.08
Nodes (23): compilerOptions, allowArbitraryExtensions, allowImportingTsExtensions, erasableSyntaxOnly, jsx, lib, module, moduleDetection (+15 more)

### Community 8 - "Mock Org & User Directory"
Cohesion: 0.17
Nodes (20): describeError(), isMessageKey(), isResourceType(), localizeParams(), STATUS_FALLBACK_KEYS, MessageKey, Messages, format() (+12 more)

### Community 9 - "Frontend TS Node Config"
Cohesion: 0.10
Nodes (19): compilerOptions, allowImportingTsExtensions, erasableSyntaxOnly, lib, module, moduleDetection, noEmit, noFallthroughCasesInSwitch (+11 more)

### Community 10 - "Architecture & Phase Overview"
Cohesion: 0.20
Nodes (10): No member list here — membership is mutable, queryable state owned by     TeamR, Team, TeamMembershipModel, TeamModel, async_sessionmaker, AsyncSession, Team, PostgreSQL-backed TeamRepository, used when PERMISSIONS_DATABASE_URL is set. (+2 more)

### Community 11 - "App Bootstrap & JWT Issuer"
Cohesion: 0.14
Nodes (18): ExternalMapAccessOut, ExternalMyAccessPageOut, get_my_access(), BaseModel, Depends, The one endpoint other internal apps call to check a user's map access., AccessSnapshot, The one place effective role is computed. Never re-implement this resolution lo (+10 more)

### Community 12 - "Auth Service & Token Issuer"
Cohesion: 0.11
Nodes (26): AsyncEngine, build_engine_and_sessionmaker(), async_sessionmaker, AsyncSession, Builds the async engine/sessionmaker pair for a given database_url., audit_log_repo(), grant_repo(), migrated_database_url() (+18 more)

### Community 13 - "Auth Domain Ports"
Cohesion: 0.29
Nodes (10): clearStoredToken(), getMe(), getMyWorkspace(), getStoredToken(), Me, MockUser, setStoredToken(), AuthContext (+2 more)

### Community 14 - "Auth API Router & Schemas"
Cohesion: 0.17
Nodes (9): _enum(), SQLAlchemy ORM models — the Postgres-facing mirror of domain/entities.py. Column, SystemRoleModel, async_sessionmaker, AsyncSession, SystemRole, PostgreSQL-backed SystemRoleRepository, used when PERMISSIONS_DATABASE_URL is se, SqlAlchemySystemRoleRepository (+1 more)

### Community 15 - "Service Design Cross-References"
Cohesion: 0.25
Nodes (8): `audit_log`, `permission_grants`, `resources`, `restrictions`, Schema, `system_roles`, `team_memberships`, `teams`

### Community 16 - "Error Handling"
Cohesion: 0.08
Nodes (27): _give_actor_role(), Team grantees skip the org-chart check entirely — only role rank     matters, m, Self-revocation must work for an ordinary Viewer/Editor with no     Manager/Adm, Even an Admin can't be their own org-chart superior — self-revocation     must, Regression guard: the self-revocation bypass must not leak into     revoking OT, A personal workspace's owner has authority over its whole subtree     regardles, The bypass is scoped to the OWNER's own workspace — an Admin grant     someone, Found via manual UI testing 2026-07-31: can_manage already lets a     SUPER_EDI (+19 more)

### Community 17 - "Access Resolution Logic"
Cohesion: 0.12
Nodes (19): add_team_member(), create_team(), list_team_members(), list_teams(), Depends, Response, Team identity and membership., remove_team_member() (+11 more)

### Community 18 - "JWT Validator & Auth Tests"
Cohesion: 0.22
Nodes (17): CatalogItemOut, CatalogPageOut, BaseModel, Wire schemas for api/routers/catalog_router.py., GranteeInfo, A grantee resolved to a display name — id/name pairing lives here     rather th, AuditAction, GranteeType (+9 more)

### Community 19 - "SOLID Principles (Docs)"
Cohesion: 0.11
Nodes (23): AccessResolver, can_manage, Delegation Rule, Dependency Inversion Principle (DIP), domain.ports, /external/v1/my-access API, Hexagonal Architecture, Interface Segregation Principle (ISP) (+15 more)

### Community 21 - "Frontend Lint Config"
Cohesion: 0.22
Nodes (8): plugins, rules, react/only-export-components, react/rules-of-hooks, $schema, oxc, typescript, warn

### Community 22 - "Data Model & Repository Docs"
Cohesion: 0.08
Nodes (24): get_auth_service(), get_token_issuer(), get_me(), list_mock_users(), login(), Depends, Mock login and the caller's own identity/system-roles., LoginRequest (+16 more)

### Community 23 - "Icon Sprite Assets"
Cohesion: 0.43
Nodes (7): Bluesky icon (social link, butterfly logo), Discord icon (social link, game-controller/robot-face logo), Documentation icon (open book / doc outline), GitHub icon (Octocat mark), Social/people icon (two-person avatar with sparkle badge), icons.svg (frontend icon sprite sheet), X (Twitter) icon

### Community 24 - "Delegation Rule Docs"
Cohesion: 0.19
Nodes (8): AuditLogEntry, Newest-first. Append-only — no update/delete method on this port,         by de, Page, InMemoryAuditLogRepository, In-memory AuditLogRepository — Phase 1 storage, used when PERMISSIONS_DATABASE_U, PostgreSQL-backed AuditLogRepository, used when PERMISSIONS_DATABASE_URL is set., SqlAlchemyAuditLogRepository, _to_domain()

### Community 25 - "Frontend Stack Docs"
Cohesion: 0.50
Nodes (4): Oxlint, React, React Compiler, Vite

### Community 26 - "External API Docs"
Cohesion: 0.12
Nodes (11): PermissionGrantService, Owns the delegation rule end-to-end. Grantee-agnostic: operates on a Grantee (us, Normally just the actor's org-chart subordinates — the only users         they c, PermissionGrantRepository, Protocol, Storage contract for per-resource role grants — in-memory and SQLAlchemy impleme, Remove every grant (any grantee) on any of these resources — the         cascad, OrgHierarchy (+3 more)

### Community 29 - "Mock Users Docs"
Cohesion: 0.15
Nodes (13): API endpoints, Architecture, Bootstrap (Phase 1 dev convenience), Build sequence (current state: Phase 1 + Phase 2 storage complete and passing), Confirmed decisions (do not re-litigate), Context, Core services, Domain model (+5 more)

### Community 46 - "Page"
Cohesion: 0.21
Nodes (12): delete_restriction(), Depends, GranteeTypePath, Response, Restriction, The restriction whitelist gate, layered on top of ordinary grants., set_restriction(), _to_out() (+4 more)

### Community 48 - "set_grant"
Cohesion: 0.25
Nodes (12): check_access(), _grantee_info_to_out(), list_admins(), my_access(), Depends, Access-transparency endpoints: explain or list who has what, and why., _to_out(), AccessSourceOut (+4 more)

### Community 49 - "test_access_resolver.py"
Cohesion: 0.05
Nodes (27): A workspace-wide grant normally reaches every descendant. Flipping     inherits, The barrier only blocks what would have come from ABOVE it — a grant     placed, Regression guard: with zero Restriction rows anywhere, effective_role     must, A restriction 'is greater than any auth' — an actor not on the     whitelist ge, Baseline: an unlisted actor is denied by a workspace-level     restriction. Onc, The user explicitly rejected a 'last one set wins' rule — ties among     restri, Confirmed 2026-07-31: both system-wide roles are "greater than any     permissi, A node can have grants without anyone there being Admin — the     resource genu (+19 more)

### Community 50 - "test_catalog_service.py"
Cohesion: 0.12
Nodes (12): _find(), Confirmed 2026-07-31: a personal workspace is invisible to anyone who     can't, A non-owner with a real, explicit grant somewhere inside another     user's pers, A grant on a single Layer, with no role on the Map itself, still makes     that, A grant on just one Layer (nothing on the Map itself) still makes the     Map's, Confirmed 2026-07-31: the caller's own personal workspace always shows     first, test_can_fetch_bubbles_up_from_a_single_accessible_layer(), test_catalog_no_search_returns_full_workspace_tree_annotated_none() (+4 more)

### Community 51 - "lifespan"
Cohesion: 0.18
Nodes (7): MockUserDirectory, Fixture-backed UserDirectory implementation over mock_users.json., load_mock_users(), MockUserRecord, Shared loader for mock_users.json — the single parse point used by both mock_use, user_directory(), TypedDict

### Community 52 - "is_valid_child"
Cohesion: 0.14
Nodes (16): ResourceModel, Custom SQLAlchemy type for PostgreSQL's ltree, used only by ResourceModel.path (, ltree labels allow only letters, digits, and underscores — resource ids     (uui, sanitize_label(), paginate(), AsyncSession, Shared offset/limit + count logic for every SQLAlchemy repo that pages a `select, async_sessionmaker (+8 more)

### Community 53 - "get_my_access"
Cohesion: 0.15
Nodes (13): 0. What OpenShift actually is, briefly, 10. What does not change, 11. Recommended order, 1. Container image changes needed, 2. Health checks, 3. OpenShift resource objects needed (none exist yet), 4. Database, 5. Packages and build-time dependencies (+5 more)

### Community 55 - "InMemoryTeamRepository"
Cohesion: 0.20
Nodes (4): upgrade(), Ltree, Maps a Python str (dot-separated labels, e.g. 'ws_city.f_infra') to     PostgreS, UserDefinedType

### Community 56 - "PermissionGrantRepository"
Cohesion: 0.25
Nodes (8): RestrictionModel, async_sessionmaker, AsyncSession, Restriction, Role, PostgreSQL-backed RestrictionRepository, used when PERMISSIONS_DATABASE_URL is s, SqlAlchemyRestrictionRepository, _to_domain()

### Community 57 - "unit/conftest.py"
Cohesion: 0.21
Nodes (10): seed(), PermissionGrantModel, grantee_key(), async_sessionmaker, AsyncSession, Role, PostgreSQL-backed PermissionGrantRepository, used when PERMISSIONS_DATABASE_URL, Always non-null and unique per (grantee_type, user_id, team_id) triple     — se (+2 more)

### Community 58 - "env.py"
Cohesion: 0.45
Nodes (5): AuditService, Role, `role` is the NEW role the grantee ends up with., `role` is the NEW role the restriction entry ends up with., AuthenticatedUser

### Community 59 - "build_engine_and_sessionmaker"
Cohesion: 0.20
Nodes (13): is_valid_child(), Map/Layer are deliberately excluded even though Map can structurally     hold c, test_folder_allows_folder_map_and_layer_directly(), test_grantee_rejects_both_ids_set_regardless_of_type(), test_grantee_team_type_requires_team_id_not_user_id(), test_grantee_user_type_requires_user_id_not_team_id(), test_group_nests_indefinitely(), test_is_organizational() (+5 more)

### Community 60 - "get_catalog"
Cohesion: 0.19
Nodes (18): get_current_user(), delete_grant(), _ensure_resource_exists(), list_grants_for_resource(), list_manageable_users(), Depends, GranteeTypePath, Response (+10 more)

### Community 61 - "AdfsAuthMockTokenIssuer"
Cohesion: 0.20
Nodes (10): CI, Configuration, Known limitations (deliberate, tracked in `PLAN.md`/`CLAUDE.md`), Permissions Server, Prerequisites, Project layout, Running with Docker, Running with PostgreSQL (one-time setup) (+2 more)

### Community 65 - "Role"
Cohesion: 0.11
Nodes (17): list_restrictions(), AccessResolver, Owns setting/revoking restrictions end-to-end — a deliberately separate, Admin-, RestrictionService, A whitelist entry, not an additive grant. Same shape as PermissionGrant     but, Restriction, Protocol, Restriction (+9 more)

### Community 66 - "AccessTransparencyService"
Cohesion: 0.17
Nodes (11): access_resolver(), access_transparency_service(), audit_log_repo(), audit_service(), catalog_service(), grant_repo(), org_hierarchy(), permission_grant_service() (+3 more)

### Community 67 - "check_access"
Cohesion: 0.29
Nodes (9): audit_for_actor(), audit_for_resource(), Depends, Read-only endpoints over the append-only audit log., _to_out(), AuditLogEntryOut, AuditLogPageOut, BaseModel (+1 more)

### Community 68 - ".__init__"
Cohesion: 0.13
Nodes (22): CatalogItem, deleteGrant(), deleteResource(), getResourceAdmins(), GranteeInfo, moveResource(), ResourceType, Role (+14 more)

### Community 69 - "TeamModel"
Cohesion: 0.16
Nodes (13): Role, Role-rank rule (both grantee types): actor needs Role.MANAGER+ on         resour, Grantee, A user-scope grantee (team_id=None) or a team-scope grantee (user_id=None)., Remove the explicit grant row; no error if it didn't exist., Remove the explicit restriction row; no error if it didn't exist., _make_resource(), Exercises SqlAlchemyGrantRepository against real Postgres — in particular the g (+5 more)

### Community 70 - "SystemRoleModel"
Cohesion: 0.50
Nodes (3): AsyncClient, client(), A fresh app + in-memory state per test, talked to over real HTTP     semantics (

### Community 71 - "AuthContext.tsx"
Cohesion: 0.15
Nodes (18): createResource(), createTeamWorkspace(), getCatalog(), isSuperEditor(), listMockUsers(), ProtectedRoute(), useAuth(), CreateResourceModal() (+10 more)

### Community 72 - "RestrictionService"
Cohesion: 0.19
Nodes (10): get_settings(), AdfsAuthMockTokenIssuer, Wraps adfs-auth's testing.MockTokenAcquirer behind the TokenIssuer port., TokenIssuer backed by the adfs-auth library's MockTokenAcquirer — delegates, create_app(), lifespan(), FastAPI, FastAPI app factory and startup wiring — builds either in-memory or SQLAlchemy r (+2 more)

### Community 73 - "lifespan"
Cohesion: 0.50
Nodes (3): Running `docker compose up` Against the Real Closed-Network DB, Steps, Why not just edit `docker-compose.yml`

### Community 74 - "InMemorySystemRoleRepository"
Cohesion: 0.10
Nodes (12): Unconditional Admin grant for target_user_id on a BRAND-NEW         resource — n, PermissionGrant, One grantee's role at one resource. See Restriction below for the     same shap, Role, The explicit grant row for this exact (grantee, resource), or None., Every explicit grant (any grantee) directly on this resource —         drives ', Every explicit grant across ALL resources, for a set of grantees (a         use, Set/replace the grant for (grantee, resource). (+4 more)

### Community 75 - "auth_headers"
Cohesion: 0.18
Nodes (15): auth_headers(), test_external_access_filters_out_none_but_totals_all_maps(), test_external_access_includes_map_reachable_only_via_one_layer(), test_external_access_is_empty_for_ungranted_user(), test_list_restrictions_requires_admin(), An outsider with no access at all can still ask 'who do I ask' —     the endpoi, test_audit_endpoint_records_grant_and_revoke(), test_audit_for_actor_allowed_for_others_with_system_role() (+7 more)

### Community 76 - "audit_for_resource"
Cohesion: 0.09
Nodes (15): InMemoryRestrictionRepository, Restriction, Role, In-memory RestrictionRepository — Phase 1 storage, used when PERMISSIONS_DATABAS, InMemorySystemRoleRepository, SystemRole, In-memory SystemRoleRepository — Phase 1 storage, used when PERMISSIONS_DATABASE, restriction_repo() (+7 more)

### Community 77 - "RoleBadge.tsx"
Cohesion: 0.24
Nodes (9): Missing, malformed, or expired token — api/ maps this to 401., UnauthorizedError, AdfsAuthMockTokenValidator, TokenValidator backed by the adfs-auth library's MockTokenValidator.      The, AuthService.login() itself guards against issuing a token for an     unknown us, test_login_issues_a_token_that_resolves_to_the_right_user(), test_login_unknown_user_raises_not_found(), test_search_users_matches_by_name_or_email_substring() (+1 more)

### Community 79 - "UserDirectory"
Cohesion: 0.06
Nodes (43): create_resource(), create_team_workspace(), delete_resource(), get_my_workspace(), move_resource(), Depends, Resource, Response (+35 more)

### Community 80 - "AccessTransparencyService"
Cohesion: 0.19
Nodes (8): Resource, Restriction, Role, The restriction twin of nearest_grants. Unlike grants, a node is         gated, Same restriction-then-grants precedence as effective_role(), but         collec, Ties among multiple grants (or restriction entries) at the nearest         ance, Nearest-ancestor-wins traversal shared by nearest_grants,         nearest_restr, Walk from resource_id up to the tree root; return         (origin_resource_id,

### Community 81 - "test_restrictions.py"
Cohesion: 0.25
Nodes (17): _effective_role(), _grant_user(), VP (granted Admin directly on OTHER_MAP_ID) sets a restriction naming     only, The FIRST restriction ever set on a resource auto-whitelists the     acting adm, Self-lockout via one's own FIRST restriction is no longer possible     (see tes, _restrict_user(), test_delete_restriction_removes_the_gate(), test_locked_out_admin_cannot_manage_further_restrictions() (+9 more)

### Community 82 - "MockOrgHierarchy"
Cohesion: 0.24
Nodes (8): MockOrgHierarchy, Fixture-backed OrgHierarchy implementation, derived from mock_users.json's manag, Verifies the visited-set guards in MockOrgHierarchy actually stop traversal on, Data-integrity edge case distinct from a cycle: manager_id points at     an id, test_is_manager_of_false_when_chain_ends_at_a_dangling_manager_id(), test_is_manager_of_still_finds_real_relationships(), test_is_manager_of_terminates_instead_of_looping_forever(), test_subordinates_of_terminates_and_finds_real_subordinates()

### Community 83 - "load_mock_users"
Cohesion: 0.43
Nodes (7): _make_resource(), Exercises SqlAlchemyRestrictionRepository against real Postgres — the restricti, test_delete_restriction_removes_only_that_grantee(), test_delete_restrictions_for_resource_ids_bulk_removes(), test_list_restrictions_for_grantees_filters_to_requested(), test_list_restrictions_for_resource_ids_spans_multiple_resources(), test_upsert_restriction_creates_then_updates_role()

### Community 84 - "Resource"
Cohesion: 0.09
Nodes (18): grantee_passes_org_chart_check(), is_within_actors_personal_workspace(), Shared by PermissionGrantService.can_manage and RestrictionService's own delegat, A personal workspace's owner has full authority over its whole     subtree, rega, Protocol, Resource, ResourceType, Storage contract for the Workspace/Folder/Map/Group/Layer resource tree. (+10 more)

### Community 85 - "test_delete_resource.py"
Cohesion: 0.30
Nodes (14): _create(), _delete(), _find(), _grant_user(), Folder/Group/Workspace only ever hard-delete when empty — this     permissions, Also doubles as the regression guard proving Map is deliberately     exempt fro, test_admin_at_subtree_but_not_root_can_delete_only_their_subtree(), test_admin_deletes_resource_and_its_subtree() (+6 more)

### Community 86 - "TeamModel"
Cohesion: 0.20
Nodes (10): 1. Database, 2. Packages — what has to be available in the closed network, 3. Auth — the biggest real gap, not just a config swap, 4. CORS and frontend↔backend wiring, 5. Secrets, 6. What does *not* change with this move, 7. Verification checklist for the move, Migrating to the Closed Network (+2 more)

### Community 88 - "test_move.py"
Cohesion: 0.33
Nodes (12): _find(), _grant_user(), _move(), test_admin_at_source_and_editor_at_destination_can_move_with_subtree(), test_move_forbidden_with_no_access_at_all(), test_move_forbidden_without_admin_at_source(), test_move_forbidden_without_editor_at_destination(), test_move_into_invalid_type_pair_is_conflict() (+4 more)

### Community 89 - "OrgHierarchy"
Cohesion: 0.23
Nodes (13): _create_resource(), _grant_user(), UI data can be in Hebrew — names are stored and searched as-is (UTF-8),     neve, test_create_child_under_editor_parent_makes_creator_admin(), test_create_child_under_nonexistent_parent_is_404(), test_create_child_with_invalid_type_pair_is_conflict(), test_create_child_with_no_access_at_parent_is_forbidden(), test_create_child_with_only_viewer_at_parent_is_forbidden() (+5 more)

### Community 90 - "TokenValidator"
Cohesion: 0.18
Nodes (6): A grant can outlive its grantee's directory record (e.g. a since-     removed m, test_check_access_forbidden_when_actor_lacks_manager_role(), test_check_access_succeeds_when_actor_is_manager(), test_explain_access_marks_the_winning_source_effective(), test_list_admins_falls_back_to_id_when_directory_lookup_misses(), test_list_admins_resolves_team_display_name()

### Community 91 - "get_catalog"
Cohesion: 0.40
Nodes (5): get_catalog(), Depends, The main resource-tree listing endpoint., _to_out(), CatalogItem

### Community 93 - "SystemRoleRepository"
Cohesion: 0.32
Nodes (4): Protocol, SystemRole, Kept separate from PermissionGrantRepository on purpose: system roles have no re, SystemRoleRepository

### Community 94 - "get_my_access"
Cohesion: 0.33
Nodes (5): AccessSource, AccessTransparencyService, Why do I have this access' — one shared breakdown, two thin callers: my_access, Ungated, like my_access — meant for a caller who just found out         their o, role_rank()

### Community 95 - "InMemoryTeamRepository"
Cohesion: 0.20
Nodes (4): InMemoryTeamRepository, Team, In-memory TeamRepository — Phase 1 storage, used when PERMISSIONS_DATABASE_URL i, team_repo()

### Community 97 - "_entry"
Cohesion: 0.31
Nodes (8): Records grant/revoke actions append-only. Kept as a collaborator that Permission, _entry(), Exercises SqlAlchemyAuditLogRepository against real Postgres, including _pagina, test_append_then_list_for_resource(), test_list_for_actor_filters_by_actor(), test_list_for_resource_orders_newest_first(), test_list_for_resource_paginates(), datetime

### Community 98 - "InMemoryEntityRepository"
Cohesion: 0.28
Nodes (5): _HasIdAndName, InMemoryEntityRepository, Protocol, T, Generic in-memory implementation of EntityRepository, shared by the Resource and

### Community 99 - "Base"
Cohesion: 0.20
Nodes (7): One-time (idempotent) loader: pushes seed_data.py's mock resource tree/teams int, Application settings, read from environment (.env supported). No hardcoded secre, Settings, Wraps adfs-auth's testing.MockTokenValidator behind the TokenValidator port, res, Covers main.py's lifespan() DB-mode branch, which the rest of the suite never e, test_lifespan_wires_sqlalchemy_repositories_when_database_url_set(), BaseSettings

### Community 100 - "AuditLogRepository"
Cohesion: 0.33
Nodes (3): AuditLogRepository, Protocol, Append-only audit trail port — no update/delete method by design.

### Community 101 - ".__init__"
Cohesion: 0.67
Nodes (3): FastAPI, Translates domain/errors.py exceptions into HTTP responses, in one place — indiv, register_error_handlers()

### Community 103 - "EntityRepository"
Cohesion: 0.40
Nodes (3): EntityRepository, T, Shared read contract for entities identified by id and searchable by name. Backs

### Community 105 - "test_catalog.py"
Cohesion: 0.40
Nodes (4): _find(), test_catalog_search_filters_by_name(), test_catalog_shows_full_tree_with_none_for_ungranted_user(), test_root_user_has_admin_from_bootstrap_seed()

### Community 106 - "ApiError"
Cohesion: 0.33
Nodes (3): ApiError, ForbiddenError, UnauthorizedError

### Community 107 - "Base"
Cohesion: 0.50
Nodes (3): Base, SQLAlchemy declarative base shared by every ORM model in infrastructure/db/model, DeclarativeBase

### Community 108 - "ConflictError"
Cohesion: 0.33
Nodes (3): Restriction, Role, Admin-only (NOT Manager, unlike ordinary grants where Manager         keeps its

### Community 111 - "Database Reference — Permissions Server"
Cohesion: 0.29
Nodes (7): Database Reference — Permissions Server, DB-backed test tier, Entity-relationship summary, Migrations, Requirements, Starting the database (one-time setup), Verifying the connection independent of the app

### Community 112 - "env.py"
Cohesion: 0.53
Nodes (5): _do_run_migrations(), get_url(), run_migrations_offline(), run_migrations_online(), Connection

### Community 113 - "CI/CD Setup — Remaining Manual Step"
Cohesion: 0.33
Nodes (5): After this works, CI/CD Setup, How to verify it worked, Steps, Why it's needed

### Community 115 - "Quick start (always DB/Postgres mode)"
Cohesion: 0.50
Nodes (4): Backend, Frontend, Quick start (always DB/Postgres mode), Try it

## Ambiguous Edges - Review These
- `Documentation icon (open book / doc outline)` → `Social/people icon (two-person avatar with sparkle badge)`  [AMBIGUOUS]
  frontend/public/icons.svg · relation: conceptually_related_to

## Knowledge Gaps
- **171 isolated node(s):** `docker-entrypoint.sh script`, `permissions-server`, `$schema`, `typescript`, `oxc` (+166 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **12 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **What is the exact relationship between `Documentation icon (open book / doc outline)` and `Social/people icon (two-person avatar with sparkle badge)`?**
  _Edge tagged AMBIGUOUS (relation: conceptually_related_to) - confidence is low._
- **Why does `Grantee` connect `TeamModel` to `Permission Grant Domain & Tests`, `App Bootstrap & JWT Issuer`, `Error Handling`, `JWT Validator & Auth Tests`, `Delegation Rule Docs`, `External API Docs`, `test_access_resolver.py`, `PermissionGrantRepository`, `unit/conftest.py`, `env.py`, `build_engine_and_sessionmaker`, `get_catalog`, `Role`, `RestrictionService`, `InMemorySystemRoleRepository`, `audit_for_resource`, `UserDirectory`, `AccessTransparencyService`, `load_mock_users`, `Resource`, `TokenValidator`, `get_my_access`, `_entry`, `ConflictError`?**
  _High betweenness centrality (0.161) - this node is a cross-community bridge._
- **Why does `AuthenticatedUser` connect `env.py` to `Permission Grant Domain & Tests`, `Catalog API & Schemas`, `App Bootstrap & JWT Issuer`, `Access Resolution Logic`, `JWT Validator & Auth Tests`, `Data Model & Repository Docs`, `External API Docs`, `Page`, `set_grant`, `lifespan`, `get_catalog`, `Role`, `check_access`, `TeamModel`, `RestrictionService`, `InMemorySystemRoleRepository`, `RoleBadge.tsx`, `UserDirectory`, `get_catalog`, `get_my_access`, `ConflictError`?**
  _High betweenness centrality (0.094) - this node is a cross-community bridge._
- **Why does `lifespan()` connect `RestrictionService` to `In-Memory Repositories`, `InMemorySystemRoleRepository`, `Architecture & Phase Overview`, `Auth Service & Token Issuer`, `RoleBadge.tsx`, `audit_for_resource`, `Auth API Router & Schemas`, `MockOrgHierarchy`, `lifespan`, `is_valid_child`, `Delegation Rule Docs`, `unit/conftest.py`, `PermissionGrantRepository`, `InMemoryTeamRepository`?**
  _High betweenness centrality (0.087) - this node is a cross-community bridge._
- **Are the 55 inferred relationships involving `Grantee` (e.g. with `seed()` and `AccessResolver`) actually correct?**
  _`Grantee` has 55 INFERRED edges - model-reasoned connections that need verification._
- **Are the 18 inferred relationships involving `AuthenticatedUser` (e.g. with `ExternalMapAccessOut` and `ExternalMyAccessPageOut`) actually correct?**
  _`AuthenticatedUser` has 18 INFERRED edges - model-reasoned connections that need verification._
- **Are the 67 inferred relationships involving `login_as()` (e.g. with `test_login_then_me_round_trip()` and `test_catalog_search_filters_by_name()`) actually correct?**
  _`login_as()` has 67 INFERRED edges - model-reasoned connections that need verification._