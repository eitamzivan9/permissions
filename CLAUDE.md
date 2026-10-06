# CLAUDE.md — Permissions Server

Permissions/access-control server for the geography team's resource tree (workspaces,
folders, maps, groups, layers). Owns *permissions only* — never resource feature data,
never a users table. Two responsibilities: (1) a web UI listing every resource the
logged-in user can reach (plus the path above it), with their own effective role, letting managers/admins grant or
change access for people below them (or for Teams), (2) `/external/v1/my-access`, an
API other internal apps call (forwarding the end-user's ADFS JWT) to get the maps a
user can reach.

See `docs/PLAN.md` for the full implementation plan (architecture, data model, file
guide, API endpoint list, build sequence). This file (`CLAUDE.md`, kept at the project
root — see `README.md`'s "Project layout" for why it and `README.md` are the two docs
not under `docs/`) is the durable, always-loaded summary of the rules that must not
silently drift. See `docs/DATABASE.md` for the full Postgres schema reference and
`docs/migration/CLOSED_NETWORK_MIGRATION.md` for what changes when this moves from the
current open network to the organization's closed network (different Postgres instance,
real ADFS, offline/mirrored package sourcing) — read that before touching anything
auth- or database-connection-related for that move.
`docs/migration/OPENSHIFT_MIGRATION.md` covers the separate concern of actually
deploying/running the app on OpenShift once inside that closed network.

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

## Running the app — ALWAYS in DB (Postgres) mode

Do not run against in-memory repositories for normal dev/testing — only the test suite
(which force-unsets `PERMISSIONS_DATABASE_URL`, see `backend/tests/conftest.py`) should
ever use in-memory. `backend/.env` already has `PERMISSIONS_DATABASE_URL` pointing at a
local Postgres. `Settings.env_file` is resolved relative to the process's **current
working directory**, not the file's location — starting uvicorn from the repo root
silently misses `backend/.env` and falls back to in-memory. Always `cd backend` first.
Two terminals, one line each. Git Bash uses `&&`; PowerShell 5.1 rejects `&&` as a
statement separator — use `;` there instead:

```bash
# Terminal 1 — backend, DB mode (http://localhost:8000) — Git Bash
cd backend && .venv/Scripts/python.exe -m uvicorn permissions_server.main:app --reload
```

```powershell
# Terminal 1 — backend, DB mode (http://localhost:8000) — PowerShell
cd backend; .venv/Scripts/python.exe -m uvicorn permissions_server.main:app --reload
```

```bash
# Terminal 2 — frontend (http://localhost:5173) — either shell
npm --prefix frontend run dev
```

One-time setup before the first run (idempotent, safe to re-run): `cd backend`, then
`alembic upgrade head` followed by `python scripts/seed.py`.

**Docker alternative**: `docker compose up` at the repo root runs the same three pieces
(Postgres, backend, frontend) in containers — see `docker-compose.yml`,
`backend/Dockerfile`, `frontend/Dockerfile`. `backend/.env` itself is untouched by this
path (the compose file overrides `PERMISSIONS_DATABASE_URL` to reach the `db` service by
name instead), so the two-terminal workflow above keeps working unchanged either way.
`backend/docker-entrypoint.sh` runs the same idempotent `alembic upgrade head` +
`scripts/seed.py` on every container start, so there's no separate manual setup step
inside Docker. Both Dockerfile and `.gitlab-ci.yml` rewrite `pyproject.toml`'s
`adfs-auth` local-path dependency at build/CI time (via `sed`, never touching the
committed file) to a reachable source — a copied build context locally in Docker, the
sibling `adfs-auth` GitLab repo in CI — since neither a container nor a CI runner can
see `C:\Users\Eitam\adfs-auth`. This is the same workaround `CLOSED_NETWORK_MIGRATION.md`
describes as the eventual real fix (publish `adfs-auth` to a package index) not yet
having been done.

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
exists at that node — without having to enumerate every affected grantee. There is
still no API route to flip this flag (it's exercised only via
`ResourceRepository.set_inherits_from_parent()` directly) — but resource creation
itself is no longer Phase-1-only static seed data; see "Resource creation, personal &
team workspaces, move" below.

## Resource creation, personal & team workspaces, move

`application/resource_service.py` (`ResourceService`) is the one place all of this is
orchestrated — validate → authorize → write → auto-grant, never duplicated per flow:
- `create_child(actor, type, name, parent_id)` — `POST /resources`. Requires the actor
  hold `effective_role` ≥ Editor at `parent_id` (restriction-aware for free, since it
  goes through `AccessResolver`); the creator is auto-granted Admin on the new resource
  via `PermissionGrantService.bootstrap_admin_grant()` (bypasses `can_manage` —
  inapplicable on a brand-new resource with no admin yet). The endpoint itself accepts
  any `ResourceType` — **no backend restriction** — but `CreateResourceModal.tsx` only
  offers Folder (Group creation is backend-only by deliberate choice, confirmed with the
  project owner — the frontend picker has no type selector at all, just a name field):
  this server doesn't own Map/Layer data, so creating those (and Group, now) is meant to
  happen server-to-server or manually, not from this UI. That server-to-server path
  isn't built yet (no service-credential auth exists) — `POST /resources` stays open and
  callable manually in the meantime; see "Known deferred work" below.
- `delete(actor, resource_id)` — `DELETE /resources/{id}`. Admin-only, same as before,
  but now type-dependent: for Workspace/Folder/Group (`is_organizational()` in
  `domain/entities.py`) it only succeeds when `children_of(resource_id)` is empty (409
  `ConflictError` otherwise) — this server must never bulk-wipe Map/Layer data nested
  under a folder-level delete. Map/Layer keep the original unconditional-cascade
  delete (every grant/restriction in the subtree cleaned up, then the resource rows) —
  deliberately untouched, since Map is structurally capable of holding children too but
  represents data this server doesn't own. The frontend never calls this endpoint for
  Map/Layer at all: `ResourceInfoPanel.tsx`'s action is "Delete" (Workspace/Folder/Group,
  Admin-gated, and only offered when the resource has no children — a non-empty one
  shows a disabled note instead, so the action is never offered only to fail) or "Remove
  access" (Map/Layer, any role) — the latter calls
  `DELETE /grants/{resource_id}/user/{actor_id}` instead, revoking only the acting
  user's own grant, never touching the Resource row. Self-revocation this way is
  always allowed regardless of role-rank or org-chart position — see "Delegation
  rule" below. The 409 conflict message for a non-empty delete never includes the
  resource id — it's not actionable for the caller and doesn't need to leak.
- `get_or_create_my_workspace(actor)` — `GET /resources/my-workspace`. Every
  authenticated user gets exactly one personal root Workspace, identified by
  `Resource.owner_id == actor.id` (`ResourceRepository.find_workspace_by_owner()`).
  Idempotent — called fire-and-forget from the frontend's `AuthContext` right after
  `/auth/me` resolves on every login, so it exists without any explicit "create my
  workspace" action. `CatalogService.get_catalog()`'s no-search branch always pins the
  caller's own personal workspace first in the top-level Workspace list (via
  `list_by_type(..., pinned_id=...)` on `ResourceRepository`) — confirmed 2026-07-31,
  so it's visible without hunting through alphabetical/paginated results.
- `create_team_workspace(actor, name, admin_user_id)` — `POST /resources/workspaces`,
  `SUPER_EDITOR`-only (403 otherwise). Creates a root Workspace (no `owner_id`) and
  grants Admin to `admin_user_id`, which need not be the caller. Frontend: a
  "+ Create team workspace" button in `Permissions.tsx`, gated by
  `isSuperEditor(user)` (reads `Me.system_roles` from `/auth/me`).
- `move(actor, resource_id, new_parent_id)` — `PATCH /resources/{id}/move`. Requires
  Admin at the resource being moved and Editor+ at the destination; rejects moving a
  resource into its own subtree (checked via `path_to_root(new_parent_id)`). Frontend:
  **drag-and-drop only** (confirmed with the project owner — the earlier search-and-pick
  `MoveResourceModal.tsx` picker is gone, not kept as a fallback). `ResourceNode.tsx`
  makes a row `draggable` only when `effective_role === "admin"` (mirrors the backend's
  source-resource check — a UX hint only, the server re-checks regardless); every row is
  a valid drop target, with a rejected drop (wrong type pairing, into-own-subtree, no
  Editor+ at the destination) surfacing the server's exact error message inline on the
  drop-target node. A drop onto the dragged node itself is a client-side no-op — no
  request is sent.

**Personal-workspace delegation bypass**: normally granting/restricting a *user*
grantee requires the actor be transitively above that user in the org chart (see
"Delegation rule" below). `application/delegation_rules.py`'s
`grantee_passes_org_chart_check()` adds one exception, shared by both
`PermissionGrantService.can_manage` and `RestrictionService.can_set_restriction`: if
the resource's root is the actor's own personal workspace
(`is_within_actors_personal_workspace()`, via `path_to_root()[0].owner_id`), the
org-chart check is skipped entirely — an owner can grant/restrict *anyone* inside their
own sandbox. `list_manageable_users(actor, resource_id=...)` mirrors this: inside the
actor's own workspace it returns every user, not just org-chart subordinates.

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

## Restrictions (whitelist gate)

A `Restriction` (`domain/entities.py`) is a **separate dataclass from `PermissionGrant`**
— same `(grantee, resource_id, role, granted_by)` shape, but the opposite meaning: the
mere *existence* of any restriction row at a resource gates it completely. Precedence
in `AccessResolver.effective_role()`, in order: (1) `SUPER_EDITOR` bypasses
unconditionally, before any restriction lookup; (2) `nearest_restriction()` — the
restriction twin of `nearest_grants()`, same nearest-ancestor-wins/`inherits_from_parent`
semantics — if found, a grantee NOT listed there gets `None` regardless of any grant
they hold (even an Admin grant), fully short-circuiting step 4; a listed grantee gets
the highest-rank matching entry's role; (3) otherwise, ordinary `nearest_grants()`
resolution, unchanged. **`SUPER_VIEWER` bypasses restrictions too** (checked right
after `SUPER_EDITOR`, before the restriction lookup even runs) — confirmed 2026-07-31:
both system-wide roles are "greater than any [resource-level] permission," including
restrictions; `SUPER_VIEWER` just resolves to Viewer instead of Admin. (Prior to
2026-07-31 this was the opposite — only `SUPER_EDITOR` bypassed — see git history on
`access_resolver.py` if that matters.) **Exception, also confirmed 2026-07-31**:
`SUPER_VIEWER`'s Viewer-cap does NOT apply inside the actor's own personal workspace —
there, resolution falls through normally to their own bootstrap Admin grant, so being
made `SUPER_VIEWER` never demotes someone in their own sandbox. `SUPER_EDITOR` needed
no equivalent carve-out (Admin is already the ceiling everywhere).

Only Admin (or `SUPER_EDITOR`) may set/revoke a restriction —
`RestrictionService.can_set_restriction`, never Manager — via
`PUT`/`DELETE /restrictions/{resource_id}/{grantee_type}/{grantee_id}`, same org-chart
+ personal-workspace-bypass rule as grants (`delegation_rules.py`, above). Frontend:
`RestrictionsModal.tsx`, wired into `ResourceNode.tsx` behind an "Restrictions" button
gated on `effective_role === "admin"` (mirrors the backend check exactly).

**Auto-whitelist + last-admin guard (confirmed with the project owner — supersedes the
old "no self-lockout guard" behavior)**: `RestrictionService.set_restriction()` — the
FIRST restriction ever placed on a resource (zero existing restriction rows there)
auto-whitelists the acting admin as `Admin`, in addition to whoever they explicitly
listed, so setting a restriction can never lock the setting admin out of their own
first restriction. `revoke_restriction()` enforces the inverse invariant: removing an
`Admin`-role restriction entry is rejected (409 `ConflictError`) if doing so would
leave the resource STILL gated (other restriction rows remain) with zero `Admin`-role
entries left — "we don't want orphaned object access." Removing the truly last
restriction row overall is always allowed, even if it's `Admin`-role — that's a full
unrestrict (falls back to ordinary grants), not an orphan, and `RestrictionsModal.tsx`'s
"Clear all" needs to be able to reach zero (it loops single deletes sequentially, not
`Promise.all`, so a rejected entry doesn't abort ones that would otherwise succeed).
Self-lockout is still possible via a **different** admin's restriction that doesn't
list you (e.g. two admins on the same resource, one restricts naming only themselves)
— only your own *first* restriction can no longer lock you out.

This **reverses part of** the "Known, deliberate departures" section below — see that
section for the history. Restrictions now also drive *visibility*: a resource you're not
whitelisted on is hidden from you (see "UI scope").

## UI scope

**Reachable-only visibility (confirmed with the project owner 2026-10-06 — replaces the
earlier universal-visibility design).** The main page lists only resources the caller
can reach: a resource appears iff its `can_fetch` is true — the caller has an
`effective_role` there OR at any descendant. `can_fetch` bubbles up (e.g. a Map is
fetchable if the caller has a role on just one Layer inside it), so the **path** above a
reachable resource still shows, with `effective_role=None`, so the tree shows where it
lives; unreachable siblings/branches are pruned from `children`, and a top-level
Workspace with nothing reachable inside is hidden entirely. Restrictions count: a
non-whitelisted caller has no role there, so it's hidden too. Exceptions: the caller's
OWN personal workspace always shows (pinned first, no-search), and
`SUPER_EDITOR`/`SUPER_VIEWER` see everything (`AccessResolver.reaches_everything()`).

Implementation (`CatalogService.get_catalog()`): for system-role holders, the repo's
own pagination over the whole tree is used unchanged. For everyone else it starts from
`AccessResolver.access_anchor_ids()` — every resource where the caller (or one of their
teams) holds a grant or a restriction-whitelist entry, the only places a role can come
from — climbs each to its root, builds those roots' pruned trees, and paginates the
result in memory. Cost is bounded by what the caller holds, not tree size, and `total`
is exact (a page is never short because of hidden items). Search matches any visible
resource by name at any depth (same case-insensitive substring as `list_page`),
returning it with its pruned subtree. If a new access source is ever added to
`effective_role()`, `access_anchor_ids()` must learn about it too, or those resources
silently disappear from the catalog.

**Hiding is catalog-only, by design (confirmed with the project owner 2026-10-06 — do
not "fix" by gating).** Two read endpoints stay ungated for any authenticated caller,
even for a resource hidden from them: `GET /grants/{resource_id}` (other backends need
to look up who has what access by id) and `GET /access/admins/{resource_id}` (anyone
must be able to find a resource's owners to contact them).

**Per-resource actions live behind one "i" info button, not a row of buttons**
(confirmed with the project owner — supersedes the original one-button-per-action row).
`ResourceNode.tsx` renders just the row itself (expand chevron, type/name, role badge,
drag handle when applicable) plus that single info button; clicking it opens
`ResourceInfoPanel.tsx`, which owns the same gating logic the row used to and renders
whichever actions currently apply: "+ Create" (`CreateResourceModal.tsx`, Folder only —
see "Resource creation..." above) at Editor+; "Manage access" (`ManageAccessModal.tsx`)
where `can_manage` is true (Manager or Admin); "Restrictions" (`RestrictionsModal.tsx`)
at Admin only; "Delete" (Workspace/Folder/Group, Admin, empty-only — a non-empty one
shows a disabled note instead, never an offered-then-failing button) or "Remove access"
(Map/Layer, any role that holds one) instead of Delete. Move is not in this panel at
all — it's drag-and-drop only, directly on the row (see "Resource creation..." above).
When the caller's own `effective_role` here is `None`, the panel also shows an "Owners"
section — every grantee (user or team) that resolves to Admin at the nearest ancestor
gating this resource, via `GET /access/admins/{resource_id}`
(`AccessResolver.nearest_admins()` / `AccessTransparencyService.list_admins()`) — so the
caller knows who to ask; this lookup only fires when there's no access, never as a
wasted round trip when there already is one.

The catalog list itself is paginated at `PAGE_SIZE = 20` (`Permissions.tsx`) with a
"Show all" control instead of Previous/Next — clicking it loops the same paginated
`getCatalog` client call (never an unpaginated endpoint, see "Scale assumptions" below)
to fetch the rest and appends into one flat, scrollable list, hiding the button once
everything is loaded. Kept on its own loading flag, separate from the primary
`isLoading`, for the same reason described next.

`Permissions.tsx`'s catalog render must never gate the resource-tree block on
`isLoading` alone (only on `items.length === 0`, for the true first load) — every modal
(`ManageAccessModal`, `RestrictionsModal`, `CreateResourceModal`) lives inside
`ResourceInfoPanel`, which itself lives inside a `ResourceNode`, and `onChanged`'s
background refetch briefly sets `isLoading`. Gating the whole tree on it unmounts every
`ResourceNode` mid-refetch, closing whatever modal was open before its success message
ever renders — found via manual UI testing 2026-07-31, not caught by the test suite (a
frontend interaction bug, not a logic bug).

## Localization (English / Hebrew)

The UI is switchable EN/HE (`components/LanguageToggle.tsx`, choice kept in
`localStorage`). **The frontend owns every translation; the backend never localizes.**
- Strings live in `frontend/src/i18n/en.ts` (source of truth, flat keys) and `he.ts`
  (`Partial<Messages>` — any key not translated there falls back to the English value).
  Dictionary values are words only; shared decorative symbols (`+ ` prefix, `…` suffix,
  wrapping parentheses) are added in the JSX, not duplicated per language. Components use
  `useLanguage()`'s `t()`/`tPlural()` — never hardcode user-visible text. Enum values
  (roles, resource types) go through `i18n/labels.ts`, never a hand-built key string.
- Hebrew sets `<html dir="rtl">`. Use logical Tailwind utilities (`ms-`/`ps-`/`border-s`/
  `text-start`), never `ml-`/`pl-`/`border-l`/`text-left`. User-provided names (mixed
  Hebrew/English) need bidi isolation: `<bdi>` inside block elements (`dir="auto"` on a
  block flips its alignment to the left), `dir="auto"` on inline spans and `<option>`s,
  and on text inputs only once non-empty (`dir={value ? "auto" : undefined}`) so the
  placeholder keeps the page's alignment.
- Errors: `DomainError` carries a stable `code` + `params` (`domain/errors.py`; each
  subclass has a generic default code), returned as `{detail, code, params}` by
  `api/error_handlers.py`. `detail` stays English for other API callers; the UI renders
  `errors.<code>` via `i18n/describeError.ts`, falling back to a per-status message. A
  new user-facing error needs a specific `code=` at the raise site plus an `errors.*`
  key in both dictionaries.
- Data (resource/user/team names) is never translated — shown as stored.

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

**Self-revocation exception (confirmed with the project owner)**: `revoke()` allows an
actor to drop their OWN grant (`grantee.user_id == actor.id`) unconditionally —
regardless of role-rank or org-chart position — since "remove my own access" isn't
delegation to anyone. Deliberately **not** folded into `can_manage()` itself:
`can_manage()` is shared with `grant()`, and bypassing role-rank there would let a
low-rank grantee self-*escalate*, not just self-revoke — kept as its own explicit
branch in `revoke()` instead. This is what powers the frontend's "Remove access"
button on Map/Layer nodes (see "Resource creation, personal & team workspaces, move"
above). Separately, `delegation_rules.py`'s `grantee_passes_org_chart_check()` also
gained a narrower self-grantee exception (an actor managing their own restriction
whitelist entry, or their own grant, always passes the *org-chart* check specifically
— nobody is their own org-chart manager) — shared by both `can_manage` and
`can_set_restriction` since that helper is meant to exist exactly once; role-rank gates
(Manager+/Admin) still apply unchanged wherever it's called from.

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

A third method, `list_admins()` (`GET /access/admins/{resource_id}`, also ungated),
answers a narrower "who do I ask" question instead of a full explanation: every grantee
that resolves to Admin at the nearest ancestor gating the resource, restriction-aware,
resolved to display names via `UserDirectory`/`TeamRepository`. Built on a new
`AccessResolver.nearest_admins()` that reuses the same nearest-ancestor-wins traversal
`nearest_grants()`/`nearest_restriction()` use (extracted into a shared `_walk_up()`
helper so the "stop at the first `inherits_from_parent=False` node" rule exists exactly
once) — never duplicate this climb. Powers `ResourceInfoPanel.tsx`'s "Owners" section
(see "UI scope" above).

## Scale assumptions

~2,000-3,000 users, 5,000-10,000 maps (each with a handful of layers). List/search
endpoints (`/catalog`, `/external/v1/my-access`) are paginated by design — do not add
an unpaginated "list everything" endpoint, in-memory or Postgres. The mock user fixture
is intentionally small (~30-50 users) for readability; don't assume its size reflects
production scale when reasoning about performance — check against the row counts above
instead.

## Tests and CI

Backend: `pytest --cov=permissions_server` from `backend/`, hermetic/in-memory always
(see "Running the app" above). `backend/pyproject.toml`'s `[tool.coverage]` config
enforces `fail_under = 100` on everything the hermetic suite can reach — `omit`s the
SQLAlchemy repository files, `infrastructure/db/session.py`/`types.py`, and
`infrastructure/repositories/_pagination.py` explicitly, since those only execute
meaningfully against a real Postgres connection the hermetic suite deliberately doesn't
have. Don't chase 100% by weakening that boundary (e.g. flipping conftest's DB-URL
force-unset) — extend the `omit` list with the same reasoning instead. Table-style
coverage (many `Role` × restricted/unrestricted × personal-workspace × system-role
combinations) lives as `pytest.mark.parametrize` cases colocated in the existing
`tests/unit`/`tests/integration` files — extend those, don't fork parallel suites.

**A third, opt-in DB-backed test tier now exists** (`backend/tests/db/`, 2026-08-21) —
the "add a real DB-backed test tier" option this section used to leave open has been
taken. It runs the SQLAlchemy repositories, `infrastructure/db/session.py`/`types.py`,
and `infrastructure/repositories/_pagination.py` against a real Postgres, keyed off
`PERMISSIONS_TEST_DATABASE_URL` (never `PERMISSIONS_DATABASE_URL`, which stays force-
unset for the hermetic tier above). Skipped, not failed, when that variable isn't set,
so the hermetic `pytest --cov=permissions_server` run above is completely unaffected —
still 100% coverage, still zero Postgres dependency. Full details (how to point it at a
scratch database safely, the async-engine-per-test-function gotcha, why it isn't folded
into the `fail_under = 100` gate) live in `DATABASE.md`'s "DB-backed test tier" section
— read that before extending `tests/db/`, not just this summary.

`.gitlab-ci.yml` runs three independent jobs (path-scoped via `rules: changes`, so an
unrelated frontend-only change doesn't re-run backend tests and vice versa):
`backend-tests` (the hermetic `pytest` above, in a fresh `python:3.11` venv),
`db-tests` (`pytest tests/db`, same venv setup, against a `postgres:17.7` GitLab CI
service container — this is the literal `db-migration-smoke`-style job an old coverage
comment referenced before this tier existed), and `frontend-checks`
(`npm ci && npm run lint && npm test && npm run build`, i.e. `oxlint` + Vitest
(`src/**/*.test.ts`, currently the i18n dictionaries/fallback/error translation) +
`tsc -b`-via-`vite build`).
`backend-tests` and `db-tests` both rewrite `adfs-auth`'s dependency line the same way
the Dockerfile does (see "Running the app" above) — CI-only, never touching the
committed `pyproject.toml`.

## Known, deliberate departures from the reference design docs (do not "fix" — ask first)

The reference docs (PDF design doc, Hebrew docx spec, and the `sk-permissions` repo)
describe a **whitelist-only visibility model** ("everything invisible by default,"
siblings hidden unless explicitly granted, restrict/unrestrict cascading). This project
originally kept **universal visibility** instead. **Superseded 2026-10-06** (confirmed with
the project owner): the catalog now shows only what the caller can reach, plus the path
above it — close to the reference docs' model. See "UI scope" above for the exact rule.

**Superseded, as of the `instructions/new-guide-he.txt` pass**: the second half of this
departure — "no restrict/unrestrict mechanism" — is no longer accurate. The user
explicitly confirmed the new whitelist requirement supersedes that part of this
document ("what i wrote is what decide, not claude.md"). A `Restriction`
mechanism now exists (see "Restrictions (whitelist gate)" above) with its own
`RESTRICT`/`UNRESTRICT`/`RESTRICTION_ROLE_CHANGE` audit actions. What did **not**
change at the time: restrictions gated only *access*, not *visibility* — superseded
2026-10-06 along with universal visibility; a non-whitelisted caller now doesn't see
the restricted resource at all.

## Known deferred work (do not silently "fix" — ask first)

- Real ADFS validation (wiring `adfs-auth`'s real `oidc.OidcJwtValidator`/
  `OidcAuthorizationCodeAcquirer` behind the same ports — the library itself is
  wired in now, just still in mock mode), real sync of resources from the
  source-of-truth system (currently `infrastructure/seed_data.py`, static mock data,
  now also the source `scripts/seed.py` loads into Postgres), real org hierarchy
  source (currently the JSON-derived fixture) — likely AD/ADFS groups eventually.
  (Real Postgres repositories are done — see "Deployment context" above.)
- No service-to-service auth mechanism exists yet for the system that owns Map/Layer
  data to call `POST`/`DELETE /resources` directly (create/delete a Map or Layer
  resource here, then presumably notify back). Those endpoints stay open to any
  authenticated caller in the meantime (confirmed with the project owner) — only the
  frontend is restricted from creating/deleting Map/Layer (see "Resource creation,
  personal & team workspaces, move" above). Don't build a service-credential path
  speculatively; ask first when this becomes real.
- No API route to toggle `inherits_from_parent` — resource *creation* now has full API
  coverage (see "Resource creation, personal & team workspaces, move" above:
  `POST /resources`, `GET /resources/my-workspace`, `POST /resources/workspaces`,
  `PATCH /resources/{id}/move`), but flipping `inherits_from_parent` on an existing
  resource is still only reachable via `ResourceRepository.set_inherits_from_parent()`
  directly, not through any endpoint.
- **OPEN DECISION — tie-break rule for grants/restrictions**: currently rank-based
  (highest role wins among multiple grants, or multiple restriction entries, at the
  same nearest-ancestor node) — see `AccessResolver.effective_role()` in
  `application/access_resolver.py`. `instructions/new-guide-he.txt` line 11 says
  conflicts should resolve by "the last one" (recency) instead, which directly
  contradicts this. The user has NOT yet decided which one is correct — do not change
  this behavior (or the regression test `test_restriction_tie_break_is_rank_based_not_recency`
  in `tests/unit/test_access_resolver.py`) until they do. Recency would also require a
  new timestamp field on `PermissionGrant`/`Restriction` (neither has one today) plus a
  migration — it's not a small tweak.

## Agent behavior (inherits workspace-level rules, restated for this project)

- Ambiguous requirement → ask, don't assume (see workspace `~/CLAUDE.md`).
- SOLID and no-duplication (above) are enforced, not optional — new code must depend on
  `domain.ports`, not on concrete `infrastructure` classes, and must not duplicate logic
  across resource types, grantee types, or repository backends.
- Always build and run in DB mode (see "Running the app" above — `cd backend` first so
  `backend/.env`'s `PERMISSIONS_DATABASE_URL` is actually picked up) and manually verify
  the affected flow before reporting a change as done.

## graphify

This project has a knowledge graph at graphify-out/ with god nodes, community structure, and cross-file relationships.

Rules:
- For codebase questions, first run `graphify query "<question>"` when graphify-out/graph.json exists. Use `graphify path "<A>" "<B>"` for relationships and `graphify explain "<concept>"` for focused concepts. These return a scoped subgraph, usually much smaller than GRAPH_REPORT.md or raw grep output.
- If graphify-out/wiki/index.md exists, use it for broad navigation instead of raw source browsing.
- Read graphify-out/GRAPH_REPORT.md only for broad architecture review or when query/path/explain do not surface enough context.
- After modifying code, run `graphify update .` to keep the graph current (AST-only, no API cost).
