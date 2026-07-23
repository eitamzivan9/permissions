# Permissions Server — Implementation Plan

See `CLAUDE.md` at the project root for the durable, always-loaded rules (SOLID/
no-duplication requirement, architecture boundaries, permission model, delegation
rule). This file is the detailed design and current-state file guide behind those
rules — read it before starting or resuming implementation.

## Context

The geography team's resource tree (workspaces → folders → maps → groups → layers)
lives in a separate system. There is no central place to manage *who can see/edit
which resource*, and no API other internal apps can call to find out "what maps can
this user see". This project builds a standalone **permissions server**: (1) a web UI
where users authenticate (via ADFS, mocked for now) and manage access for people below
them in the org (or for Teams), and (2) a machine-facing endpoint other apps call
(forwarding the end-user's JWT) to get the maps a user can access. The permissions DB
stores only permission grants plus a mirrored id/name copy of the resource tree —
never the actual map/layer data, and never a users table (identity stays
mocked/external).

The domain model here converges toward a richer reference design (a PDF design doc, a
Hebrew docx dev spec, and the `sk-permissions` reference repo) — 5-level resource
hierarchy, 4-role model, Teams, audit log, permission transparency — but implemented
fresh inside this project's own hexagonal architecture, not by cloning the reference
repo. Two confirmed, deliberate departures from those docs: (1) universal visibility
(every resource is shown to every user) instead of the docs' whitelist-only model, and
(2) an org-chart delegation check layered on top of role-rank for individual-user
grants (not present in the reference docs), kept for user grantees only — not for Team
grants, matching the docs there.

**Deployment context**: the organization's real ADFS lives inside a closed/air-gapped
network, unreachable from where this is being built; a local PostgreSQL install became
available first. So this plan has two phases, and the storage half of Phase 2 is
now done ahead of the ADFS half:
- **Phase 1 (now, outside the network)**: build and fully run the whole system —
  backend, frontend, mock auth — with **no real database at all**. Repositories are
  in-memory implementations behind the same `domain.ports` interfaces every other
  implementation uses.
- **Phase 2 storage (done)**: real PostgreSQL repository implementations (same
  `domain.ports` interfaces) exist alongside the in-memory ones, wired in via
  `config.py`'s `database_url` — no changes to `domain/` or `application/` were
  needed. See "Postgres persistence (done)" below for the concrete file list.
- **Phase 2 auth (later, inside the network)**: once there's real ADFS access, wire
  the already-built `adfs-auth` library's real OIDC validator behind
  `domain/ports/token_validator.py`/`token_issuer.py` — no changes to `domain/` or
  `application/` here either.

Scale to design for: **~2,000–3,000 users, 5,000–10,000 maps** (each with a handful of
layers, so tens of thousands of layer rows). This rules out anything O(n) over "every
resource" per request and means the catalog/search/external endpoints need pagination
from day one.

## Confirmed decisions (do not re-litigate)

- **Visibility**: universal — the catalog shows every resource to every user, not just
  ones they can access (deliberate departure from the reference docs' whitelist model).
- **Delegation rule**: actor's *effective* role at the target resource must be Manager
  or Admin (Manager may only grant Editor/Viewer, never Manager/Admin); for **user**
  grantees, the actor must additionally be transitively above the target user in the
  org management chain — this project's own addition, not in the reference docs; for
  **Team** grantees, only the role-rank check applies.
- **Inheritance**: nearest-ancestor-wins, generalized across all 5 levels — the closest
  ancestor (inclusive) with any explicit grant wins outright over a farther one; ties
  among multiple grantees at that same node (a direct user grant plus N team grants)
  break by highest role rank. `inherits_from_parent=False` on a resource is a separate,
  per-resource circuit-breaker that stops the climb at that node regardless of grants.
- **Resource mirror**: permissions DB stores mirrored `id + name + type + parent_id`
  only; real sync from the source-of-truth system is out of scope for now — seed with
  mock data (`infrastructure/seed_data.py`, loaded into Postgres by `scripts/seed.py`).
- **External API auth**: calling apps forward the end-user's ADFS JWT (not a service
  API key).
- **Mock ADFS/org hierarchy**: mock users + manager hierarchy live in a small fixture
  (`infrastructure/auth/_mock_users_fixture.py`). No `users` table anywhere, in memory
  or Postgres — grants reference free-text user ids matching the fixture (future: AD
  objectGUID/UPN), so swapping in real ADFS/AD touches zero schema.
- **Storage swap (done)**: `config.py`'s `database_url` is what selects which
  implementation `main.py`'s `lifespan` wires onto `app.state` (unset → in-memory;
  set → real Postgres via SQLAlchemy — see "Postgres persistence" below). Tests force
  `database_url` unset (`backend/tests/conftest.py`) so they stay hermetic regardless
  of `backend/.env`.
- **Stack**: Python + FastAPI backend, PostgreSQL via SQLAlchemy (async) + Alembic
  (now in the codebase), React + TypeScript (Vite) + Tailwind frontend as a separate
  SPA calling the backend as a JSON API.
- **Real ADFS support**: developed as a separate standalone library, `adfs-auth`
  (`C:\Users\Eitam\adfs-auth`, own repo/versioning, installed here as a path
  dependency), covering both token acquisition (OIDC authorization-code + PKCE, for
  client apps) and token validation (for resource servers like this one). **Wired in
  now, in mock mode**: `infrastructure/auth/adfs_auth_mock_issuer.py` and
  `adfs_auth_mock_validator.py` wrap the library's `testing.MockTokenAcquirer`/
  `MockTokenValidator`. Swapping to the library's real `oidc.OidcJwtValidator`/
  `OidcAuthorizationCodeAcquirer` behind `domain/ports/token_validator.py`/
  `token_issuer.py` is Phase 2 (no real ADFS reachable yet).

## Architecture

Backend is layered/hexagonal to satisfy the SOLID/no-duplication requirement in
`CLAUDE.md`. This is not just a style choice — it's the concrete mechanism behind both
swaps this project needs: mock auth → real ADFS, and in-memory storage → real Postgres,
each isolated to one `infrastructure/` module behind an unchanged `domain.ports`
interface.

```
domain/        pure entities + Protocol interfaces ("ports"), no FastAPI/SQLAlchemy imports
application/   use-case services, depend only on domain ports
infrastructure/  concrete adapters: in-memory repos (Phase 1) / SQLAlchemy repos (Phase 2), mock JWT, JSON-derived org hierarchy
api/           FastAPI routers + DI wiring (deps.py), depend on application services
```

**Where duplication is deliberately designed out**:
- All 5 resource types (Workspace/Folder/Map/Group/Layer) are **one** `Resource`
  dataclass and **one** `ResourceRepository`, not five near-identical entities/repos —
  legality of a parent/child pair is one data table (`_ALLOWED_CHILD_TYPES`), not a
  branching type hierarchy.
- User- and Team-grantees are **one** polymorphic `Grantee` concept — one
  `PermissionGrantRepository` method set, one `PermissionGrantService`, one grants
  router parametrized by `grantee_type` in the path, not separate code paths per
  grantee kind.
- `AccessResolver` is the single place effective role is computed — `CatalogService`,
  `PermissionGrantService.can_manage`, and `AccessTransparencyService` all call it
  rather than re-deriving inheritance logic.
- The mock resource tree is defined **once**, in `infrastructure/seed_data.py`, reused
  by the in-memory repos at startup now and (Phase 2) by a seed script populating
  Postgres.

```
Premissions/
├── CLAUDE.md                 # durable rules — read first
├── PLAN.md                   # this file
├── backend/
│   ├── pyproject.toml
│   ├── src/permissions_server/
│   │   ├── main.py                    # app factory, CORS, router mounting, lifespan, root-grant bootstrap
│   │   ├── config.py                  # pydantic Settings: database_url, JWT secret/alg, CORS origins
│   │   ├── domain/
│   │   │   ├── entities.py            # ResourceType, Resource (+is_valid_child), Role(+role_rank),
│   │   │   │                          # SystemRole, GranteeType/Grantee, Team, PermissionGrant,
│   │   │   │                          # AuditAction/AuditLogEntry, AuthenticatedUser
│   │   │   ├── errors.py              # DomainError, NotFoundError, UnauthorizedError, ForbiddenError, ConflictError
│   │   │   └── ports/
│   │   │       ├── entity_repository.py       # Page[T] + EntityRepository[T] Protocol (get_by_id, list_page)
│   │   │       ├── resource_repository.py      # +children_of, path_to_root, list_by_type, create, set_inherits_from_parent
│   │   │       ├── team_repository.py           # +list_members, list_teams_for_user, add/remove_member, create
│   │   │       ├── grant_repository.py           # get_grant, list_grants_for_resource/grantees, upsert_grant, delete_grant
│   │   │       ├── system_role_repository.py     # list_system_roles, grant_system_role
│   │   │       ├── audit_log_repository.py       # append, list_for_resource, list_for_actor
│   │   │       ├── token_issuer.py / token_validator.py  # async; split per ISP: mock issues+validates, real ADFS only ever validates
│   │   │       ├── user_directory.py             # get_user, list_users, search_users
│   │   │       └── org_hierarchy.py              # is_manager_of(a,b) transitive, subordinates_of(a)
│   │   ├── application/
│   │   │   ├── access_resolver.py             # effective_role, nearest_grants, snapshot_for_user — single source of truth
│   │   │   ├── permission_grant_service.py    # can_manage (delegation rule), grant/revoke (+audit), list_manageable_users
│   │   │   ├── audit_service.py               # record_grant/record_role_change/record_revoke, history_for_resource/actor
│   │   │   ├── access_transparency_service.py # explain_access, my_access, check_access
│   │   │   ├── catalog_service.py             # full resource tree annotated per-caller, + external "my maps" view
│   │   │   └── auth_service.py                 # mock-login, "who am I"
│   │   ├── infrastructure/
│   │   │   ├── seed_data.py               # THE mock resource tree + Teams/memberships — single source
│   │   │   ├── memory/
│   │   │   │   ├── in_memory_entity_repository.py   # generic base: shared dict-backed get/list/search
│   │   │   │   ├── in_memory_resource_repository.py  # ResourceRepository impl, seeded from seed_data.py
│   │   │   │   ├── in_memory_team_repository.py
│   │   │   │   ├── in_memory_grant_repository.py       # keyed by (Grantee, resource_id)
│   │   │   │   ├── in_memory_system_role_repository.py
│   │   │   │   └── in_memory_audit_log_repository.py    # append-only, no update/delete method by design
│   │   │   ├── db/                      # Postgres engine/session/ORM models (SQLAlchemy)
│   │   │   │   ├── types.py               # Ltree TypeDecorator + sanitize_label() for resources.path
│   │   │   │   ├── base.py                # DeclarativeBase
│   │   │   │   ├── models.py              # ResourceModel/TeamModel/TeamMembershipModel/PermissionGrantModel/SystemRoleModel/AuditLogModel
│   │   │   │   └── session.py             # build_engine_and_sessionmaker(database_url)
│   │   │   └── auth/
│   │   │       ├── _mock_users_fixture.py    # small representative fixture (~30-50 users, 3+ hierarchy levels)
│   │   │       ├── mock_user_directory.py
│   │   │       ├── mock_org_hierarchy.py      # walks manager chains; cycle-safe (visited-set guard)
│   │   │       ├── adfs_auth_mock_issuer.py    # TokenIssuer, wraps adfs_auth.testing.MockTokenAcquirer
│   │   │       └── adfs_auth_mock_validator.py # TokenValidator, wraps adfs_auth.testing.MockTokenValidator + UserDirectory
│   │   ├── repositories/                # SQLAlchemy repos — one per domain.ports Protocol, mirrors infrastructure/memory/
│   │   │   ├── _pagination.py             # shared count+offset+limit helper (resource/team/audit-log repos)
│   │   │   ├── sqlalchemy_resource_repository.py  # path_to_root via one ltree containment query, not O(depth)
│   │   │   ├── sqlalchemy_team_repository.py
│   │   │   ├── sqlalchemy_grant_repository.py     # grantee_key() — collision-safe dict-key equivalent for nullable user_id/team_id
│   │   │   ├── sqlalchemy_system_role_repository.py
│   │   │   └── sqlalchemy_audit_log_repository.py
│   │   └── api/
│   │       ├── deps.py                # DI providers; repos are app.state singletons built once at startup
│   │       ├── error_handlers.py      # maps domain/errors.py -> HTTP status codes
│   │       ├── schemas/{auth,catalog,grant,team,access,audit}_schemas.py
│   │       └── routers/
│   │           ├── auth_router.py       # /auth
│   │           ├── catalog_router.py    # /catalog
│   │           ├── grants_router.py     # /grants — one PUT + DELETE pair, grantee_type is a path param
│   │           ├── teams_router.py      # /teams
│   │           ├── access_router.py     # /access — permission transparency
│   │           ├── audit_router.py      # /audit
│   │           └── external_router.py   # /external/v1 — evolves independently of the UI's contract
│   ├── alembic.ini / alembic/{env.py,script.py.mako,versions/0001_initial_schema.py}
│   ├── scripts/seed.py                # idempotent: seed_data.py -> Postgres + root bootstrap grant
│   ├── .env                           # PERMISSIONS_DATABASE_URL (git-ignored, local-only; unset = in-memory mode)
│   └── tests/{unit,integration}/{conftest.py,...}  # conftest.py force-unsets database_url so tests stay in-memory
└── frontend/
    └── src/{pages,components,api,auth}/  # Login, Permissions pages; typed API client; AuthContext (sessionStorage-backed)
```

**Still not built**: a real `domain/ports/token_validator.py`/`token_issuer.py`
implementation wrapping the `adfs-auth` library (Phase 2 auth), and real resource sync
replacing `seed_data.py` as the source of truth.

## Domain model

- **`ResourceType`**: `WORKSPACE`, `FOLDER`, `MAP`, `GROUP`, `LAYER`. One `Resource`
  dataclass for all five (`id`, `type`, `name`, `parent_id`, `inherits_from_parent`).
  Legality of a parent/child pair: Workspace/Folder → Folder, Map, or Layer directly
  (levels may be skipped); Folder → Folder (indefinite nesting); Map → Group or Layer;
  Group → Group (indefinite nesting) or Layer; Layer is always a leaf. Only a Workspace
  may have `parent_id is None`.
- **`Role`**: `VIEWER < EDITOR < MANAGER < ADMIN`, ranked via `role_rank()`.
- **`SystemRole`**: `SUPER_EDITOR` / `SUPER_VIEWER` — global, not resource-scoped,
  bypass `AccessResolver`'s normal climb entirely.
- **`Grantee`**: polymorphic — `GranteeType.USER` (`user_id` set) xor
  `GranteeType.TEAM` (`team_id` set), validated in `__post_init__`.
- **`Team`**: id/name only; membership is separate mutable state in
  `TeamRepository`, not baked into the frozen entity.
- **`PermissionGrant`**: `(grantee, resource_id, role, granted_by)`.
- **`AuditAction`**: `GRANT` / `ROLE_CHANGE` / `REVOKE`. `AuditLogEntry` is
  append-only.

## Core services

- **`AccessResolver`** (`application/access_resolver.py`) — the one place effective
  role is computed. `snapshot_for_user()` gathers a user's own grants plus every Team
  they belong to into one indexed `AccessSnapshot`. `nearest_grants()` walks a
  resource's `path_to_root()` from the resource itself upward, returning the nearest
  node (inclusive) with any grant — stopping early if it passes a node with
  `inherits_from_parent=False`. `effective_role()` layers the `SystemRole` bypass on
  top and breaks ties among multiple grants at the winning node by highest rank.
- **`PermissionGrantService`** — `can_manage()` implements the delegation rule
  end-to-end (role-rank for both grantee kinds, plus the org-chart check for user
  grantees only); `grant()`/`revoke()` always re-check `can_manage` server-side, then
  write, then record to `AuditService` (`GRANT` for a new grantee+resource pair,
  `ROLE_CHANGE` when an existing grant's role changes, nothing for a same-role no-op);
  `list_manageable_users()` powers the "grant to whom" picker via
  `org_hierarchy.subordinates_of()`.
- **`AuditService`** — thin, focused wrapper around `AuditLogRepository`; a separate
  collaborator from `PermissionGrantService` because "record what happened" is a
  different reason to change than "decide if it's allowed."
- **`AccessTransparencyService`** — `explain_access()` returns every contributing
  `AccessSource` (system role or grant) at the nearest ancestor with any grant, with
  `is_effective` marking the winner; `my_access` exposes this ungated for the caller's
  own access; `check_access` gates inspecting someone else's access on Manager+ (or a
  system role).
- **`CatalogService`** — builds the paginated, searchable **full** resource tree:
  `get_catalog()` (search or top-level Workspaces, each node annotated with
  `effective_role`, `can_manage`, and `can_fetch` — the last bubbling up from
  descendants) and `get_external_access()` (flat Map-only view, reusing the same
  `can_fetch` bubbling to decide which maps a caller can reach).

## Postgres persistence (done)

Real SQLAlchemy (async) repositories now exist alongside the in-memory ones, one class
per `domain.ports` Protocol, in `infrastructure/repositories/`. `main.py`'s `lifespan`
branches on `get_settings().database_url`: unset builds the exact same in-memory block
as before; set builds an async engine/sessionmaker and the SQLAlchemy repos instead,
onto the same `app.state.*` attribute names — `api/deps.py` and everything above it
needed zero changes (DIP in action).

- **Resource tree uses `ltree`**: `resources.path` is a Postgres `ltree` column (a
  dot-separated chain of ancestor ids, hyphens sanitized to underscores since `ltree`
  labels disallow them — `infrastructure/db/types.py`). `parent_id` is kept too, as a
  plain column, for `children_of()`. `path` turns `path_to_root()` — called by
  `AccessResolver` on essentially every access check — into one indexed ancestor
  query (`path @> CAST(:leaf_path AS ltree) ORDER BY nlevel(path)`) instead of an
  O(depth) walk up `parent_id`. Computed once, in Python, at `create()` time — not a
  DB trigger.
- **Grant uniqueness**: a plain `UNIQUE(grantee_type, user_id, team_id, resource_id)`
  wouldn't actually work — standard SQL treats two rows sharing a NULL column as
  non-duplicate. `PermissionGrantModel.grantee_key` (a computed, always-non-null
  string — `sqlalchemy_grant_repository.grantee_key()`) is what the unique index and
  every lookup/upsert actually key off, mirroring the in-memory repo's
  `(Grantee, resource_id)` dict key exactly.
- **Enums stored as `VARCHAR`**, not native Postgres enum types
  (`native_enum=False` in `models.py`) — adding a new `Role`/`ResourceType`/etc. value
  later is a one-line Python change, not an `ALTER TYPE` migration (OCP).
- **No users table, in Postgres either** — `user_directory`/`org_hierarchy`/
  `token_issuer`/`token_validator` are untouched by `database_url`; they stay on their
  mock/JSON-backed implementations in both storage modes.
- **Schema**: `alembic/versions/0001_initial_schema.py` — `CREATE EXTENSION ltree`
  then all 6 tables (`resources`, `teams`, `team_memberships`, `permission_grants`,
  `system_roles`, `audit_log`) + a GiST index on `resources.path`.
- **Seeding**: `scripts/seed.py` loads `seed_data.py`'s `RESOURCES`/`TEAMS`/
  `TEAM_MEMBERSHIPS` straight into the ORM models (not via
  `ResourceRepository.create()`, which always mints a fresh uuid — seed ids must stay
  fixed since later rows reference earlier ones by `parent_id`), plus the same
  root-user (`u001`) bootstrap Admin grant `main.py`'s in-memory lifespan creates
  automatically. Idempotent (safe to re-run against an already-seeded database).
- **Tests stay hermetic**: `backend/tests/conftest.py` force-sets
  `PERMISSIONS_DATABASE_URL=""` before any other import, so `pytest` always exercises
  in-memory repos even though `backend/.env` sets the real variable for normal
  `uvicorn` runs. Without this, `.env` silently makes the test suite hit the live dev
  database.

## API endpoints

| Method | Path | Auth | Purpose |
|---|---|---|---|
| GET | `/auth/mock-users` | none | list pickable mock identities for the login screen |
| POST | `/auth/login` | none | mock ADFS: issue an HS256 JWT for the chosen mock user |
| GET | `/auth/me` | Bearer | current user's name/email for the page header |
| GET | `/catalog?q=&page=&page_size=` | Bearer | **every** resource, annotated with `effective_role`/`can_manage`/`can_fetch`, paginated, searchable by name at any depth |
| GET | `/grants/manageable-users` | Bearer | subordinates the caller may grant to |
| GET | `/grants/{resource_id}` | Bearer | list grants directly on a resource |
| PUT | `/grants/{resource_id}/{grantee_type}/{grantee_id}` | Bearer | set/change a grant — `grantee_type` is `user` or `team`; body `{role}` |
| DELETE | `/grants/{resource_id}/{grantee_type}/{grantee_id}` | Bearer | remove a grant row |
| GET | `/teams` | Bearer | list Teams |
| POST | `/teams` | Bearer | create a Team |
| GET | `/teams/{team_id}/members` | Bearer | list a Team's members |
| POST/DELETE | `/teams/{team_id}/members/{user_id}` | Bearer | add/remove a Team member |
| GET | `/access/my-access/{resource_id}` | Bearer | explain the caller's own access to a resource |
| GET | `/access/check-access/{resource_id}/{user_id}` | Bearer | Manager+/system-role only: explain someone else's access |
| GET | `/audit/resource/{resource_id}` | Bearer | audit history for a resource |
| GET | `/audit/actor/{actor_id}` | Bearer | audit history by actor |
| GET | `/external/v1/my-access?page=&page_size=` | Bearer (forwarded end-user JWT) | other apps: maps the caller can reach + role, paginated over all maps |

One handler pair implements both grantee-type cases for grants (PUT/DELETE) — see
`grants_router.py` — rather than four near-duplicate routes.

## Bootstrap (Phase 1 dev convenience)

With an empty grant table nobody has Manager+ to delegate from, so nobody could make
the first grant through the API. `main.py`'s `lifespan` seeds the one user with no
manager (`ROOT_USER_ID = "u001"`) with `Admin` on every top-level Workspace — Admin
cascades the whole subtree via the nearest-ancestor climb, so one grant per Workspace
replaces one grant per resource. Not a permanent rule; Phase 2 replaces this with
whatever real grants already exist in Postgres.

## Known gaps vs. the reference design docs (tracked, not silently fixed)

- Universal visibility instead of the docs' whitelist-only model — deliberate,
  confirmed (see `CLAUDE.md`).
- No `restrict`/`unrestrict` mechanism or corresponding audit actions — follows from
  the visibility departure above.
- No API surface to create resources or toggle `inherits_from_parent` yet — Phase 1
  has no resource-admin endpoints at all; only exercised via the repository directly.

## Build sequence (current state: Phase 1 + Phase 2 storage complete and passing)

Phase 1 is built and green: `domain/entities.py` + all `domain/ports/*.py` →
`infrastructure/seed_data.py` → in-memory repositories → mock auth infra →
`application/*` services (heaviest coverage on `AccessResolver`'s inheritance climb and
`PermissionGrantService`'s delegation rule) → `api/deps.py` DI wiring + all 7 routers +
`main.py` → frontend (Vite+TS+Tailwind, typed API client, `AuthContext`, login +
main + manage-access pages). 79 backend tests passing (`pytest`).

**Phase 2 storage is built and verified** against a real local PostgreSQL 18 install:
`sqlalchemy[asyncio]` + `asyncpg` + `alembic` added → `infrastructure/db/`
(types/base/models/session) → `infrastructure/repositories/sqlalchemy_*_repository.py`
mirroring each in-memory repo → `alembic/versions/0001_initial_schema.py` → `main.py`
lifespan branches on `settings.database_url` → `scripts/seed.py`. See "Postgres
persistence" above for the `ltree`/`grantee_key` design decisions.

**Phase 2 auth** (later, once inside the org network, not built yet): wire the
already-built `adfs-auth` library's real OIDC validator behind
`domain/ports/token_validator.py`/`token_issuer.py`; also still deferred: real
resource sync replacing `seed_data.py`/`scripts/seed.py` as the source of truth, and a
real org-hierarchy source (AD/ADFS groups). Re-run the full Phase 1 verification
walkthrough against real ADFS once that's wired in.

## Verification

**Phase 1 (in-memory mode):**
1. `uvicorn permissions_server.main:app --reload` with `PERMISSIONS_DATABASE_URL`
   unset (backend, in-memory repos, no setup needed), `npm run dev` (frontend).
2. Manual walkthrough: mock-login as the root user or a manager → confirm the catalog
   shows every resource with correct `effective_role`/`can_fetch` including no-access →
   search by name → grant a subordinate access on a resource they didn't have → log in
   as that subordinate → confirm the effective role is now correct → attempt a grant as
   a non-manager/non-Manager-role user and confirm `403`.
3. `pytest` for unit (access resolver, delegation, catalog bubbling, audit actions,
   org-hierarchy cycle safety) and integration (routers against in-memory repos)
   suites — currently 79/79 passing, always hermetic (`tests/conftest.py` forces
   `database_url` unset regardless of `backend/.env`).

**Phase 2 storage (done, verified against real Postgres 18 locally):**
1. `alembic upgrade head` against a fresh `permissions` database — confirms the
   `ltree` extension, all 6 tables, and the GiST index on `resources.path`.
2. `scripts/seed.py` — confirmed row counts match `seed_data.py`'s constants (41
   resources, 2 teams, 5 memberships, 1 root bootstrap grant).
3. `uvicorn` with `PERMISSIONS_DATABASE_URL` set → same manual walkthrough as Phase 1
   step 2, now backed by Postgres — confirmed identical behavior.
4. Persistence proven directly: created a grant via the API, killed the backend
   process, started a new one, confirmed the grant survived — cross-checked against
   `psql` directly, not just through the app.
5. `pytest` with `database_url` unset (the default, via `conftest.py`) still 79/79 —
   confirms the storage swap didn't regress Phase 1 in-memory mode.

**Phase 2 auth (once inside the org network, not yet applicable):** repeat the
manual walkthrough with real ADFS wired in via `adfs-auth`.
