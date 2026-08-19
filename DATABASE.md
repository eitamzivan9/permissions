# Database Reference — Permissions Server

Everything you need to stand up, seed, and understand the Postgres schema this
project uses. Applies both to the current open-network dev database and to the
closed-network target — see `CLOSED_NETWORK_MIGRATION.md` for what actually changes
between the two.

There is deliberately **no `users` table** anywhere in this schema — identity is
always resolved externally (mocked today via `infrastructure/auth/_mock_users_fixture.py`,
real ADFS/AD later). Every `user_id` column here is a free-text string that must match
an id the identity source recognizes; nothing in Postgres enforces that.

## Requirements

- **PostgreSQL 15** (confirmed as the closed-network target). Local dev has been run
  against PostgreSQL 18, and nothing in this schema uses anything newer than what's
  been in Postgres since well before 13, so 15 is fine — the one non-default piece is
  the **`ltree`** extension (ships in the standard `postgresql-contrib` package on
  every mainstream distribution/installer; nothing to compile).
- `ltree` has been a **trusted extension** since Postgres 13, meaning a non-superuser
  role with `CREATE` privilege on the target schema can install it itself — you do
  **not** need superuser/DBA involvement for `CREATE EXTENSION ltree` specifically,
  only for creating the database/role in the first place.

## Starting the database (one-time setup)

1. Create the database and an application role (run as a superuser, e.g. `psql -U postgres`):

   ```sql
   CREATE DATABASE permissions;
   CREATE ROLE permissions_app WITH LOGIN PASSWORD 'change-me';
   GRANT ALL PRIVILEGES ON DATABASE permissions TO permissions_app;
   \c permissions
   GRANT ALL ON SCHEMA public TO permissions_app;
   ```

   If your closed-network Postgres policy blocks even trusted-extension self-install,
   ask a DBA to run `CREATE EXTENSION IF NOT EXISTS ltree;` once against the `permissions`
   database before continuing — the app's own migration (below) also issues this
   statement and is idempotent either way.

2. Point the app at it — set in `backend/.env` (git-ignored):

   ```
   PERMISSIONS_DATABASE_URL=postgresql+asyncpg://permissions_app:change-me@HOST:5432/permissions
   ```

   Must be an `asyncpg`-style URL (`postgresql+asyncpg://…`), not plain `postgresql://` —
   `infrastructure/db/session.py` builds an async SQLAlchemy engine. `asyncpg` is a pure
   Python driver (no `libpq`/native build toolchain needed), which matters for an
   offline install — see `CLOSED_NETWORK_MIGRATION.md`.

3. Apply migrations (creates all 6 tables below plus the `ltree` extension):

   ```bash
   cd backend
   alembic upgrade head
   ```

4. Seed the mock resource tree / teams / bootstrap grant (idempotent — safe to re-run):

   ```bash
   python scripts/seed.py
   ```

   Expected output on a fresh database: `resources: 41 checked`, `teams: 2 checked`,
   `team memberships: 5 inserted`, and one `root bootstrap grants` line per top-level
   Workspace in `infrastructure/seed_data.py` (currently 1). If these counts don't
   match, something about the target database wasn't actually empty — check before
   assuming the seed script is broken.

5. Run the app (from inside `backend/`, so `backend/.env` is actually picked up —
   `Settings.env_file` resolves relative to the process's working directory, not this
   file's location):

   ```bash
   uvicorn permissions_server.main:app --reload
   ```

To start over completely: `alembic downgrade base` then `alembic upgrade head`, or just
drop and recreate the database (step 1) and re-run migrations + seed.

## Schema

Source of truth: `backend/src/permissions_server/infrastructure/db/models.py` (ORM) and
`backend/alembic/versions/0001_initial_schema.py` + `0002_owner_restrictions.py`
(migrations — 0002 added `resources.owner_id` and the whole `restrictions` table).
Every enum column (`type`, `role`, `grantee_type`, `action`, `system_roles.role`) is
stored as `VARCHAR`, not a native Postgres `ENUM` type — deliberate, so adding a new
value later is a one-line Python change, not an `ALTER TYPE` migration.

Alembic also auto-creates a 7th table, **`alembic_version`** — one row holding the
current migration revision id. Bookkeeping only, not part of the application schema,
never queried by app code.

### `resources`

The mirrored resource tree (Workspace/Folder/Map/Group/Layer) — id/name/type/parent
only, never the real feature data those types represent elsewhere.

| Column | Type | Constraints | Notes |
|---|---|---|---|
| `id` | `VARCHAR` | **PK** | uuid4 hex for app-created resources; fixed slugs (e.g. `ws-city`) for seed data |
| `type` | `VARCHAR` | NOT NULL | `WORKSPACE` \| `FOLDER` \| `MAP` \| `GROUP` \| `LAYER` |
| `name` | `VARCHAR` | NOT NULL | |
| `parent_id` | `VARCHAR` | FK → `resources.id`, NULLABLE | NULL only for Workspaces (the only valid tree root) |
| `inherits_from_parent` | `BOOLEAN` | NOT NULL, default `true` | `false` cuts `AccessResolver`'s ancestor climb short at this node |
| `path` | `LTREE` | NOT NULL | dot-separated chain of sanitized ancestor ids (hyphens → underscores, `ltree` labels disallow them); computed once in Python at `create()` time, not a DB trigger — powers `path_to_root()` as one indexed containment query instead of an O(depth) `parent_id` walk |
| `owner_id` | `VARCHAR` | NULLABLE | set only on a personal workspace (one per user, lazily created); NULL for every other resource including team workspaces |

Indexes: `ix_resources_parent_id` (btree on `parent_id`), `ix_resources_path` (**GiST**
on `path` — required for `ltree` ancestor/descendant queries to be indexed at all),
`ix_resources_owner_id` (btree on `owner_id`, added in `0002`).

### `teams`

| Column | Type | Constraints |
|---|---|---|
| `id` | `VARCHAR` | **PK** |
| `name` | `VARCHAR` | NOT NULL |

### `team_memberships`

Many-to-many join table, no surrogate id.

| Column | Type | Constraints |
|---|---|---|
| `team_id` | `VARCHAR` | **PK (composite)**, FK → `teams.id` |
| `user_id` | `VARCHAR` | **PK (composite)** — free-text, not a FK (no `users` table) |

### `permission_grants`

One row = one role granted to one grantee (user or team) at one resource. The
*additive* mechanism — see `restrictions` below for the opposite-meaning whitelist.

| Column | Type | Constraints | Notes |
|---|---|---|---|
| `id` | `VARCHAR` | **PK** | default `uuid4().hex` |
| `grantee_type` | `VARCHAR` | NOT NULL | `USER` \| `TEAM` |
| `user_id` | `VARCHAR` | NULLABLE | set iff `grantee_type = USER` |
| `team_id` | `VARCHAR` | FK → `teams.id`, NULLABLE | set iff `grantee_type = TEAM` |
| `resource_id` | `VARCHAR` | FK → `resources.id`, NOT NULL | |
| `role` | `VARCHAR` | NOT NULL | `VIEWER` \| `EDITOR` \| `MANAGER` \| `ADMIN` |
| `granted_by` | `VARCHAR` | NOT NULL | actor id who made/last changed the grant |
| `grantee_key` | `VARCHAR` | NOT NULL | see below |

`grantee_key` exists because a plain `UNIQUE(grantee_type, user_id, team_id, resource_id)`
does **not** work — standard SQL treats two rows sharing a NULL column as non-duplicate,
so two different `USER` grants (both with `team_id = NULL`) wouldn't collide on that
column alone. `grantee_key` (computed in `infrastructure/repositories/sqlalchemy_grant_repository.py::grantee_key()`)
encodes the grantee as one always-non-null string, mirroring the in-memory repo's
`(Grantee, resource_id)` dict key exactly. The actual uniqueness constraint is
`UNIQUE(grantee_key, resource_id)` (`uq_grant_grantee_resource`).

Index: `ix_permission_grants_resource_id`.

### `restrictions`

Same column shape as `permission_grants`, added by migration `0002`, but the opposite
meaning: the mere existence of a row here gates the resource to an exclusive
whitelist — see `CLAUDE.md`'s "Restrictions (whitelist gate)" for the resolution
semantics. Same `grantee_key` technique, same reason.

| Column | Type | Constraints |
|---|---|---|
| `id` | `VARCHAR` | **PK**, default `uuid4().hex` |
| `grantee_type` | `VARCHAR` | NOT NULL |
| `user_id` | `VARCHAR` | NULLABLE |
| `team_id` | `VARCHAR` | FK → `teams.id`, NULLABLE |
| `resource_id` | `VARCHAR` | FK → `resources.id`, NOT NULL |
| `role` | `VARCHAR` | NOT NULL |
| `granted_by` | `VARCHAR` | NOT NULL |
| `grantee_key` | `VARCHAR` | NOT NULL |

Unique: `UNIQUE(grantee_key, resource_id)` (`uq_restriction_grantee_resource`).
Index: `ix_restrictions_resource_id`.

### `system_roles`

Resource-independent, global roles (`SUPER_EDITOR` acts as Admin everywhere,
`SUPER_VIEWER` as Viewer everywhere — see `CLAUDE.md`).

| Column | Type | Constraints |
|---|---|---|
| `user_id` | `VARCHAR` | **PK (composite)** |
| `role` | `VARCHAR` | **PK (composite)** — `SUPER_EDITOR` \| `SUPER_VIEWER` |

Composite PK means a given user can hold both system roles simultaneously (each is its
own row) but can't hold the same one twice.

### `audit_log`

Append-only — `AuditLogRepository` (both in-memory and SQLAlchemy implementations)
exposes no update/delete method by design; nothing in the app ever mutates or removes
a row here.

| Column | Type | Constraints | Notes |
|---|---|---|---|
| `id` | `VARCHAR` | **PK** | |
| `actor_id` | `VARCHAR` | NOT NULL | who performed the action |
| `grantee_type` | `VARCHAR` | NOT NULL | |
| `user_id` | `VARCHAR` | NULLABLE | |
| `team_id` | `VARCHAR` | NULLABLE | **not** a FK here (unlike `permission_grants`/`restrictions`) — a historical record must survive the referenced team or resource being deleted later |
| `resource_id` | `VARCHAR` | NOT NULL | **not** a FK, same reason |
| `role` | `VARCHAR` | NOT NULL | |
| `action` | `VARCHAR` | NOT NULL | `GRANT` \| `ROLE_CHANGE` \| `REVOKE` \| `RESTRICT` \| `UNRESTRICT` \| `RESTRICTION_ROLE_CHANGE` |
| `timestamp` | `TIMESTAMPTZ` | NOT NULL | |

Indexes: `ix_audit_log_resource_id`, `ix_audit_log_actor_id`.

## Entity-relationship summary

```
resources (self-referencing tree via parent_id, ltree path)
   ├─< permission_grants.resource_id
   ├─< restrictions.resource_id
   └─  (owner_id — no FK, just a free-text user id)

teams
   ├─< team_memberships.team_id
   ├─< permission_grants.team_id  (nullable — set only for TEAM grantees)
   └─< restrictions.team_id       (nullable — set only for TEAM grantees)

system_roles   — standalone, keyed by (user_id, role)
audit_log      — standalone, intentionally not FK-linked (survives deletes)
```

No table stores users — `user_id`/`actor_id`/`owner_id`/`granted_by` columns are
free-text, validated only against whatever `UserDirectory` implementation is wired in
(mock fixture today).

## Migrations

Two revisions exist today, always applied together in order:

| Revision | Adds |
|---|---|
| `0001_initial_schema` | `CREATE EXTENSION ltree` + all 6 tables + `ix_resources_path` GiST index |
| `0002_owner_restrictions` | `resources.owner_id` + `ix_resources_owner_id`, and the whole `restrictions` table |

`alembic upgrade head` applies whatever hasn't been applied yet — safe to run against
an already-current database (no-op). When you add new tables/columns, write a new
migration under `backend/alembic/versions/`; never hand-edit `0001`/`0002` after
they've been applied anywhere.

## Verifying the connection independent of the app

```bash
psql "postgresql://permissions_app:change-me@HOST:5432/permissions" -c "\dt"
```

should list all 7 tables (6 above + `alembic_version`). To sanity-check `ltree`
specifically:

```sql
SELECT extname, extversion FROM pg_extension WHERE extname = 'ltree';
```
