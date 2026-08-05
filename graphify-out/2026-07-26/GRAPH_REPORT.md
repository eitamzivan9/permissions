# Graph Report - Premissions  (2026-07-23)

## Corpus Check
- 114 files · ~24,549 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 858 nodes · 1655 edges · 69 communities (62 shown, 7 thin omitted)
- Extraction: 78% EXTRACTED · 22% INFERRED · 0% AMBIGUOUS · INFERRED: 360 edges (avg confidence: 0.65)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `f2731e15`
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

## God Nodes (most connected - your core abstractions)
1. `AuthenticatedUser` - 52 edges
2. `Grantee` - 46 edges
3. `Page` - 32 edges
4. `Role` - 31 edges
5. `AccessResolver` - 30 edges
6. `SystemRole` - 28 edges
7. `Resource` - 27 edges
8. `ResourceRepository` - 24 edges
9. `get_current_user()` - 23 edges
10. `PermissionGrantService` - 23 edges

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

## Communities (69 total, 7 thin omitted)

### Community 0 - "Frontend React App"
Cohesion: 0.07
Nodes (48): ApiError, buildQueryString(), CatalogItem, CatalogPage, clearStoredToken(), deleteGrant(), DeleteGrantParams, extractErrorMessage() (+40 more)

### Community 1 - "Permission Grant Domain & Tests"
Cohesion: 0.06
Nodes (33): seed(), PermissionGrantService, Role, Owns the delegation rule end-to-end. Grantee-agnostic: operates on a Grantee (us, Role-rank rule (both grantee types): actor needs Role.MANAGER+ on         resour, Grantee, PermissionGrant, A user-scope grantee (team_id=None) or a team-scope grantee (user_id=None). (+25 more)

### Community 2 - "Catalog API & Schemas"
Cohesion: 0.08
Nodes (22): One shape for all 5 resource kinds — no separate Map/Layer dataclasses.     pare, Resource, ResourceType, Direct children only, one level down., [root, ..., resource itself] — root-first, inclusive. Single-element         lis, All resources of one type (e.g. every Workspace, or every Map),         for the, Persists a new node. Parent/child type legality (is_valid_child) is         the, Flip the inheritance-barrier flag on an existing resource (see         Resource. (+14 more)

### Community 3 - "Grants Router & DI Wiring"
Cohesion: 0.30
Nodes (16): get_access_resolver(), get_access_transparency_service(), get_audit_log_repository(), get_audit_service(), get_auth_service(), get_catalog_service(), get_grant_repository(), get_org_hierarchy() (+8 more)

### Community 4 - "Frontend Package Dependencies"
Cohesion: 0.06
Nodes (35): dependencies, react, react-dom, react-router-dom, devDependencies, oxlint, tailwindcss, @tailwindcss/vite (+27 more)

### Community 5 - "Backend Integration Tests"
Cohesion: 0.11
Nodes (29): AsyncClient, auth_headers(), client(), login_as(), A fresh app + in-memory state per test, talked to over real HTTP     semantics (, test_login_then_me_round_trip(), test_protected_route_with_garbage_token_is_401(), _find() (+21 more)

### Community 6 - "In-Memory Repositories"
Cohesion: 0.28
Nodes (6): MockOrgHierarchy, org_hierarchy(), Verifies the visited-set guards in MockOrgHierarchy actually stop traversal on c, test_is_manager_of_still_finds_real_relationships(), test_is_manager_of_terminates_instead_of_looping_forever(), test_subordinates_of_terminates_and_finds_real_subordinates()

### Community 7 - "Frontend TS App Config"
Cohesion: 0.08
Nodes (23): compilerOptions, allowArbitraryExtensions, allowImportingTsExtensions, erasableSyntaxOnly, jsx, lib, module, moduleDetection (+15 more)

### Community 8 - "Mock Org & User Directory"
Cohesion: 0.19
Nodes (6): MockUserDirectory, load_mock_users(), MockUserRecord, Shared loader for mock_users.json — the single parse point used by both mock_use, user_directory(), TypedDict

### Community 9 - "Frontend TS Node Config"
Cohesion: 0.10
Nodes (19): compilerOptions, allowImportingTsExtensions, erasableSyntaxOnly, lib, module, moduleDetection, noEmit, noFallthroughCasesInSwitch (+11 more)

### Community 10 - "Architecture & Phase Overview"
Cohesion: 0.19
Nodes (15): Permissions Server, Phase 1 (outside org network), Phase 2 (inside org network), Scale Assumptions, UI Scope, Build Sequence, External API Auth (forwarded ADFS JWT), Maps/Layers Mirror (+7 more)

### Community 11 - "App Bootstrap & JWT Issuer"
Cohesion: 0.17
Nodes (12): One-time (idempotent) loader: pushes seed_data.py's mock resource tree/teams int, get_settings(), Application settings, read from environment (.env supported). No hardcoded secre, Settings, AdfsAuthMockTokenIssuer, TokenIssuer backed by the adfs-auth library's MockTokenAcquirer — delegates, create_app(), lifespan() (+4 more)

### Community 12 - "Auth Service & Token Issuer"
Cohesion: 0.16
Nodes (8): AuthService, AuthenticatedUser, Protocol, Issues a bearer token for a user. Only the mock auth flow implements this —, TokenIssuer, Protocol, Looks up identities. Backed by mock_users.json now, real AD/ADFS later., UserDirectory

### Community 13 - "Auth Domain Ports"
Cohesion: 0.20
Nodes (11): get_current_user(), get_token_validator(), audit_for_actor(), audit_for_resource(), Depends, _to_out(), Protocol, Validates a bearer token and returns who it belongs to.      Phase 2 swap point: (+3 more)

### Community 14 - "Auth API Router & Schemas"
Cohesion: 0.29
Nodes (9): get_me(), list_mock_users(), login(), Depends, LoginRequest, LoginResponse, MockUserOut, BaseModel (+1 more)

### Community 15 - "Service Design Cross-References"
Cohesion: 0.23
Nodes (12): can_manage, Hexagonal Architecture, MirroredEntityRepository, No Duplicated Code Rule, PermissionGrantService, AccessResolver, Layered/Hexagonal Architecture, AuthService (+4 more)

### Community 16 - "Error Handling"
Cohesion: 0.09
Nodes (28): FastAPI, Translates domain/errors.py exceptions into HTTP responses, in one place — indiv, register_error_handlers(), ConflictError, DomainError, ForbiddenError, NotFoundError, Domain-level errors. api/ translates these into HTTP responses. (+20 more)

### Community 17 - "Access Resolution Logic"
Cohesion: 0.15
Nodes (17): get_team_repository(), add_team_member(), create_team(), list_team_members(), list_teams(), Depends, Response, remove_team_member() (+9 more)

### Community 18 - "JWT Validator & Auth Tests"
Cohesion: 0.25
Nodes (4): AdfsAuthMockTokenValidator, TokenValidator backed by the adfs-auth library's MockTokenValidator.      The li, test_login_issues_a_token_that_resolves_to_the_right_user(), test_login_unknown_user_raises_not_found()

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
Cohesion: 0.07
Nodes (23): AuditService, Role, Records grant/revoke actions append-only. Kept as a collaborator that Permission, `role` is the NEW role the grantee ends up with., AuditLogEntry, AuditLogRepository, Protocol, Newest-first. Append-only — no update/delete method on this port,         by des (+15 more)

### Community 47 - "SystemRole"
Cohesion: 0.14
Nodes (9): System-wide bypass roles — no resource_id, never resource-scoped., SystemRole, Protocol, Kept separate from PermissionGrantRepository on purpose: system roles have no re, SystemRoleRepository, SystemRoleModel, InMemorySystemRoleRepository, SqlAlchemySystemRoleRepository (+1 more)

### Community 48 - "set_grant"
Cohesion: 0.28
Nodes (13): delete_grant(), _ensure_resource_exists(), list_grants_for_resource(), list_manageable_users(), Depends, Response, set_grant(), _to_grantee() (+5 more)

### Community 49 - "test_access_resolver.py"
Cohesion: 0.13
Nodes (6): The barrier only blocks what would have come from ABOVE it — a grant     placed, A workspace-wide grant normally reaches every descendant. Flipping     inherits_, test_highest_rank_wins_between_direct_and_team_grant(), test_inherits_from_parent_false_still_honors_its_own_grant(), test_inherits_from_parent_false_walls_off_the_workspace_grant(), test_team_grant_used_when_no_direct_grant()

### Community 50 - "test_catalog_service.py"
Cohesion: 0.18
Nodes (6): _find(), A grant on a single Layer, with no role on the Map itself, still makes     that, A grant on just one Layer (nothing on the Map itself) still makes the     Map's, test_can_fetch_bubbles_up_from_a_single_accessible_layer(), test_catalog_no_search_returns_full_workspace_tree_annotated_none(), test_external_access_includes_map_reachable_only_via_one_layer()

### Community 51 - "lifespan"
Cohesion: 0.19
Nodes (10): AccessResolver, AccessSnapshot, Role, The one place effective role is computed. Never re-implement this resolution log, A user's full grant set, pre-indexed for O(1) lookups. Grants come from     the, Walk from resource_id up to the tree root; return         (origin_resource_id, g, Ties among multiple grants at the nearest ancestor (a direct grant         plus, ExternalAccessItem (+2 more)

### Community 52 - "is_valid_child"
Cohesion: 0.43
Nodes (7): is_valid_child(), test_folder_allows_folder_map_and_layer_directly(), test_group_nests_indefinitely(), test_layer_is_always_a_leaf(), test_map_allows_group_and_layer_only(), test_only_a_workspace_may_be_a_root(), test_workspace_allows_folder_map_and_layer_directly()

### Community 53 - "get_my_access"
Cohesion: 0.08
Nodes (19): upgrade(), Base, _enum(), SQLAlchemy ORM models — the Postgres-facing mirror of domain/entities.py. Column, TeamMembershipModel, TeamModel, Ltree, Custom SQLAlchemy type for PostgreSQL's ltree, used only by ResourceModel.path ( (+11 more)

### Community 55 - "InMemoryTeamRepository"
Cohesion: 0.18
Nodes (5): No member list here — membership is mutable, queryable state owned by     TeamRe, Team, InMemoryTeamRepository, Team, team_repo()

### Community 56 - "PermissionGrantRepository"
Cohesion: 0.22
Nodes (10): ExternalMapAccessOut, ExternalMyAccessPageOut, get_my_access(), BaseModel, Depends, CatalogItem, CatalogService, Builds the searchable, paginated resource catalog for the UI. Visibility stays u (+2 more)

### Community 57 - "unit/conftest.py"
Cohesion: 0.25
Nodes (7): access_resolver(), access_transparency_service(), audit_log_repo(), audit_service(), catalog_service(), grant_repo(), permission_grant_service()

### Community 58 - "env.py"
Cohesion: 0.53
Nodes (5): _do_run_migrations(), get_url(), run_migrations_offline(), run_migrations_online(), Connection

### Community 59 - "build_engine_and_sessionmaker"
Cohesion: 0.40
Nodes (4): AsyncEngine, build_engine_and_sessionmaker(), async_sessionmaker, AsyncSession

### Community 60 - "get_catalog"
Cohesion: 0.31
Nodes (7): get_catalog(), Depends, _to_out(), CatalogItemOut, CatalogPageOut, BaseModel, CatalogItem

### Community 61 - "AdfsAuthMockTokenIssuer"
Cohesion: 0.15
Nodes (12): Backend, Configuration, Frontend, Known limitations (deliberate, tracked in `PLAN.md`/`CLAUDE.md`), Permissions Server, Prerequisites, Project layout, Quick start (Phase 1 — in-memory, no DB setup) (+4 more)

### Community 65 - "Role"
Cohesion: 0.33
Nodes (10): AuditLogEntryOut, AuditLogPageOut, BaseModel, AuditAction, GranteeType, Pure domain entities. No FastAPI/SQLAlchemy imports allowed here., ResourceType, Role (+2 more)

### Community 66 - "AccessTransparencyService"
Cohesion: 0.39
Nodes (4): AccessSource, AccessTransparencyService, Why do I have this access' — one shared breakdown, two thin callers: my_access (, role_rank()

### Community 67 - "check_access"
Cohesion: 0.43
Nodes (6): check_access(), my_access(), Depends, _to_out(), AccessSourceOut, BaseModel

## Ambiguous Edges - Review These
- `Documentation icon (open book / doc outline)` → `Social/people icon (two-person avatar with sparkle badge)`  [AMBIGUOUS]
  frontend/public/icons.svg · relation: conceptually_related_to

## Knowledge Gaps
- **101 isolated node(s):** `Stack`, `Prerequisites`, `Backend`, `Frontend`, `Try it` (+96 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **7 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **What is the exact relationship between `Documentation icon (open book / doc outline)` and `Social/people icon (two-person avatar with sparkle badge)`?**
  _Edge tagged AMBIGUOUS (relation: conceptually_related_to) - confidence is low._
- **Why does `Grantee` connect `Permission Grant Domain & Tests` to `Role`, `AccessTransparencyService`, `App Bootstrap & JWT Issuer`, `Page`, `set_grant`, `test_access_resolver.py`, `Error Handling`, `lifespan`?**
  _High betweenness centrality (0.100) - this node is a cross-community bridge._
- **Why does `lifespan()` connect `App Bootstrap & JWT Issuer` to `Permission Grant Domain & Tests`, `Catalog API & Schemas`, `In-Memory Repositories`, `Mock Org & User Directory`, `Page`, `SystemRole`, `JWT Validator & Auth Tests`, `get_my_access`, `InMemoryTeamRepository`, `build_engine_and_sessionmaker`?**
  _High betweenness centrality (0.093) - this node is a cross-community bridge._
- **Why does `AuthenticatedUser` connect `Auth Service & Token Issuer` to `Permission Grant Domain & Tests`, `AccessTransparencyService`, `check_access`, `Role`, `Mock Org & User Directory`, `App Bootstrap & JWT Issuer`, `Auth Domain Ports`, `Auth API Router & Schemas`, `Page`, `set_grant`, `Access Resolution Logic`, `JWT Validator & Auth Tests`, `Error Handling`, `PermissionGrantRepository`, `get_catalog`?**
  _High betweenness centrality (0.086) - this node is a cross-community bridge._
- **Are the 13 inferred relationships involving `AuthenticatedUser` (e.g. with `ExternalMapAccessOut` and `ExternalMyAccessPageOut`) actually correct?**
  _`AuthenticatedUser` has 13 INFERRED edges - model-reasoned connections that need verification._
- **Are the 19 inferred relationships involving `Grantee` (e.g. with `seed()` and `AccessResolver`) actually correct?**
  _`Grantee` has 19 INFERRED edges - model-reasoned connections that need verification._
- **Are the 13 inferred relationships involving `Page` (e.g. with `AuditService` and `CatalogItem`) actually correct?**
  _`Page` has 13 INFERRED edges - model-reasoned connections that need verification._