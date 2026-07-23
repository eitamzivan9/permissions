# CLAUDE.md — Permissions Server

Permissions/access-control server for the geography team's resource tree (workspaces,
folders, maps, groups, layers). Owns *permissions only* — never resource feature data,
never a users table. Two responsibilities: (1) a web UI listing every resource in the
system with the logged-in user's own effective role, letting managers/admins grant or
change access for people below them (or for Teams), (2) `/external/v1/my-access`, an
API other internal apps call (forwarding the end-user's ADFS JWT) to get the maps a
user can reach.

See `PLAN.md` at the project root for the full implementation plan (architecture, data
model, file guide, API endpoint list, build sequence). This file is the durable,
always-loaded summary of the rules that must not silently drift.

## Core philosophy: SOLID, and no duplicated code

This is a hard requirement for every change in this codebase, not a style preference:

- **SRP**: each repository, service, and router does exactly one job (e.g.
  `AccessResolver` only computes effective role; it never authorizes writes).
- **OCP**: new behavior (a new resource type, a new grantee kind, a new repository
  backend) extends `domain.ports`/`application` code, it doesn't modify their
  internals. Adding a resource type is a new entry in `_ALLOWED_CHILD_TYPES`
  (`domain/entities.py`), not a new class hierarchy.
- **LSP**: every implementation of a `domain.ports` Protocol (in-memory or SQLAlchemy;
  mock or, later, real ADFS) must be a drop-in substitute — same inputs, same outputs,
  same errors.
- **ISP**: ports stay small and single-purpose (e.g. `TokenIssuer` vs `TokenValidator`
  are separate, because real ADFS only ever validates).
- **DIP**: `application/` and `api/` depend only on `domain.ports` interfaces, never on
  concrete `infrastructure/` classes — concrete classes are wired in exactly once, in
  `api/deps.py`.
- **No duplicated code**, specifically: don't write near-identical logic once per
  resource type or once per grantee type. All 5 resource types (Workspace/Folder/
  Map/Group/Layer) share **one** `Resource` entity and **one** `ResourceRepository`;
  user- and team-grantees share **one** `Grantee` shape, **one**
  `PermissionGrantRepository` method set, and **one** grants router
  (`/grants/{resource_id}/{grantee_type}/{grantee_id}`) — never a second near-copy
  router or resolver path per grantee type. Before adding a new file, check whether an
  existing repository, service, or component already does this and should be extended
  instead.

## Deployment context — two phases

Built *outside* the organization's closed network first (no access to real
Postgres/ADFS), then moved inside. **Storage swap (done)**: `config.py`'s
`database_url` (unset → in-memory, set → real Postgres via SQLAlchemy) now actually
branches in `main.py`'s `lifespan` — both `infrastructure/memory/*` and
`infrastructure/repositories/sqlalchemy_*` implementations of every `domain.ports`
repository exist and are interchangeable. **Still mocked**: ADFS auth
(`domain/ports/token_validator.py`/`token_issuer.py` still wrap mock issuers/
validators) and the resource tree's data source (`infrastructure/seed_data.py` is
still hand-written mock data, just now optionally loaded into Postgres via
`scripts/seed.py` instead of only into memory). Never hardcode a connection or bypass
`domain.ports` to "just make it work" — that's exactly what breaks a swap like this.

## Stack

- Backend: Python, FastAPI. Storage: in-memory repositories
  (`infrastructure/memory/`) when `database_url` is unset; PostgreSQL via SQLAlchemy
  (async) + Alembic (`infrastructure/db/`, `infrastructure/repositories/`,
  `alembic/`) when it's set. The resource tree's Postgres table adds a `path` column
  using Postgres's `ltree` extension (`infrastructure/db/types.py`) so
  `ResourceRepository.path_to_root()` — called on every access check via
  `AccessResolver` — is one indexed ancestor-containment query instead of an
  O(depth) walk up `parent_id`. `backend/tests/conftest.py` force-unsets
  `PERMISSIONS_DATABASE_URL` so the test suite always runs hermetically against
  in-memory repos regardless of whether `backend/.env` sets it for normal runs.
- Frontend: React + TypeScript (Vite) + Tailwind, calls the backend as a JSON API.
- Auth: ADFS-issued JWT in production; **currently mocked**, backed by the standalone
  `adfs-auth` library (`C:\Users\Eitam\adfs-auth`, installed as a path dependency) —
  `infrastructure/auth/adfs_auth_mock_issuer.py`/`adfs_auth_mock_validator.py` wrap its
  `testing.MockTokenAcquirer`/`MockTokenValidator`, with users resolved via
  `UserDirectory` (fixture-backed,
  `backend/src/permissions_server/infrastructure/auth/_mock_users_fixture.py`) since
  the library's mock tokens only carry a verified `sub`, not name/email. `TokenIssuer`/
  `TokenValidator` (`domain/ports/`) are `async` to match the library's shape — see
  `domain/ports/token_validator.py` for the Phase 2 real-ADFS swap point
  (`adfs_auth.oidc.OidcJwtValidator`, not yet wired in — no real ADFS reachable yet).

## Architecture (hexagonal — enforced, not optional)

`domain/` (entities + Protocol ports, zero framework imports) → `application/`
(use-case services, depend only on `domain.ports`) → `infrastructure/` (in-memory or
SQLAlchemy repos, mock/real JWT, org-hierarchy adapters) → `api/` (FastAPI routers +
`deps.py` DI wiring).

**Repo singletons, not per-request instances.** In-memory repositories live on
`app.state`, built once at startup — a per-request instance silently resets all data.
See `api/deps.py` and `main.py`'s `lifespan`.

## Resource hierarchy

5 resource types in one tree, one `Resource` entity (`domain/entities.py`) — no
separate dataclass per type: **Workspace → Folder → Map → Group → Layer**. Legal
parent/child pairs live in `_ALLOWED_CHILD_TYPES` / `is_valid_child()`:
- Workspace and Folder may directly contain a Folder, a Map, **or** a Layer (skipping
  levels is legal — a resource doesn't have to nest through every intermediate type).
- Folders nest indefinitely (Folder → Folder).
- Map may directly contain a Group or a Layer.
- Groups nest indefinitely (Group → Group) and may directly contain a Layer.
- Layer is always a leaf.
- Only a Workspace may be a tree root (`parent_id is None`).

Each `Resource` also carries `inherits_from_parent: bool` (default `True`). Setting it
`False` on a resource walls off that resource and everything below it from any
ancestor's grant — `AccessResolver`'s climb stops there even if no explicit grant
exists at that node — without having to enumerate every affected grantee. There is no
API route to flip this yet (no resource-admin endpoints exist at all in Phase 1;
resources come only from `infrastructure/seed_data.py`); it's exercised today via
`ResourceRepository.set_inherits_from_parent()` directly.

## Permission model

- **Per-resource roles**, ranked: `Viewer < Editor < Manager < Admin` (`Role` +
  `role_rank()` in `domain/entities.py`). A grant assigns one role to one `Grantee`
  (a user or a Team) at one resource.
- **System-wide roles**, resource-independent, checked first and bypass everything:
  `SUPER_EDITOR` (acts as Admin everywhere) and `SUPER_VIEWER` (acts as Viewer
  everywhere).
- **Inheritance**: nearest-ancestor-wins. `AccessResolver.effective_role()` climbs from
  a resource up through its ancestors and returns the role at the *nearest* ancestor
  (inclusive) that has any explicit grant for the caller (directly or via a Team they
  belong to) — ties among multiple grants at that same node break by highest rank.
  There is no "sticky none" role; the only way to cut inheritance short is the
  `inherits_from_parent` flag above, not a grant value.
- Effective role is always computed by `application/access_resolver.py`
  (`AccessResolver`) — never re-implement this resolution logic elsewhere (a router,
  the frontend); `CatalogService`, `PermissionGrantService`, and
  `AccessTransparencyService` all go through it so they can't drift apart.

## UI scope

The main page lists **every** resource in the system (not just ones the caller has
access to), each annotated with the caller's own `effective_role` (possibly `None`),
`can_manage`, and `can_fetch`. `can_fetch` bubbles up from descendants: a resource with
no role of its own is still `can_fetch=true` if the caller can reach even one
descendant (e.g. a Map is fetchable if the caller has a role on just one Layer inside
it, since the map has to load to render that layer). Search matches any resource by
name at any depth, returning it with its full subtree. A "manage access" affordance
appears only where `can_manage` is true (effective role is Manager or Admin).

## Delegation rule (who can change whose grant)

`PermissionGrantService.can_manage()` — role-rank check applies to **both** grantee
kinds: the actor needs `effective_role` (via `AccessResolver`) of Manager or Admin at
the resource; Admin may grant/revoke any role, Manager may only grant/revoke
Editor/Viewer (never Manager/Admin). **This project's own addition on top of the
reference design**, user grantees only: the actor must *also* be above the target user
in the org management chain (transitive — see `infrastructure/auth/mock_org_hierarchy.py`).
Team grantees skip the org-chart check entirely — a Team isn't a person in an org
chart, only the role-rank check applies. `SUPER_EDITOR` bypasses both checks. Always
re-checked server-side on every write (`grant()`/`revoke()`) — a `can_manage` flag
returned to the UI is a display hint only, never a trust boundary.

## Audit log

Append-only (`AuditLogRepository` has no update/delete method by design).
`AuditService` records one of `GRANT` (brand-new grant for that grantee+resource),
`ROLE_CHANGE` (an existing grant's role changed), or `REVOKE`. A re-grant of the exact
same role is a no-op and logs nothing.

## Permission transparency

`AccessTransparencyService.explain_access()` returns every contributing source (system
role, or each grant at the nearest ancestor with any grant) with an `is_effective` flag
on the one that actually wins. `my_access` exposes this for the caller's own access,
ungated; `check_access` lets a Manager+ (or system role) inspect anyone else's access to
a resource, gated the same way `can_manage`'s role-rank check is.

## Scale assumptions

~2,000-3,000 users, 5,000-10,000 maps (each with a handful of layers). List/search
endpoints (`/catalog`, `/external/v1/my-access`) are paginated by design — do not add
an unpaginated "list everything" endpoint, in-memory or Postgres. The mock user fixture
is intentionally small (~30-50 users) for readability; don't assume its size reflects
production scale when reasoning about performance — check against the row counts above
instead.

## Known, deliberate departures from the reference design docs (do not "fix" — ask first)

The reference docs (PDF design doc, Hebrew docx spec, and the `sk-permissions` repo)
describe a **whitelist-only visibility model** ("everything invisible by default,"
siblings hidden unless explicitly granted, restrict/unrestrict cascading). This project
deliberately keeps **universal visibility** instead — every resource is shown to every
user — confirmed with the project owner. There is intentionally no `restrict`/
`unrestrict` mechanism and no corresponding audit actions for it.

## Known deferred work (do not silently "fix" — ask first)

- Real ADFS validation (wiring `adfs-auth`'s real `oidc.OidcJwtValidator`/
  `OidcAuthorizationCodeAcquirer` behind the same ports — the library itself is
  wired in now, just still in mock mode), real sync of resources from the
  source-of-truth system (currently `infrastructure/seed_data.py`, static mock data,
  now also the source `scripts/seed.py` loads into Postgres), real org hierarchy
  source (currently the JSON-derived fixture) — likely AD/ADFS groups eventually.
  (Real Postgres repositories are done — see "Deployment context" above.)
- No API route to create resources or toggle `inherits_from_parent` — Phase 1 has no
  resource-admin endpoints at all.

## Agent behavior (inherits workspace-level rules, restated for this project)

- Ambiguous requirement → ask, don't assume (see workspace `~/CLAUDE.md`).
- SOLID and no-duplication (above) are enforced, not optional — new code must depend on
  `domain.ports`, not on concrete `infrastructure` classes, and must not duplicate logic
  across resource types, grantee types, or repository backends.
- Always build and run (`uvicorn` backend + `npm run dev` frontend — no DB setup needed
  in Phase 1) and manually verify the affected flow before reporting a change as done.

## graphify

This project has a knowledge graph at graphify-out/ with god nodes, community structure, and cross-file relationships.

Rules:
- For codebase questions, first run `graphify query "<question>"` when graphify-out/graph.json exists. Use `graphify path "<A>" "<B>"` for relationships and `graphify explain "<concept>"` for focused concepts. These return a scoped subgraph, usually much smaller than GRAPH_REPORT.md or raw grep output.
- If graphify-out/wiki/index.md exists, use it for broad navigation instead of raw source browsing.
- Read graphify-out/GRAPH_REPORT.md only for broad architecture review or when query/path/explain do not surface enough context.
- After modifying code, run `graphify update .` to keep the graph current (AST-only, no API cost).
