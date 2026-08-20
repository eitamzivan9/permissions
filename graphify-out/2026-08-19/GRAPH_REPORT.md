# Graph Report - Premissions  (2026-08-19)

## Corpus Check
- 137 files · ~45,827 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 1199 nodes · 2490 edges · 87 communities (80 shown, 7 thin omitted)
- Extraction: 78% EXTRACTED · 22% INFERRED · 0% AMBIGUOUS · INFERRED: 545 edges (avg confidence: 0.67)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `f5305747`
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
- audit_for_resource
- RoleBadge.tsx
- AccessTransparencyService
- MockOrgHierarchy
- load_mock_users
- InMemorySystemRoleRepository
- OrgHierarchy
- TokenValidator
- .upsert_grant
- restriction_service.py
- Restriction

## God Nodes (most connected - your core abstractions)
1. `Grantee` - 87 edges
2. `AuthenticatedUser` - 74 edges
3. `login_as()` - 61 edges
4. `auth_headers()` - 48 edges
5. `AccessResolver` - 41 edges
6. `Role` - 39 edges
7. `ResourceRepository` - 39 edges
8. `Page` - 32 edges
9. `get_current_user()` - 31 edges
10. `AuditService` - 28 edges

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

## Communities (87 total, 7 thin omitted)

### Community 0 - "Frontend React App"
Cohesion: 0.09
Nodes (37): buildQueryString(), CatalogPage, CreateResourceParams, CreateTeamWorkspaceParams, deleteGrant(), DeleteGrantParams, deleteResource(), deleteRestriction() (+29 more)

### Community 1 - "Permission Grant Domain & Tests"
Cohesion: 0.24
Nodes (11): _make_admin(), Removing the LAST restriction row overall is always allowed, even if     it's Ad, Row-count can't distinguish 'added once' from 'upserted twice' (same     key jus, The orphan case the guard exists for: removing the last Admin entry     while th, test_first_restriction_auto_whitelists_the_acting_admin(), test_first_restriction_does_not_duplicate_when_actor_restricts_self(), test_revoke_admin_restriction_succeeds_when_another_admin_remains(), test_revoke_last_admin_restriction_is_conflict_when_other_entries_remain() (+3 more)

### Community 2 - "Catalog API & Schemas"
Cohesion: 0.09
Nodes (18): AccessResolver, PermissionGrantService, Owns the delegation rule end-to-end. Grantee-agnostic: operates on a Grantee (us, Orchestrates every resource-creation flow (child creation, personal workspace ge, ResourceService, Protocol, Resource, ResourceType (+10 more)

### Community 3 - "Grants Router & DI Wiring"
Cohesion: 0.22
Nodes (22): get_access_resolver(), get_audit_log_repository(), get_audit_service(), get_auth_service(), get_catalog_service(), get_grant_repository(), get_org_hierarchy(), get_permission_grant_service() (+14 more)

### Community 4 - "Frontend Package Dependencies"
Cohesion: 0.06
Nodes (35): dependencies, react, react-dom, react-router-dom, devDependencies, oxlint, tailwindcss, @tailwindcss/vite (+27 more)

### Community 5 - "Backend Integration Tests"
Cohesion: 0.05
Nodes (87): AsyncClient, auth_headers(), client(), login_as(), A fresh app + in-memory state per test, talked to over real HTTP     semantics (, test_login_then_me_round_trip(), test_protected_route_with_garbage_token_is_401(), _find() (+79 more)

### Community 6 - "In-Memory Repositories"
Cohesion: 0.13
Nodes (8): _HasIdAndName, InMemoryEntityRepository, Protocol, T, Generic in-memory implementation of EntityRepository, shared by the Resource and, InMemoryResourceRepository, Resource, ResourceType

### Community 7 - "Frontend TS App Config"
Cohesion: 0.08
Nodes (23): compilerOptions, allowArbitraryExtensions, allowImportingTsExtensions, erasableSyntaxOnly, jsx, lib, module, moduleDetection (+15 more)

### Community 8 - "Mock Org & User Directory"
Cohesion: 0.16
Nodes (12): PermissionGrant, The explicit grant row for this exact (grantee, resource), or None., Every explicit grant (any grantee) directly on this resource —         drives 'w, Every explicit grant across ALL resources, for a set of grantees (a         user, PermissionGrantModel, grantee_key(), async_sessionmaker, AsyncSession (+4 more)

### Community 9 - "Frontend TS Node Config"
Cohesion: 0.10
Nodes (19): compilerOptions, allowImportingTsExtensions, erasableSyntaxOnly, lib, module, moduleDetection, noEmit, noFallthroughCasesInSwitch (+11 more)

### Community 10 - "Architecture & Phase Overview"
Cohesion: 0.19
Nodes (15): Permissions Server, Phase 1 (outside org network), Phase 2 (inside org network), Scale Assumptions, UI Scope, Build Sequence, External API Auth (forwarded ADFS JWT), Maps/Layers Mirror (+7 more)

### Community 11 - "App Bootstrap & JWT Issuer"
Cohesion: 0.24
Nodes (9): CatalogItem, CatalogService, ExternalAccessItem, Resource, Builds the searchable, paginated resource catalog for the UI. Visibility stays u, Flat view for /external/v1/my-access: only Maps the caller can         actually, No search: paginate over top-level Workspaces, each with its full         subtre, One shape for all 5 resource kinds — no separate Map/Layer dataclasses.     pare (+1 more)

### Community 12 - "Auth Service & Token Issuer"
Cohesion: 0.08
Nodes (19): get_me(), list_mock_users(), login(), Depends, LoginRequest, LoginResponse, MeOut, MockUserOut (+11 more)

### Community 13 - "Auth Domain Ports"
Cohesion: 0.33
Nodes (3): ApiError, ForbiddenError, UnauthorizedError

### Community 14 - "Auth API Router & Schemas"
Cohesion: 0.29
Nodes (10): clearStoredToken(), getMe(), getMyWorkspace(), getStoredToken(), Me, MockUser, setStoredToken(), AuthContext (+2 more)

### Community 15 - "Service Design Cross-References"
Cohesion: 0.23
Nodes (12): can_manage, Hexagonal Architecture, MirroredEntityRepository, No Duplicated Code Rule, PermissionGrantService, AccessResolver, Layered/Hexagonal Architecture, AuthService (+4 more)

### Community 16 - "Error Handling"
Cohesion: 0.08
Nodes (27): _give_actor_role(), Team grantees skip the org-chart check entirely — only role rank     matters, ma, Self-revocation must work for an ordinary Viewer/Editor with no     Manager/Admi, Even an Admin can't be their own org-chart superior — self-revocation     must n, Regression guard: the self-revocation bypass must not leak into     revoking OTH, A personal workspace's owner has authority over its whole subtree     regardless, The bypass is scoped to the OWNER's own workspace — an Admin grant     someone e, Found via manual UI testing 2026-07-31: can_manage already lets a     SUPER_EDIT (+19 more)

### Community 17 - "Access Resolution Logic"
Cohesion: 0.13
Nodes (20): get_current_user(), get_team_repository(), add_team_member(), create_team(), list_team_members(), list_teams(), Depends, Response (+12 more)

### Community 18 - "JWT Validator & Auth Tests"
Cohesion: 0.20
Nodes (9): access_resolver(), access_transparency_service(), audit_log_repo(), audit_service(), catalog_service(), permission_grant_service(), resource_repo(), resource_service() (+1 more)

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
Cohesion: 0.06
Nodes (38): audit_for_actor(), audit_for_resource(), Depends, _to_out(), ExternalMapAccessOut, ExternalMyAccessPageOut, get_my_access(), BaseModel (+30 more)

### Community 47 - "SystemRole"
Cohesion: 0.29
Nodes (8): AsyncEngine, build_engine_and_sessionmaker(), async_sessionmaker, AsyncSession, create_app(), lifespan(), FastAPI, _seed_root_grants()

### Community 48 - "set_grant"
Cohesion: 0.39
Nodes (7): get_access_transparency_service(), check_access(), my_access(), Depends, _to_out(), AccessSourceOut, BaseModel

### Community 49 - "test_access_resolver.py"
Cohesion: 0.07
Nodes (18): A workspace-wide grant normally reaches every descendant. Flipping     inherits_, The barrier only blocks what would have come from ABOVE it — a grant     placed, Regression guard: with zero Restriction rows anywhere, effective_role     must b, A restriction 'is greater than any auth' — an actor not on the     whitelist get, Baseline: an unlisted actor is denied by a workspace-level     restriction. Once, The user explicitly rejected a 'last one set wins' rule — ties among     restric, Confirmed 2026-07-31: both system-wide roles are "greater than any     permissio, Confirmed 2026-07-31: SUPER_VIEWER's blanket Viewer-cap is meant to     apply ev (+10 more)

### Community 50 - "test_catalog_service.py"
Cohesion: 0.12
Nodes (12): _find(), Confirmed 2026-07-31: a personal workspace is invisible to anyone who     can't, A non-owner with a real, explicit grant somewhere inside another     user's pers, A grant on a single Layer, with no role on the Map itself, still makes     that, A grant on just one Layer (nothing on the Map itself) still makes the     Map's, Confirmed 2026-07-31: the caller's own personal workspace always shows     first, test_can_fetch_bubbles_up_from_a_single_accessible_layer(), test_catalog_no_search_returns_full_workspace_tree_annotated_none() (+4 more)

### Community 51 - "lifespan"
Cohesion: 0.25
Nodes (6): Missing, malformed, or expired token — api/ maps this to 401., UnauthorizedError, AdfsAuthMockTokenValidator, TokenValidator backed by the adfs-auth library's MockTokenValidator.      The li, test_login_issues_a_token_that_resolves_to_the_right_user(), test_login_unknown_user_raises_not_found()

### Community 52 - "is_valid_child"
Cohesion: 0.06
Nodes (32): upgrade(), seed(), Base, _enum(), SQLAlchemy ORM models — the Postgres-facing mirror of domain/entities.py. Column, ResourceModel, TeamMembershipModel, TeamModel (+24 more)

### Community 53 - "get_my_access"
Cohesion: 0.19
Nodes (18): get_catalog(), Depends, _to_out(), CatalogItemOut, CatalogPageOut, BaseModel, AuditAction, GranteeType (+10 more)

### Community 55 - "InMemoryTeamRepository"
Cohesion: 0.18
Nodes (5): No member list here — membership is mutable, queryable state owned by     TeamRe, Team, InMemoryTeamRepository, Team, team_repo()

### Community 56 - "PermissionGrantRepository"
Cohesion: 0.27
Nodes (7): RestrictionModel, async_sessionmaker, AsyncSession, Restriction, Role, SqlAlchemyRestrictionRepository, _to_domain()

### Community 57 - "unit/conftest.py"
Cohesion: 0.19
Nodes (4): InMemoryGrantRepository, Role, grant_repo(), _GrantKey

### Community 58 - "env.py"
Cohesion: 0.28
Nodes (14): create_resource(), create_team_workspace(), delete_resource(), get_my_workspace(), move_resource(), Depends, Resource, Response (+6 more)

### Community 59 - "build_engine_and_sessionmaker"
Cohesion: 0.43
Nodes (7): is_valid_child(), test_folder_allows_folder_map_and_layer_directly(), test_group_nests_indefinitely(), test_layer_is_always_a_leaf(), test_map_allows_group_and_layer_only(), test_only_a_workspace_may_be_a_root(), test_workspace_allows_folder_map_and_layer_directly()

### Community 60 - "get_catalog"
Cohesion: 0.28
Nodes (13): delete_grant(), _ensure_resource_exists(), list_grants_for_resource(), list_manageable_users(), Depends, GranteeTypePath, Response, set_grant() (+5 more)

### Community 61 - "AdfsAuthMockTokenIssuer"
Cohesion: 0.05
Nodes (36): 1. Database, 2. Packages — what has to be available in the closed network, 3. Auth — the biggest real gap, not just a config swap, 4. CORS and frontend↔backend wiring, 5. Secrets, 6. What does *not* change with this move, 7. Verification checklist for the move, Migrating to the Closed Network (+28 more)

### Community 65 - "Role"
Cohesion: 0.14
Nodes (10): Protocol, Restriction, Role, The explicit restriction row for this exact (grantee, resource), or None., Every restriction entry (any grantee) directly on this resource —         drives, Every restriction entry (any grantee) across a SET of resource ids.         Unli, Every restriction entry across ALL resources, for a set of         grantees (a u, Set/replace the restriction entry for (grantee, resource). (+2 more)

### Community 66 - "AccessTransparencyService"
Cohesion: 0.12
Nodes (19): AccessSource, AccessTransparencyService, Why do I have this access' — one shared breakdown, two thin callers: my_access (, Resource, ResourceType, Actor must be Admin (hierarchical) at the resource being moved and         Edito, Admin-only, same rank as move()'s source-resource check — deleting         is at, Editor+ at the parent may add a child under it — 'editor can edit         conten (+11 more)

### Community 67 - "check_access"
Cohesion: 0.20
Nodes (7): grantee_passes_org_chart_check(), is_within_actors_personal_workspace(), Shared by PermissionGrantService.can_manage and RestrictionService's own delegat, A personal workspace's owner has full authority over its whole     subtree, rega, Role, Normally just the actor's org-chart subordinates — the only users         they c, Role-rank rule (both grantee types): actor needs Role.MANAGER+ on         resour

### Community 68 - ".__init__"
Cohesion: 0.15
Nodes (17): CatalogItem, createResource(), moveResource(), ResourceType, roleAtLeast(), CreateResourceModal(), CreateResourceModalProps, TYPE_OPTIONS (+9 more)

### Community 69 - "TeamModel"
Cohesion: 0.53
Nodes (5): _do_run_migrations(), get_url(), run_migrations_offline(), run_migrations_online(), Connection

### Community 70 - "SystemRoleModel"
Cohesion: 0.28
Nodes (4): async_sessionmaker, AsyncSession, SystemRole, SqlAlchemySystemRoleRepository

### Community 71 - "AuthContext.tsx"
Cohesion: 0.20
Nodes (11): createTeamWorkspace(), getCatalog(), isSuperEditor(), listMockUsers(), ProtectedRoute(), useAuth(), CreateTeamWorkspaceModal(), CreateTeamWorkspaceModalProps (+3 more)

### Community 72 - "RestrictionService"
Cohesion: 0.67
Nodes (3): FastAPI, Translates domain/errors.py exceptions into HTTP responses, in one place — indiv, register_error_handlers()

### Community 73 - "lifespan"
Cohesion: 0.16
Nodes (8): One-time (idempotent) loader: pushes seed_data.py's mock resource tree/teams int, get_settings(), Application settings, read from environment (.env supported). No hardcoded secre, Settings, AdfsAuthMockTokenIssuer, TokenIssuer backed by the adfs-auth library's MockTokenAcquirer — delegates, auth_service(), BaseSettings

### Community 74 - "InMemorySystemRoleRepository"
Cohesion: 0.27
Nodes (11): delete_restriction(), list_restrictions(), Depends, GranteeTypePath, Response, Restriction, set_restriction(), _to_out() (+3 more)

### Community 76 - "audit_for_resource"
Cohesion: 0.13
Nodes (10): Unconditional Admin grant for target_user_id on a BRAND-NEW         resource — n, Grantee, A user-scope grantee (team_id=None) or a team-scope grantee (user_id=None)., Remove the explicit grant row; no error if it didn't exist., Remove the explicit restriction row; no error if it didn't exist., InMemoryRestrictionRepository, Restriction, Role (+2 more)

### Community 77 - "RoleBadge.tsx"
Cohesion: 0.50
Nodes (4): Role, ROLE_STYLES, RoleBadge(), RoleBadgeProps

### Community 80 - "AccessTransparencyService"
Cohesion: 0.18
Nodes (9): AccessSnapshot, Resource, Restriction, Role, The one place effective role is computed. Never re-implement this resolution log, The restriction twin of nearest_grants. Unlike grants, a node is         gated b, Ties among multiple grants (or restriction entries) at the nearest         ances, A user's full grant set, pre-indexed for O(1) lookups. Grants come from     the (+1 more)

### Community 82 - "MockOrgHierarchy"
Cohesion: 0.22
Nodes (6): MockOrgHierarchy, org_hierarchy(), Verifies the visited-set guards in MockOrgHierarchy actually stop traversal on c, test_is_manager_of_still_finds_real_relationships(), test_is_manager_of_terminates_instead_of_looping_forever(), test_subordinates_of_terminates_and_finds_real_subordinates()

### Community 83 - "load_mock_users"
Cohesion: 0.24
Nodes (6): MockUserDirectory, load_mock_users(), MockUserRecord, Shared loader for mock_users.json — the single parse point used by both mock_use, user_directory(), TypedDict

### Community 87 - "InMemorySystemRoleRepository"
Cohesion: 0.32
Nodes (3): InMemorySystemRoleRepository, SystemRole, system_role_repo()

### Community 89 - "OrgHierarchy"
Cohesion: 0.33
Nodes (3): OrgHierarchy, Protocol, Manager-chain lookups the delegation rule depends on. Both methods are     trans

### Community 90 - "TokenValidator"
Cohesion: 0.40
Nodes (3): test_check_access_forbidden_when_actor_lacks_manager_role(), test_check_access_succeeds_when_actor_is_manager(), test_explain_access_marks_the_winning_source_effective()

### Community 98 - "restriction_service.py"
Cohesion: 0.48
Nodes (6): _admin_of(), Regression guard: Map is structurally capable of having children     (Group/Laye, test_delete_empty_organizational_resource_succeeds(), test_delete_layer_with_no_children_succeeds(), test_delete_map_with_children_still_cascades(), test_delete_organizational_resource_with_children_is_conflict()

### Community 105 - "Restriction"
Cohesion: 0.20
Nodes (7): Restriction, Role, Owns setting/revoking restrictions end-to-end — a deliberately separate, Admin-o, Admin-only (NOT Manager, unlike ordinary grants where Manager         keeps its, RestrictionService, A whitelist entry, not an additive grant. Same shape as PermissionGrant     but, Restriction

## Ambiguous Edges - Review These
- `Documentation icon (open book / doc outline)` → `Social/people icon (two-person avatar with sparkle badge)`  [AMBIGUOUS]
  frontend/public/icons.svg · relation: conceptually_related_to

## Knowledge Gaps
- **137 isolated node(s):** `permissions-server`, `$schema`, `typescript`, `oxc`, `react/rules-of-hooks` (+132 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **7 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **What is the exact relationship between `Documentation icon (open book / doc outline)` and `Social/people icon (two-person avatar with sparkle badge)`?**
  _Edge tagged AMBIGUOUS (relation: conceptually_related_to) - confidence is low._
- **Why does `Grantee` connect `audit_for_resource` to `Permission Grant Domain & Tests`, `Catalog API & Schemas`, `Grants Router & DI Wiring`, `Mock Org & User Directory`, `Error Handling`, `Page`, `SystemRole`, `test_access_resolver.py`, `is_valid_child`, `get_my_access`, `PermissionGrantRepository`, `unit/conftest.py`, `get_catalog`, `Role`, `AccessTransparencyService`, `check_access`, `AccessTransparencyService`, `TokenValidator`, `.upsert_grant`, `restriction_service.py`, `Restriction`?**
  _High betweenness centrality (0.179) - this node is a cross-community bridge._
- **Why does `lifespan()` connect `SystemRole` to `In-Memory Repositories`, `SystemRoleModel`, `Mock Org & User Directory`, `lifespan`, `audit_for_resource`, `Page`, `MockOrgHierarchy`, `load_mock_users`, `lifespan`, `InMemoryTeamRepository`, `is_valid_child`, `InMemorySystemRoleRepository`, `PermissionGrantRepository`, `unit/conftest.py`?**
  _High betweenness centrality (0.117) - this node is a cross-community bridge._
- **Why does `AuthenticatedUser` connect `Page` to `AccessTransparencyService`, `Catalog API & Schemas`, `check_access`, `Restriction`, `InMemorySystemRoleRepository`, `lifespan`, `Auth Service & Token Issuer`, `audit_for_resource`, `set_grant`, `Access Resolution Logic`, `lifespan`, `load_mock_users`, `get_my_access`, `env.py`, `get_catalog`?**
  _High betweenness centrality (0.080) - this node is a cross-community bridge._
- **Are the 37 inferred relationships involving `Grantee` (e.g. with `seed()` and `AccessResolver`) actually correct?**
  _`Grantee` has 37 INFERRED edges - model-reasoned connections that need verification._
- **Are the 15 inferred relationships involving `AuthenticatedUser` (e.g. with `ExternalMapAccessOut` and `ExternalMyAccessPageOut`) actually correct?**
  _`AuthenticatedUser` has 15 INFERRED edges - model-reasoned connections that need verification._
- **Are the 59 inferred relationships involving `login_as()` (e.g. with `test_login_then_me_round_trip()` and `test_catalog_search_filters_by_name()`) actually correct?**
  _`login_as()` has 59 INFERRED edges - model-reasoned connections that need verification._