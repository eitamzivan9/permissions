# Permissions Server

Permissions / access-control server for the geography team's resource tree
(**Workspace → Folder → Map → Group → Layer**). It owns *permissions only* — never
resource feature data, never a users table. Two responsibilities:

1. A web UI listing every resource in the system, annotated with the logged-in user's
   own effective role, letting Managers/Admins grant or change access for people below
   them in the org (or for Teams).
2. `/external/v1/my-access` — an API other internal apps call (forwarding the
   end-user's ADFS JWT) to find out which maps a user can reach.

See [`docs/PLAN.md`](docs/PLAN.md) for the full architecture, data model, and API
reference, and [`CLAUDE.md`](CLAUDE.md) for the durable design rules (SOLID, hexagonal
boundaries, permission model, delegation rule) that must not silently drift. See
[`docs/DATABASE.md`](docs/DATABASE.md) for the full Postgres schema reference (tables,
columns, keys, how to start the DB, the DB-backed test tier), and
[`docs/migration/`](docs/migration/) for what changes when this moves from the open
network it's being built on to the organization's closed network — split into
[`CLOSED_NETWORK_MIGRATION.md`](docs/migration/CLOSED_NETWORK_MIGRATION.md) (different
Postgres, real ADFS, offline package sourcing) and
[`OPENSHIFT_MIGRATION.md`](docs/migration/OPENSHIFT_MIGRATION.md) (deploying and running
the app on OpenShift within that closed network).

## Stack

- **Backend**: Python + FastAPI. Storage is pluggable via `PERMISSIONS_DATABASE_URL`:
  unset → in-memory repositories (no setup needed), set → PostgreSQL via SQLAlchemy
  (async) + Alembic.
- **Frontend**: React + TypeScript (Vite) + Tailwind, calling the backend as a JSON
  API.
- **Auth**: ADFS-issued JWT in production; currently mocked via the `adfs-auth`
  library (installed as a local path dependency from `C:\Users\Eitam\adfs-auth`).

## Prerequisites

- Python 3.11+
- Node.js (for the Vite frontend)
- The `adfs-auth` library checked out at `C:\Users\Eitam\adfs-auth` (installed as a
  path dependency — see `backend/pyproject.toml`; this is a local-path dependency that
  will need to be published to a real package index before this project can run
  anywhere other than this machine — see `CLOSED_NETWORK_MIGRATION.md`)
- PostgreSQL — local dev here runs PostgreSQL 18, but the schema targets nothing newer
  than PostgreSQL 15 (the closed-network deployment target — see `DATABASE.md`), so
  either works; required for everyday dev, this project always runs in DB mode, not
  in-memory

## Quick start (always DB/Postgres mode)

Always run against Postgres, not in-memory — `backend/.env` already sets
`PERMISSIONS_DATABASE_URL` for this. `Settings.env_file` is resolved relative to the
process's **current working directory**, not the file's location, so the backend must
be started from inside `backend/` or it silently misses `backend/.env` and falls back
to in-memory mode. Two terminals, one line each, from the repo root (`Premissions/`):

```bash
# Terminal 1 — backend, DB mode (http://localhost:8000) — Git Bash
cd backend && .venv/Scripts/python.exe -m uvicorn permissions_server.main:app --reload

# Terminal 2 — frontend (http://localhost:5173)
npm --prefix frontend run dev
```

PowerShell doesn't support `&&` as a statement separator — use `;` instead:

```powershell
# Terminal 1 — backend, DB mode (http://localhost:8000) — PowerShell
cd backend; .venv/Scripts/python.exe -m uvicorn permissions_server.main:app --reload

# Terminal 2 — frontend (http://localhost:5173)
npm --prefix frontend run dev
```

Then open `http://localhost:5173` and mock-login as a user. See "Running with
PostgreSQL" below for one-time setup (`alembic upgrade head`, `scripts/seed.py`) if you
haven't already applied migrations and seeded data.

### Backend

First-time setup:

```bash
cd backend
python -m venv .venv
source .venv/Scripts/activate   # Git Bash on Windows
pip install -e ".[dev]"
```

Set `PERMISSIONS_DATABASE_URL` in `backend/.env` (see "Running with PostgreSQL" below),
apply migrations, and seed data — then run it:

```bash
alembic upgrade head
python scripts/seed.py
uvicorn permissions_server.main:app --reload
```

Runs at `http://localhost:8000` using Postgres via SQLAlchemy — always start this from
inside `backend/` (not the repo root), since `PERMISSIONS_DATABASE_URL` is read from
`backend/.env`, resolved relative to the current working directory.

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Runs at `http://localhost:5173` (the backend's default CORS origin).

### Try it

Open `http://localhost:5173`, mock-login as a user, and browse the catalog. The one
user with no manager (`u001`) is bootstrapped with Admin on every top-level Workspace
so there's someone able to grant access from a cold start.

## Running with PostgreSQL (one-time setup)

1. Create a local database and set `PERMISSIONS_DATABASE_URL` in `backend/.env`
   (git-ignored), e.g.:
   ```
   PERMISSIONS_DATABASE_URL=postgresql+asyncpg://user:pass@localhost/permissions
   ```
2. Apply migrations:
   ```bash
   cd backend
   alembic upgrade head
   ```
3. Seed mock resource/team data (idempotent):
   ```bash
   python scripts/seed.py
   ```
4. Run `uvicorn` as above — it now uses the SQLAlchemy repositories instead of
   in-memory ones.

## Running with Docker

`docker compose up` at the repo root starts Postgres, the backend, and the frontend
together — no local Python/Node/Postgres setup needed. See `docker-compose.yml`,
`backend/Dockerfile`, `frontend/Dockerfile`. `backend/.env` is untouched by this path
(compose overrides `PERMISSIONS_DATABASE_URL` to reach the `db` service by name), so
switching between the two-terminal workflow above and Docker doesn't require any config
changes. Migrations and seeding run automatically on container start
(`backend/docker-entrypoint.sh`), same idempotent commands as the manual setup.

## Tests

```bash
cd backend
pytest --cov=permissions_server
```

`backend/tests/conftest.py` force-unsets `PERMISSIONS_DATABASE_URL`, so the suite
always runs hermetically against in-memory repositories regardless of what
`backend/.env` sets for normal runs. `backend/pyproject.toml` enforces 100% coverage
(`fail_under = 100`) on everything that suite can reach — a documented `omit` list
excludes the SQLAlchemy repository files and a couple of other DB-execution-only
modules, since those need a real Postgres connection the hermetic suite deliberately
doesn't have.

A third, opt-in tier, `backend/tests/db/`, covers exactly those omitted files against a
real Postgres — keyed off `PERMISSIONS_TEST_DATABASE_URL`, skipped (not failed) when
that's unset, so it never affects the command above. See `DATABASE.md`'s "DB-backed
test tier" section for how to run it (never point it at your real dev database — it
truncates every app table between tests).

## CI

`.gitlab-ci.yml` runs three independent, path-scoped jobs: `backend-tests` (the
hermetic `pytest` above), `db-tests` (`pytest tests/db` against a `postgres:17.7`
service container), and `frontend-checks` (`npm ci && npm run lint && npm run build`).
`backend-tests` and `db-tests` both rewrite `backend/pyproject.toml`'s local-path
`adfs-auth` dependency to its GitLab remote at CI time only (never touching the
committed file) — see `CLOSED_NETWORK_MIGRATION.md` for why that dependency needs
special handling off this machine.

## Configuration

Backend settings (`backend/src/permissions_server/config.py`), all under the
`PERMISSIONS_` env prefix, loaded from `backend/.env`:

| Variable | Default | Purpose |
|---|---|---|
| `PERMISSIONS_DATABASE_URL` | unset | unset = in-memory repos; set = Postgres via SQLAlchemy |
| `PERMISSIONS_JWT_SECRET` | dev-only insecure default | HS256 signing secret for mock JWTs |
| `PERMISSIONS_JWT_ALGORITHM` | `HS256` | JWT signing algorithm |
| `PERMISSIONS_JWT_EXPIRE_MINUTES` | `480` | mock token lifetime |
| `PERMISSIONS_JWT_ISSUER` | `premissions-mock-adfs` | mock token issuer claim |
| `PERMISSIONS_JWT_AUDIENCE` | `permissions-server` | mock token audience claim |
| `PERMISSIONS_CORS_ORIGINS` | `["http://localhost:5173"]` | allowed frontend origins |

## Project layout

```
Premissions/
├── CLAUDE.md           # durable architecture/design rules — read first
├── docs/
│   ├── PLAN.md                    # full implementation plan, data model, API reference
│   ├── DATABASE.md                # Postgres schema reference + DB-backed test tier
│   ├── CI_CD_SETUP.md             # one-time manual GitLab CI setup step
│   └── migration/
│       ├── CLOSED_NETWORK_MIGRATION.md  # what changes moving to the closed network
│       └── OPENSHIFT_MIGRATION.md       # deploying/running the app on OpenShift there
├── docker-compose.yml  # Postgres + backend + frontend, containerized
├── .gitlab-ci.yml      # backend-tests + db-tests + frontend-checks CI jobs
├── backend/            # FastAPI app (domain / application / infrastructure / api)
└── frontend/           # React + TS + Tailwind SPA
```

`CLAUDE.md` and this `README.md` stay at the repo root deliberately, not in `docs/`:
`CLAUDE.md` is auto-loaded by Claude Code specifically from the project root, and
`README.md` is what GitHub/GitLab render automatically on the repo's landing page —
moving either would break that.

Backend follows hexagonal architecture: `domain/` (entities + ports, no framework
imports) → `application/` (use-case services) → `infrastructure/` (in-memory or
SQLAlchemy repos, mock auth) → `api/` (FastAPI routers + DI wiring). See `PLAN.md` for
the full file guide.

## Known limitations (deliberate, tracked in `PLAN.md`/`CLAUDE.md`)

- Real ADFS validation is not wired in yet — auth is mocked. This is a bigger swap
  than it looks: the mock login flow (pick a user, get a token immediately) and real
  ADFS's redirect-based OIDC flow have different shapes, not just different adapter
  classes — see `CLOSED_NETWORK_MIGRATION.md` section 3 before starting this.
- Resource tree is static mock data (`infrastructure/seed_data.py`), not synced from a
  real source-of-truth system.
- Org hierarchy is a small JSON-derived fixture, not a real AD/ADFS source.
- Resource creation (personal workspaces, team workspaces, child resources, move) has
  full API + frontend coverage; toggling `inherits_from_parent` on an existing resource
  still has no API route.
- A `Restriction`/whitelist mechanism exists to gate access at Admin's discretion (see
  `CLAUDE.md`'s "Restrictions (whitelist gate)"); both `SUPER_EDITOR` and
  `SUPER_VIEWER` bypass it. The first restriction on a resource auto-whitelists the
  acting admin, and removing the last `Admin`-role entry while the resource would stay
  gated is blocked, to avoid orphaning access.
- The frontend only lets you create/delete Folder resources (real, empty-only deletes —
  a non-empty one shows a disabled note instead of a failing button). Group creation is
  backend-only by deliberate choice; Map/Layer are never created or deleted from the UI
  at all — this server doesn't own that data — the UI instead offers "Remove access"
  there, which revokes only your own grant. No service-to-service auth exists yet for
  the system that owns that data to call the (still-open) `POST`/`DELETE /resources`
  endpoints directly.
- Moving a resource is drag-and-drop only (no picker modal). Every per-resource action
  (Create, Manage access, Restrictions, Delete/Remove access, plus an "Owners" lookup
  when you have no access) lives behind one "i" info button per row instead of a row of
  buttons.
