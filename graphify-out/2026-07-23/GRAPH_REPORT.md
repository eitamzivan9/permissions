# Graph Report - .  (2026-07-20)

## Corpus Check
- Corpus is ~15,033 words - fits in a single context window. You may not need a graph.

## Summary
- 555 nodes · 937 edges · 46 communities (41 shown, 5 thin omitted)
- Extraction: 81% EXTRACTED · 19% INFERRED · 0% AMBIGUOUS · INFERRED: 179 edges (avg confidence: 0.68)
- Token cost: 147,526 input · 0 output

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

## God Nodes (most connected - your core abstractions)
1. `AuthenticatedUser` - 33 edges
2. `GrantTarget` - 31 edges
3. `PermissionGrantService` - 21 edges
4. `AccessResolver` - 19 edges
5. `PermissionLevel` - 19 edges
6. `compilerOptions` - 18 edges
7. `PermissionGrantRepository` - 17 edges
8. `CatalogService` - 15 edges
9. `LayerRepository` - 15 edges
10. `login_as()` - 15 edges

## Surprising Connections (you probably didn't know these)
- `MirroredEntityRepository` --references--> `MirroredEntityRepository (Protocol)`  [INFERRED]
  CLAUDE.md → PLAN.md
- `AccessResolver` --references--> `AccessResolver`  [INFERRED]
  CLAUDE.md → PLAN.md
- `domain.ports` --conceptually_related_to--> `MirroredEntityRepository (Protocol)`  [INFERRED]
  CLAUDE.md → PLAN.md
- `Hexagonal Architecture` --references--> `Layered/Hexagonal Architecture`  [INFERRED]
  CLAUDE.md → PLAN.md
- `Delegation Rule` --references--> `Delegation Rule`  [INFERRED]
  CLAUDE.md → PLAN.md

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **SOLID Principles Group** — claude_solid, claude_srp, claude_ocp, claude_lsp, claude_isp, claude_dip [EXTRACTED 1.00]
- **Delegation Enforcement Flow** — plan_permissiongrantservice, plan_accessresolver, plan_orghierarchy [EXTRACTED 1.00]
- **Port/Adapter/DI Wiring Pattern** — plan_mirroredentityrepository, plan_inmemorymirroredentityrepository, plan_deps_py, plan_grants_router [INFERRED 0.85]

## Communities (46 total, 5 thin omitted)

### Community 0 - "Frontend React App"
Cohesion: 0.07
Nodes (43): ApiError, buildQueryString(), CatalogResponse, clearStoredToken(), deleteGrant(), DeleteGrantParams, extractErrorMessage(), ForbiddenError (+35 more)

### Community 1 - "Permission Grant Domain & Tests"
Cohesion: 0.06
Nodes (33): PermissionGrant, PermissionLevel, GrantTarget, A map-scope target (layer_id=None) or a layer-scope target., ForbiddenError, Authenticated, but not permitted for this action — api/ maps this to 403., PermissionGrant, PermissionLevel (+25 more)

### Community 2 - "Catalog API & Schemas"
Cohesion: 0.08
Nodes (34): get_maps_catalog(), Depends, ExternalMapAccessOut, ExternalMyAccessPageOut, get_my_access(), BaseModel, Depends, CatalogPageOut (+26 more)

### Community 3 - "Grants Router & DI Wiring"
Cohesion: 0.09
Nodes (33): get_access_resolver(), get_catalog_service(), get_current_user(), get_grant_repository(), get_layer_repository(), get_map_repository(), get_org_hierarchy(), get_permission_grant_service() (+25 more)

### Community 4 - "Frontend Package Dependencies"
Cohesion: 0.06
Nodes (35): dependencies, react, react-dom, react-router-dom, devDependencies, oxlint, tailwindcss, @tailwindcss/vite (+27 more)

### Community 5 - "Backend Integration Tests"
Cohesion: 0.13
Nodes (21): AsyncClient, auth_headers(), client(), login_as(), A fresh app + in-memory state per test, talked to over real HTTP     semantics (, test_login_then_me_round_trip(), test_protected_route_with_garbage_token_is_401(), test_catalog_search_filters_by_name() (+13 more)

### Community 6 - "In-Memory Repositories"
Cohesion: 0.09
Nodes (14): Layer, InMemoryLayerRepository, InMemoryMapRepository, _HasIdAndName, InMemoryMirroredEntityRepository, Protocol, T, Generic in-memory implementation of MirroredEntityRepository, shared by the Map (+6 more)

### Community 7 - "Frontend TS App Config"
Cohesion: 0.08
Nodes (23): compilerOptions, allowArbitraryExtensions, allowImportingTsExtensions, erasableSyntaxOnly, jsx, lib, module, moduleDetection (+15 more)

### Community 8 - "Mock Org & User Directory"
Cohesion: 0.12
Nodes (12): MockOrgHierarchy, MockUserDirectory, load_mock_users(), MockUserRecord, Shared loader for mock_users.json — the single parse point used by both mock_use, org_hierarchy(), user_directory(), Verifies the visited-set guards in MockOrgHierarchy actually stop traversal on c (+4 more)

### Community 9 - "Frontend TS Node Config"
Cohesion: 0.10
Nodes (19): compilerOptions, allowImportingTsExtensions, erasableSyntaxOnly, lib, module, moduleDetection, noEmit, noFallthroughCasesInSwitch (+11 more)

### Community 10 - "Architecture & Phase Overview"
Cohesion: 0.16
Nodes (18): Hexagonal Architecture, Permission Model (none/read/edit), Permissions Server, Phase 1 (outside org network), Phase 2 (inside org network), Scale Assumptions, UI Scope, Build Sequence (+10 more)

### Community 11 - "App Bootstrap & JWT Issuer"
Cohesion: 0.21
Nodes (11): get_settings(), Application settings, read from environment (.env supported). No hardcoded secre, Settings, JwtHs256Issuer, Mock TokenIssuer — HS256, ADFS-shaped claims (sub/name/email/iat/exp)., create_app(), lifespan(), FastAPI (+3 more)

### Community 12 - "Auth Service & Token Issuer"
Cohesion: 0.19
Nodes (7): get_auth_service(), get_token_issuer(), AuthService, NotFoundError, Protocol, Issues a bearer token for a user. Only the mock auth flow implements this —, TokenIssuer

### Community 13 - "Auth Domain Ports"
Cohesion: 0.21
Nodes (7): AuthenticatedUser, Protocol, Validates a bearer token and returns who it belongs to.      Phase 2 swap point:, TokenValidator, Protocol, Looks up identities. Backed by mock_users.json now, real AD/ADFS later., UserDirectory

### Community 14 - "Auth API Router & Schemas"
Cohesion: 0.29
Nodes (9): get_me(), list_mock_users(), login(), Depends, LoginRequest, LoginResponse, MockUserOut, BaseModel (+1 more)

### Community 15 - "Service Design Cross-References"
Cohesion: 0.25
Nodes (11): can_manage, MirroredEntityRepository, No Duplicated Code Rule, PermissionGrantService, AccessResolver, Layered/Hexagonal Architecture, AuthService, CatalogService (+3 more)

### Community 16 - "Error Handling"
Cohesion: 0.24
Nodes (8): FastAPI, Translates domain/errors.py exceptions into HTTP responses, in one place — indiv, register_error_handlers(), ConflictError, DomainError, Domain-level errors. api/ translates these into HTTP responses., Base class for all domain/application errors., Exception

### Community 17 - "Access Resolution Logic"
Cohesion: 0.33
Nodes (4): AccessSnapshot, PermissionLevel, The one place effective permission is computed. Never re-implement this resoluti, A user's full grant set, pre-indexed for O(1) lookups. The single place     'lay

### Community 18 - "JWT Validator & Auth Tests"
Cohesion: 0.22
Nodes (6): Missing, malformed, or expired token — api/ maps this to 401., UnauthorizedError, JwtHs256Validator, Mock TokenValidator — HS256. Replaced (not edited around) by a real ADFS     JWK, test_login_issues_a_token_that_resolves_to_the_right_user(), test_login_unknown_user_raises_not_found()

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
Cohesion: 0.40
Nodes (5): AccessResolver, Delegation Rule, mock_org_hierarchy.py, Single Responsibility Principle (SRP), Delegation Rule

### Community 25 - "Frontend Stack Docs"
Cohesion: 0.50
Nodes (5): Oxlint, React, React Compiler, Vite, Technology Stack

### Community 26 - "External API Docs"
Cohesion: 0.50
Nodes (4): /external/v1/my-access API, API Endpoints Table, external_router.py, grants_router.py

## Ambiguous Edges - Review These
- `Documentation icon (open book / doc outline)` → `Social/people icon (two-person avatar with sparkle badge)`  [AMBIGUOUS]
  frontend/public/icons.svg · relation: conceptually_related_to

## Knowledge Gaps
- **89 isolated node(s):** `permissions-server`, `$schema`, `typescript`, `oxc`, `react/rules-of-hooks` (+84 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **5 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **What is the exact relationship between `Documentation icon (open book / doc outline)` and `Social/people icon (two-person avatar with sparkle badge)`?**
  _Edge tagged AMBIGUOUS (relation: conceptually_related_to) - confidence is low._
- **Why does `AuthenticatedUser` connect `Auth Domain Ports` to `Permission Grant Domain & Tests`, `Catalog API & Schemas`, `Grants Router & DI Wiring`, `Mock Org & User Directory`, `App Bootstrap & JWT Issuer`, `Auth Service & Token Issuer`, `Auth API Router & Schemas`, `JWT Validator & Auth Tests`?**
  _High betweenness centrality (0.085) - this node is a cross-community bridge._
- **Why does `GrantTarget` connect `Permission Grant Domain & Tests` to `App Bootstrap & JWT Issuer`, `Catalog API & Schemas`, `Grants Router & DI Wiring`?**
  _High betweenness centrality (0.074) - this node is a cross-community bridge._
- **Why does `lifespan()` connect `App Bootstrap & JWT Issuer` to `Mock Org & User Directory`, `Permission Grant Domain & Tests`, `JWT Validator & Auth Tests`, `In-Memory Repositories`?**
  _High betweenness centrality (0.064) - this node is a cross-community bridge._
- **Are the 10 inferred relationships involving `AuthenticatedUser` (e.g. with `ExternalMapAccessOut` and `ExternalMyAccessPageOut`) actually correct?**
  _`AuthenticatedUser` has 10 INFERRED edges - model-reasoned connections that need verification._
- **Are the 17 inferred relationships involving `GrantTarget` (e.g. with `PermissionGrantService` and `PermissionGrantRepository`) actually correct?**
  _`GrantTarget` has 17 INFERRED edges - model-reasoned connections that need verification._
- **Are the 11 inferred relationships involving `PermissionGrantService` (e.g. with `AccessResolver` and `AuthenticatedUser`) actually correct?**
  _`PermissionGrantService` has 11 INFERRED edges - model-reasoned connections that need verification._