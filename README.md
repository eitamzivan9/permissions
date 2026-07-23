# Permissions Server

Permissions / access-control server for the geography team's resource tree
(**Workspace → Folder → Map → Group → Layer**). It owns *permissions only* — never
resource feature data, never a users table. Two responsibilities:

1. A web UI listing every resource in the system, annotated with the logged-in user's
   own effective role, letting Managers/Admins grant or change access for people below
   them in the org (or for Teams).
2. `/external/v1/my-access` — an API other internal apps call (forwarding the
   end-user's ADFS JWT) to find out which maps a user can reach.

See [`PLAN.md`](PLAN.md) for the full architecture, data model, and API reference, and
[`CLAUDE.md`](CLAUDE.md) for the durable design rules (SOLID, hexagonal boundaries,
permission model, delegation rule) that must not silently drift.

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
  path dependency — see `backend/pyproject.toml`)
- PostgreSQL 18 (only if running in Phase 2 / Postgres-backed mode — not required for
  everyday dev)

## Quick start (Phase 1 — in-memory, no DB setup)

### Backend

```bash
cd backend
python -m venv .venv
source .venv/Scripts/activate   # Git Bash on Windows
pip install -e ".[dev]"
uvicorn permissions_server.main:app --reload
```

Runs at `http://localhost:8000` with `PERMISSIONS_DATABASE_URL` unset, so it uses
in-memory repositories — nothing to configure.

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

## Running with PostgreSQL (Phase 2 storage)

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

## Tests

```bash
cd backend
pytest
```

`backend/tests/conftest.py` force-unsets `PERMISSIONS_DATABASE_URL`, so the suite
always runs hermetically against in-memory repositories regardless of what
`backend/.env` sets for normal runs.

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
├── CLAUDE.md      # durable architecture/design rules — read first
├── PLAN.md        # full implementation plan, data model, API reference
├── backend/       # FastAPI app (domain / application / infrastructure / api)
└── frontend/      # React + TS + Tailwind SPA
```

Backend follows hexagonal architecture: `domain/` (entities + ports, no framework
imports) → `application/` (use-case services) → `infrastructure/` (in-memory or
SQLAlchemy repos, mock auth) → `api/` (FastAPI routers + DI wiring). See `PLAN.md` for
the full file guide.

## Known limitations (deliberate, tracked in `PLAN.md`/`CLAUDE.md`)

- Real ADFS validation is not wired in yet — auth is mocked.
- Resource tree is static mock data (`infrastructure/seed_data.py`), not synced from a
  real source-of-truth system.
- Org hierarchy is a small JSON-derived fixture, not a real AD/ADFS source.
- No resource-admin API (create resources, toggle `inherits_from_parent`) exists yet.
