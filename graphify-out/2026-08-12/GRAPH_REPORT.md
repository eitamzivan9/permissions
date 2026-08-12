# Graph Report - Premissions  (2026-08-05)

## Corpus Check
- 132 files · ~37,367 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 1157 nodes · 2284 edges · 95 communities (85 shown, 10 thin omitted)
- Extraction: 81% EXTRACTED · 19% INFERRED · 0% AMBIGUOUS · INFERRED: 435 edges (avg confidence: 0.66)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `26ff8d2b`
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
- Ltree
- audit_for_resource
- RoleBadge.tsx
- get_catalog
- AccessTransparencyService
- RestrictionService
- MockOrgHierarchy
- load_mock_users
- paginate
- register_error_handlers
- .__init__
- InMemorySystemRoleRepository
- EntityRepository
- OrgHierarchy
- TokenValidator
- GrantOut
- .upsert_grant
- Base
- FastAPI

## God Nodes (most connected - your core abstractions)
1. `Grantee` - 76 edges
2. `AuthenticatedUser` - 74 edges
3. `login_as()` - 56 edges
4. `auth_headers()` - 43 edges
5. `AccessResolver` - 39 edges
6. `Role` - 39 edges
7. `ResourceRepository` - 37 edges
8. `get_current_user()` - 31 edges
9. `AuditService` - 26 edges
10. `AuditLogEntry` - 26 edges

## Surprising Connections (you probably didn't know these)
- `MirroredEntityRepository` --references--> `MirroredEntityRepository (Protocol)`  [INFERRED]
  CLAUDE.md → PLAN.md
- `AccessResolver` --references--> `AccessResolver`  [INFERRED]
  CLAUDE.md → PLAN.md
- `domain.ports` --conceptually_related_to--> `MirroredEntityRepository (Protocol)`  [INFERRED]
  CLAUDE.md → PLAN.md
- `Delegation Rule` --references--> `Delegation Rule`  [INFERRED]
  CLAUDE.md → PLAN.md
- `Scale Assumptions` --conceptually_related_to--> `Permissions Server Implementation Plan`  [INFERRED]
  CLAUDE.md → PLAN.md

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **SOLID Principles Group** — claude_solid, claude_srp, claude_ocp, claude_lsp, claude_isp, claude_dip [EXTRACTED 1.00]
- **Delegation Enforcement Flow** — plan_permissiongrantservice, plan_accessresolver, plan_orghierarchy [EXTRACTED 1.00]
- **Port/Adapter/DI Wiring Pattern** — plan_mirroredentityrepository, plan_inmemorymirroredentityrepository, plan_deps_py, plan_grants_router [INFERRED 0.85]

## Communities (95 total, 10 thin omitted)

### Community 0 - "Frontend React App"
Cohesion: 0.11
Nodes (23): buildQueryString(), deleteGrant(), deleteRestriction(), extractErrorMessage(), getGrantsForResource(), getManageableUsers(), getRestrictionsForResource(), Grant (+15 more)

### Community 1 - "Permission Grant Domain & Tests"
Cohesion: 0.10
Nodes (12): Role, Unconditional Admin grant for target_user_id on a BRAND-NEW         resource — n, Role-rank rule (both grantee types): actor needs Role.MANAGER+ on         resour, Grantee, A user-scope grantee (team_id=None) or a team-scope grantee (user_id=None)., The explicit grant row for this exact (grantee, resource), or None., Every explicit grant across ALL resources, for a set of grantees (a         user, Remove the explicit grant row; no error if it didn't exist. (+4 more)

### Community 2 - "Catalog API & Schemas"
Cohesion: 0.10
Nodes (14): Page, Protocol, Resource, ResourceType, Direct children only, one level down., [root, ..., resource itself] — root-first, inclusive. Single-element         lis, All resources of one type (e.g. every Workspace, or every Map),         for the, Persists a new node. Parent/child type legality (is_valid_child) is         the (+6 more)

### Community 3 - "Grants Router & DI Wiring"
Cohesion: 0.22
Nodes (24): get_access_resolver(), get_access_transparency_service(), get_audit_log_repository(), get_audit_service(), get_auth_service(), get_catalog_service(), get_grant_repository(), get_org_hierarchy() (+16 more)

### Community 4 - "Frontend Package Dependencies"
Cohesion: 0.06
Nodes (35): dependencies, react, react-dom, react-router-dom, devDependencies, oxlint, tailwindcss, @tailwindcss/vite (+27 more)

### Community 5 - "Backend Integration Tests"
Cohesion: 0.06
Nodes (77): AsyncClient, auth_headers(), client(), login_as(), A fresh app + in-memory state per test, talked to over real HTTP     semantics (, test_login_then_me_round_trip(), test_protected_route_with_garbage_token_is_401(), _find() (+69 more)

### Community 6 - "In-Memory Repositories"
Cohesion: 0.08
Nodes (14): AccessTransparencyService, InMemoryResourceRepository, Page, Resource, ResourceType, access_resolver(), access_transparency_service(), audit_service() (+6 more)

### Community 7 - "Frontend TS App Config"
Cohesion: 0.08
Nodes (23): compilerOptions, allowArbitraryExtensions, allowImportingTsExtensions, erasableSyntaxOnly, jsx, lib, module, moduleDetection (+15 more)

### Community 8 - "Mock Org & User Directory"
Cohesion: 0.20
Nodes (11): seed(), PermissionGrant, Every explicit grant (any grantee) directly on this resource —         drives 'w, PermissionGrantModel, grantee_key(), async_sessionmaker, AsyncSession, Role (+3 more)

### Community 9 - "Frontend TS Node Config"
Cohesion: 0.10
Nodes (19): compilerOptions, allowImportingTsExtensions, erasableSyntaxOnly, lib, module, moduleDetection, noEmit, noFallthroughCasesInSwitch (+11 more)

### Community 10 - "Architecture & Phase Overview"
Cohesion: 0.19
Nodes (15): Permissions Server, Phase 1 (outside org network), Phase 2 (inside org network), Scale Assumptions, UI Scope, Build Sequence, External API Auth (forwarded ADFS JWT), Maps/Layers Mirror (+7 more)

### Community 11 - "App Bootstrap & JWT Issuer"
Cohesion: 0.12
Nodes (14): _do_run_migrations(), get_url(), run_migrations_offline(), run_migrations_online(), One-time (idempotent) loader: pushes seed_data.py's mock resource tree/teams int, get_settings(), Application settings, read from environment (.env supported). No hardcoded secre, Settings (+6 more)

### Community 12 - "Auth Service & Token Issuer"
Cohesion: 0.11
Nodes (12): AuthService, Admin-only, same rank as move()'s source-resource check — deleting         is at, Restriction, Role, Admin-only (NOT Manager, unlike ordinary grants where Manager         keeps its, AuthenticatedUser, Protocol, Issues a bearer token for a user. Only the mock auth flow implements this — (+4 more)

### Community 13 - "Auth Domain Ports"
Cohesion: 0.11
Nodes (16): ApiError, CatalogPage, CreateResourceParams, CreateTeamWorkspaceParams, DeleteGrantParams, DeleteRestrictionParams, ForbiddenError, GetCatalogParams (+8 more)

### Community 14 - "Auth API Router & Schemas"
Cohesion: 0.31
Nodes (6): getCatalog(), isSuperEditor(), ProtectedRoute(), useAuth(), Permissions(), react

### Community 15 - "Service Design Cross-References"
Cohesion: 0.23
Nodes (12): can_manage, Hexagonal Architecture, MirroredEntityRepository, No Duplicated Code Rule, PermissionGrantService, AccessResolver, Layered/Hexagonal Architecture, AuthService (+4 more)

### Community 16 - "Error Handling"
Cohesion: 0.11
Nodes (19): _give_actor_role(), Team grantees skip the org-chart check entirely — only role rank     matters, ma, A personal workspace's owner has authority over its whole subtree     regardless, The bypass is scoped to the OWNER's own workspace — an Admin grant     someone e, Found via manual UI testing 2026-07-31: can_manage already lets a     SUPER_EDIT, A manager's role on a layer target can come from the map-level     default, not, test_can_manage_false_for_non_subordinate_inside_someone_elses_personal_workspace(), test_can_manage_false_when_manager_but_not_subordinate() (+11 more)

### Community 17 - "Access Resolution Logic"
Cohesion: 0.14
Nodes (18): get_team_repository(), TeamRepository, add_team_member(), create_team(), list_team_members(), list_teams(), Depends, Response (+10 more)

### Community 19 - "SOLID Principles (Docs)"
Cohesion: 0.25
Nodes (9): Dependency Inversion Principle (DIP), domain.ports, Interface Segregation Principle (ISP), Liskov Substitution Principle (LSP), Open/Closed Principle (OCP), SOLID Principles, token_validator.py, TokenIssuer (+1 more)

### Community 20 - "Frontend Entry Point Docs"
Cohesion: 0.22
Nodes (9): src/main.tsx entry script, #root div, AuthContext.tsx, client.ts, LayerChip.tsx, Login.tsx, ManageAccessModal.tsx, MapCard.tsx (+1 more)

### Community 21 - "Frontend Lint Config"
Cohesion: 0.22
Nodes (8): plugins, rules, react/only-export-components, react/rules-of-hooks, $schema, oxc, typescript, warn

### Community 22 - "Data Model & Repository Docs"
Cohesion: 0.28
Nodes (9): Postgres Schema (Phase 2 data model), deps.py, PermissionGrantRepository, InMemoryMirroredEntityRepository, LayerRepository, MapRepository, MirroredEntityRepository (Protocol), permission_grants table (+1 more)

### Community 23 - "Icon Sprite Assets"
Cohesion: 0.43
Nodes (7): Bluesky icon (social link, butterfly logo), Discord icon (social link, game-controller/robot-face logo), Documentation icon (open book / doc outline), GitHub icon (Octocat mark), Social/people icon (two-person avatar with sparkle badge), icons.svg (frontend icon sprite sheet), X (Twitter) icon

### Community 24 - "Delegation Rule Docs"
Cohesion: 0.29
Nodes (7): AccessResolver, Delegation Rule, mock_org_hierarchy.py, Permission Model (none/read/edit), Single Responsibility Principle (SRP), Delegation Rule, Permission Scope (map/layer)

### Community 25 - "Frontend Stack Docs"
Cohesion: 0.50
Nodes (5): Oxlint, React, React Compiler, Vite, Technology Stack

### Community 26 - "External API Docs"
Cohesion: 0.50
Nodes (4): /external/v1/my-access API, API Endpoints Table, external_router.py, grants_router.py

### Community 46 - "Page"
Cohesion: 0.23
Nodes (8): AuditService, AuditLogRepository, Page, Role, Records grant/revoke actions append-only. Kept as a collaborator that Permission, `role` is the NEW role the grantee ends up with., `role` is the NEW role the restriction entry ends up with., AuditLogEntry

### Community 47 - "SystemRole"
Cohesion: 0.32
Nodes (4): Protocol, SystemRole, Kept separate from PermissionGrantRepository on purpose: system roles have no re, SystemRoleRepository

### Community 48 - "set_grant"
Cohesion: 0.21
Nodes (13): get_me(), list_mock_users(), login(), AuthService, Depends, SystemRoleRepository, LoginRequest, LoginResponse (+5 more)

### Community 49 - "test_access_resolver.py"
Cohesion: 0.07
Nodes (18): A workspace-wide grant normally reaches every descendant. Flipping     inherits_, The barrier only blocks what would have come from ABOVE it — a grant     placed, Regression guard: with zero Restriction rows anywhere, effective_role     must b, A restriction 'is greater than any auth' — an actor not on the     whitelist get, Baseline: an unlisted actor is denied by a workspace-level     restriction. Once, The user explicitly rejected a 'last one set wins' rule — ties among     restric, Confirmed 2026-07-31: both system-wide roles are "greater than any     permissio, Confirmed 2026-07-31: SUPER_VIEWER's blanket Viewer-cap is meant to     apply ev (+10 more)

### Community 50 - "test_catalog_service.py"
Cohesion: 0.12
Nodes (12): _find(), Confirmed 2026-07-31: a personal workspace is invisible to anyone who     can't, A non-owner with a real, explicit grant somewhere inside another     user's pers, A grant on a single Layer, with no role on the Map itself, still makes     that, A grant on just one Layer (nothing on the Map itself) still makes the     Map's, Confirmed 2026-07-31: the caller's own personal workspace always shows     first, test_can_fetch_bubbles_up_from_a_single_accessible_layer(), test_catalog_no_search_returns_full_workspace_tree_annotated_none() (+4 more)

### Community 51 - "lifespan"
Cohesion: 0.17
Nodes (15): ExternalMapAccessOut, ExternalMyAccessPageOut, get_my_access(), BaseModel, Depends, CatalogItem, CatalogService, ExternalAccessItem (+7 more)

### Community 52 - "is_valid_child"
Cohesion: 0.25
Nodes (8): ResourceModel, async_sessionmaker, AsyncSession, Page, Resource, ResourceType, SqlAlchemyResourceRepository, _to_domain()

### Community 53 - "get_my_access"
Cohesion: 0.30
Nodes (13): AuditAction, GranteeType, Pure domain entities. No FastAPI/SQLAlchemy imports allowed here., No member list here — membership is mutable, queryable state owned by     TeamRe, System-wide bypass roles — no resource_id, never resource-scoped., ResourceType, Role, role_rank() (+5 more)

### Community 55 - "InMemoryTeamRepository"
Cohesion: 0.13
Nodes (7): _HasIdAndName, InMemoryEntityRepository, Protocol, T, Generic in-memory implementation of EntityRepository, shared by the Resource and, InMemoryTeamRepository, Team

### Community 56 - "PermissionGrantRepository"
Cohesion: 0.27
Nodes (7): RestrictionModel, async_sessionmaker, AsyncSession, Restriction, Role, SqlAlchemyRestrictionRepository, _to_domain()

### Community 57 - "unit/conftest.py"
Cohesion: 0.21
Nodes (3): InMemoryGrantRepository, Role, _GrantKey

### Community 58 - "env.py"
Cohesion: 0.24
Nodes (17): get_resource_service(), create_resource(), create_team_workspace(), delete_resource(), get_my_workspace(), move_resource(), Depends, Resource (+9 more)

### Community 59 - "build_engine_and_sessionmaker"
Cohesion: 0.40
Nodes (4): AsyncEngine, build_engine_and_sessionmaker(), async_sessionmaker, AsyncSession

### Community 60 - "get_catalog"
Cohesion: 0.22
Nodes (17): get_current_user(), get_token_validator(), delete_grant(), _ensure_resource_exists(), list_grants_for_resource(), list_manageable_users(), Depends, GranteeTypePath (+9 more)

### Community 61 - "AdfsAuthMockTokenIssuer"
Cohesion: 0.15
Nodes (12): Backend, Configuration, Frontend, Known limitations (deliberate, tracked in `PLAN.md`/`CLAUDE.md`), Permissions Server, Prerequisites, Project layout, Quick start (always DB/Postgres mode) (+4 more)

### Community 65 - "Role"
Cohesion: 0.17
Nodes (7): Restriction, Role, The explicit restriction row for this exact (grantee, resource), or None., Every restriction entry (any grantee) directly on this resource —         drives, Every restriction entry (any grantee) across a SET of resource ids.         Unli, Every restriction entry across ALL resources, for a set of         grantees (a u, Set/replace the restriction entry for (grantee, resource).

### Community 66 - "AccessTransparencyService"
Cohesion: 0.08
Nodes (29): FastAPI, Translates domain/errors.py exceptions into HTTP responses, in one place — indiv, register_error_handlers(), check_access(), my_access(), Depends, _to_out(), audit_for_actor() (+21 more)

### Community 67 - "check_access"
Cohesion: 0.29
Nodes (6): grantee_passes_org_chart_check(), is_within_actors_personal_workspace(), OrgHierarchy, Shared by PermissionGrantService.can_manage and RestrictionService's own delegat, A personal workspace's owner has full authority over its whole     subtree, rega, Normally just the actor's org-chart subordinates — the only users         they c

### Community 68 - ".__init__"
Cohesion: 0.18
Nodes (13): CatalogItem, createResource(), deleteResource(), ResourceType, roleAtLeast(), CreateResourceModal(), CreateResourceModalProps, TYPE_OPTIONS (+5 more)

### Community 69 - "TeamModel"
Cohesion: 0.24
Nodes (8): TeamMembershipModel, TeamModel, async_sessionmaker, AsyncSession, Team, SqlAlchemyTeamRepository, _to_domain(), Base

### Community 70 - "SystemRoleModel"
Cohesion: 0.19
Nodes (8): _enum(), SQLAlchemy ORM models — the Postgres-facing mirror of domain/entities.py. Column, SystemRoleModel, async_sessionmaker, AsyncSession, SystemRole, SqlAlchemySystemRoleRepository, SqlEnum

### Community 71 - "AuthContext.tsx"
Cohesion: 0.43
Nodes (7): clearStoredToken(), getMe(), getMyWorkspace(), getStoredToken(), setStoredToken(), AuthContext, AuthProvider()

### Community 72 - "RestrictionService"
Cohesion: 0.11
Nodes (16): AccessResolver, SystemRoleRepository, TeamRepository, PermissionGrantService, OrgHierarchy, UserDirectory, Owns the delegation rule end-to-end. Grantee-agnostic: operates on a Grantee (us, OrgHierarchy (+8 more)

### Community 73 - "lifespan"
Cohesion: 0.80
Nodes (4): create_app(), lifespan(), _seed_root_grants(), FastAPI

### Community 74 - "InMemorySystemRoleRepository"
Cohesion: 0.27
Nodes (11): delete_restriction(), list_restrictions(), Depends, GranteeTypePath, Response, Restriction, set_restriction(), _to_out() (+3 more)

### Community 75 - "Ltree"
Cohesion: 0.14
Nodes (7): upgrade(), Ltree, Custom SQLAlchemy type for PostgreSQL's ltree, used only by ResourceModel.path (, ltree labels allow only letters, digits, and underscores — resource ids     (uui, Maps a Python str (dot-separated labels, e.g. 'ws_city.f_infra') to     PostgreS, sanitize_label(), UserDefinedType

### Community 76 - "audit_for_resource"
Cohesion: 0.20
Nodes (5): InMemoryRestrictionRepository, Restriction, Role, restriction_repo(), _RestrictionKey

### Community 77 - "RoleBadge.tsx"
Cohesion: 0.50
Nodes (3): Role, ROLE_STYLES, RoleBadgeProps

### Community 79 - "get_catalog"
Cohesion: 0.15
Nodes (13): Resource, ResourceType, Editor+ at the parent may add a child under it — 'editor can edit         conten, Lazy personal workspace: any authenticated user may fetch (or, on         first, Superuser-only. The specified admin_user_id — not necessarily the         caller, Actor must be Admin (hierarchical) at the resource being moved and         Edito, is_valid_child(), test_folder_allows_folder_map_and_layer_directly() (+5 more)

### Community 80 - "AccessTransparencyService"
Cohesion: 0.15
Nodes (11): AccessSnapshot, Resource, Restriction, Role, The one place effective role is computed. Never re-implement this resolution log, The restriction twin of nearest_grants. Unlike grants, a node is         gated b, Ties among multiple grants (or restriction entries) at the nearest         ances, A user's full grant set, pre-indexed for O(1) lookups. Grants come from     the (+3 more)

### Community 81 - "RestrictionService"
Cohesion: 0.20
Nodes (5): AuditLogRepository, Protocol, Newest-first. Append-only — no update/delete method on this port,         by des, Page, InMemoryAuditLogRepository

### Community 82 - "MockOrgHierarchy"
Cohesion: 0.24
Nodes (5): MockOrgHierarchy, Verifies the visited-set guards in MockOrgHierarchy actually stop traversal on c, test_is_manager_of_still_finds_real_relationships(), test_is_manager_of_terminates_instead_of_looping_forever(), test_subordinates_of_terminates_and_finds_real_subordinates()

### Community 83 - "load_mock_users"
Cohesion: 0.27
Nodes (5): MockUserDirectory, load_mock_users(), MockUserRecord, Shared loader for mock_users.json — the single parse point used by both mock_use, TypedDict

### Community 84 - "paginate"
Cohesion: 0.16
Nodes (9): paginate(), AsyncSession, Shared offset/limit + count logic for every SQLAlchemy repo that pages a `select, async_sessionmaker, AsyncSession, SqlAlchemyAuditLogRepository, _to_domain(), M (+1 more)

### Community 85 - "register_error_handlers"
Cohesion: 0.27
Nodes (8): createTeamWorkspace(), listMockUsers(), Me, MockUser, AuthContextValue, CreateTeamWorkspaceModal(), CreateTeamWorkspaceModalProps, Login()

### Community 86 - ".__init__"
Cohesion: 0.31
Nodes (7): get_catalog(), Depends, _to_out(), CatalogItemOut, CatalogPageOut, BaseModel, CatalogItem

### Community 88 - "EntityRepository"
Cohesion: 0.40
Nodes (3): EntityRepository, T, Shared read contract for entities identified by id and searchable by name. Backs

### Community 89 - "OrgHierarchy"
Cohesion: 0.33
Nodes (3): OrgHierarchy, Protocol, Manager-chain lookups the delegation rule depends on. Both methods are     trans

### Community 90 - "TokenValidator"
Cohesion: 0.40
Nodes (3): Protocol, Validates a bearer token and returns who it belongs to.      Phase 2 swap point:, TokenValidator

### Community 91 - "GrantOut"
Cohesion: 0.67
Nodes (3): GrantOut, BaseModel, SetGrantRequest

## Ambiguous Edges - Review These
- `Documentation icon (open book / doc outline)` → `Social/people icon (two-person avatar with sparkle badge)`  [AMBIGUOUS]
  frontend/public/icons.svg · relation: conceptually_related_to

## Knowledge Gaps
- **115 isolated node(s):** `Stack`, `Prerequisites`, `Backend`, `Frontend`, `Try it` (+110 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **10 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **What is the exact relationship between `Documentation icon (open book / doc outline)` and `Social/people icon (two-person avatar with sparkle badge)`?**
  _Edge tagged AMBIGUOUS (relation: conceptually_related_to) - confidence is low._
- **Why does `Grantee` connect `Permission Grant Domain & Tests` to `Role`, `AccessTransparencyService`, `check_access`, `Mock Org & User Directory`, `RestrictionService`, `lifespan`, `Auth Service & Token Issuer`, `audit_for_resource`, `Page`, `.upsert_grant`, `AccessTransparencyService`, `test_access_resolver.py`, `Error Handling`, `paginate`, `get_my_access`, `PermissionGrantRepository`, `unit/conftest.py`, `get_catalog`?**
  _High betweenness centrality (0.201) - this node is a cross-community bridge._
- **Why does `AuthenticatedUser` connect `Auth Service & Token Issuer` to `Permission Grant Domain & Tests`, `AccessTransparencyService`, `check_access`, `TokenValidator`, `RestrictionService`, `InMemorySystemRoleRepository`, `App Bootstrap & JWT Issuer`, `Page`, `get_catalog`, `set_grant`, `Access Resolution Logic`, `lifespan`, `load_mock_users`, `get_my_access`, `.__init__`, `env.py`, `get_catalog`?**
  _High betweenness centrality (0.107) - this node is a cross-community bridge._
- **Are the 26 inferred relationships involving `Grantee` (e.g. with `seed()` and `AccessResolver`) actually correct?**
  _`Grantee` has 26 INFERRED edges - model-reasoned connections that need verification._
- **Are the 15 inferred relationships involving `AuthenticatedUser` (e.g. with `ExternalMapAccessOut` and `ExternalMyAccessPageOut`) actually correct?**
  _`AuthenticatedUser` has 15 INFERRED edges - model-reasoned connections that need verification._
- **Are the 54 inferred relationships involving `login_as()` (e.g. with `test_login_then_me_round_trip()` and `test_catalog_search_filters_by_name()`) actually correct?**
  _`login_as()` has 54 INFERRED edges - model-reasoned connections that need verification._
- **Are the 42 inferred relationships involving `auth_headers()` (e.g. with `test_login_then_me_round_trip()` and `test_protected_route_with_garbage_token_is_401()`) actually correct?**
  _`auth_headers()` has 42 INFERRED edges - model-reasoned connections that need verification._