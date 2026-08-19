# Migrating to the Closed Network

This project is currently being built on the open network (no real ADFS, no real
resource sync, local Postgres) and will move into a closed network — no internet
access, a different PostgreSQL instance, real ADFS reachable, users on an internal
("closed Chrome network") browser network. This is the durable reference for that
move: what to change and how, what has to be installed/available in the closed
network, and everything the codebase doesn't yet handle that you'll need to decide or
build before this is production-ready there.

Confirmed so far (recorded here so this doesn't drift from what was actually decided):
an **internal package mirror** exists for both Python and Node — you don't need to
vendor wheels/tarballs by hand. The closed-network Postgres is **version 15**. The
frontend keeps running as the **Vite dev server** (`npm run dev`), not a built static
bundle, for now.

This is a planning/reference document, not a work log — update it if any of these
decisions change, and treat every "not built yet" item below the way `CLAUDE.md`
already treats deferred work: don't silently build it, ask first, since several of
these require decisions only the project owner can make (client type, session
storage, etc.).

---

## 1. Database

Full schema reference: **`DATABASE.md`**. Summary of what changes:

- New connection string in `backend/.env` (git-ignored, provisioned independently per
  environment — see "Secrets" below):
  ```
  PERMISSIONS_DATABASE_URL=postgresql+asyncpg://permissions_app:<password>@<closed-network-host>:5432/permissions
  ```
- Postgres **15** target — confirmed compatible: nothing in this schema needs newer
  than what's shipped since well before 13. The one non-default requirement is the
  `ltree` extension (standard `postgresql-contrib`, trusted since PG13 — no superuser
  needed to `CREATE EXTENSION`, just `CREATE` privilege on the database). See
  `DATABASE.md` for exact setup commands.
- Run `alembic upgrade head` then `python scripts/seed.py` against the new instance —
  same as today, just pointed at a different host. Both are idempotent.
- Nothing in `domain/`, `application/`, or the SQLAlchemy repository layer changes —
  the whole point of the ports/adapters split (`CLAUDE.md`'s DIP requirement) is that
  swapping the Postgres host is a config change, not a code change.
- **`backend/tests/conftest.py`** force-unsets `PERMISSIONS_DATABASE_URL` already, so
  the test suite stays hermetic (in-memory) regardless of which network it runs on —
  no change needed there.

## 2. Packages — what has to be available in the closed network

Since an internal mirror exists, point the package managers at it rather than
vendoring files:

- **Python** (`pip`): configure the mirror as the index (`pip.conf` /
  `PIP_INDEX_URL` env var, or a `[tool.uv]`/`--index-url` flag depending on how you
  actually install — this repo uses plain `pip install -e ".[dev]"` today, see
  `README.md`). Everything in `backend/pyproject.toml`'s `dependencies` needs to exist
  on that mirror: `fastapi`, `uvicorn[standard]`, `pydantic`, `pydantic-settings`,
  `pyjwt`, `sqlalchemy[asyncio]`, `asyncpg`, `alembic` — all are common enough that a
  general-purpose internal PyPI mirror almost certainly already has them. Confirm
  **prebuilt wheels** are mirrored, not just source distributions — `asyncpg` in
  particular has C extensions and building from an sdist needs a matching compiler
  toolchain on the target machine, which an air-gapped box may not have.
- **`adfs-auth` — the one dependency that will NOT resolve as-is.** `pyproject.toml`
  currently declares it as
  ```
  adfs-auth @ file:///C:/Users/Eitam/adfs-auth
  ```
  a hardcoded absolute Windows path on *this* machine. That will not exist on the
  closed-network host. **Action needed before the move**: publish `adfs-auth`
  (`C:\Users\Eitam\adfs-auth`) as a proper package to the internal mirror (build a
  wheel — it already has a `[build-system]`/hatchling config — and upload it), then
  change the dependency line to a normal versioned requirement
  (`adfs-auth>=0.1.0`). This is also just better practice generally: a `file://` path
  dependency is fragile even within the open network (breaks the moment the repo or
  the library moves, breaks in any second checkout or CI). I haven't changed
  `pyproject.toml` for this yet since it depends on you actually publishing the
  package somewhere — flagging it here as the top action item.
- **Node** (`npm`): point at the mirror via `.npmrc` (`registry=<mirror-url>`, per-project
  or per-user). `frontend/package.json`'s dependencies (`react`, `react-dom`,
  `react-router-dom`, Vite, Tailwind, TypeScript, oxlint) should all be on a
  general-purpose npm mirror. Before moving, run `npm info vite engines` (or check
  Vite's own docs for whatever version `package.json` pins) to confirm the closed
  network's Node runtime satisfies Vite 8's minimum Node version — don't assume;
  verify against what's actually mirrored.
- **PostgreSQL 15 server itself** — provisioned by whoever manages the closed-network
  infra, not something `pip`/`npm` install; see `DATABASE.md`.

## 3. Auth — the biggest real gap, not just a config swap

This is the part most likely to be underestimated: swapping mock auth for real ADFS
is **not** a drop-in adapter change like the Postgres swap was. The mock login flow
and the real ADFS flow have genuinely different shapes.

### What exists today

- `domain/ports/token_validator.py` / `token_issuer.py` are the two swap-point
  interfaces (already designed for this — see their docstrings).
- `infrastructure/auth/adfs_auth_mock_issuer.py` / `adfs_auth_mock_validator.py` wrap
  the `adfs-auth` library's `testing.MockTokenAcquirer` / `MockTokenValidator`.
- The login flow today: frontend shows a dropdown of mock users
  (`GET /auth/mock-users`) → user picks one → `POST /auth/login {user_id}` →
  backend calls `TokenIssuer.issue(user)`, which mints an HS256 JWT **immediately**,
  no redirect, no external call. `TokenIssuer.issue(user: AuthenticatedUser) -> str`
  assumes the caller already knows who the user is.

### What real ADFS actually requires

`adfs-auth`'s real implementation (`adfs_auth.oidc`) is an OIDC **authorization-code +
PKCE** flow — the opposite shape: you do *not* know who the user is until they've
been redirected to ADFS, logged in there, and been redirected back with a code.
Concretely, from `adfs_auth`'s `domain/ports.py` / `oidc/acquirer.py`:

- `TokenAcquirer.start_login()` → returns a `LoginChallenge(redirect_url, state,
  code_verifier)`. The caller must **persist `state` and `code_verifier`** somewhere
  and send the browser to `redirect_url` (ADFS's authorization endpoint).
- ADFS redirects back to this app's `redirect_uri` with `?code=...&state=...`.
- `TokenAcquirer.complete_login(code, state, expected_state, code_verifier)` exchanges
  the code for tokens (server-to-server call to ADFS's token endpoint) and validates
  the result.

This app has **no session/state-storage mechanism at all today** — it's fully
stateless, JWT-bearer-only. Wiring real ADFS needs somewhere to hold `state` +
`code_verifier` between the redirect-out and redirect-back (a server-side store keyed
by `state`, or a short-lived signed cookie) — a new piece of infrastructure, not
covered by any existing `domain.ports` interface. That's a decision for you to make
(cookie vs. server-side store; this app's session lifetime requirements), not
something to default silently.

Concretely, when you're ready to build this (don't do it silently — this is the kind
of deferred-work item `CLAUDE.md` says to ask about first):

1. **New settings** in `config.py` (a new `Settings` block, separate from the mock
   `jwt_*` fields, which stay only for the mock path):
   `adfs_issuer`, `adfs_audience`, `adfs_client_id`, `adfs_client_secret` (only if
   ADFS is configured as a confidential client — public clients omit it),
   `adfs_redirect_uri`. All currently unset/undecided — get the real values from
   whoever administers the closed network's ADFS server.
2. **Validator swap** (the easy half — same `TokenValidator.validate(token) ->
   AuthenticatedUser` shape as the mock): new
   `infrastructure/auth/adfs_auth_real_validator.py` composing
   `adfs_auth.oidc.HttpOidcMetadataProvider` → `HttpJwksProvider` →
   `OidcJwtValidator`, then resolving `AuthenticatedIdentity.subject` through
   `UserDirectory` exactly like `adfs_auth_mock_validator.py` does now (that part of
   the pattern carries over unchanged). This validates RS256 tokens against ADFS's
   published JWKS — no shared secret on this side at all.
3. **New router endpoints**, since `POST /auth/login {user_id}` doesn't fit a redirect
   flow: something like `GET /auth/login` (redirect to ADFS) and
   `GET /auth/callback?code=&state=` (complete the exchange, then issue this app's own
   session — a cookie, or hand the browser the ADFS `id_token`/`access_token`
   directly, again your call). The mock-only `/auth/mock-users` and the current shape
   of `/auth/login` go away entirely for the real path (they can stay for local dev
   against in-memory storage if you still want a mock-login option outside the closed
   network — that's a product decision, not a technical constraint).
4. **Frontend**: `Login.tsx`'s user-picker dropdown gets replaced with a "Log in"
   button that navigates the browser to the backend's `/auth/login` redirect starter,
   and a callback route that lands after ADFS redirects back.
5. **`jwt_secret`/`jwt_algorithm`/`jwt_issuer`/`jwt_audience`** in `config.py` stop
   being used at all once the real validator is wired in for a given environment —
   they're mock-only. Don't let the insecure default secret linger as if it still
   matters once real ADFS is live; it simply becomes dead config for that adapter.
6. **Clock sync**: JWT validation checks `exp`/`iat`, and `HttpOidcMetadataProvider` /
   `HttpJwksProvider` cache the discovery document / JWKS for 1 hour by default
   (`DEFAULT_METADATA_TTL_SECONDS`/`DEFAULT_JWKS_TTL_SECONDS` in `adfs-auth`). Confirm
   the closed-network host has a working internal NTP source — there's no public NTP
   reachable there, and clock drift breaks token validation silently/intermittently.
7. **Network reachability, both directions**: the *backend* needs to reach ADFS's
   token endpoint and JWKS endpoint (server-to-server, inside the closed network —
   fine). The *browser* needs to reach ADFS's authorization endpoint directly (for the
   redirect) — confirm the "closed Chrome network" the users sit on can actually
   resolve/reach the ADFS host, not just the frontend/backend hosts.

**Recommended order**: do the Postgres move first, verified fully working with mock
auth still in place (same as today, just pointed at the new DB) — that isolates the
"did the storage swap work" question from the "did the auth swap work" question.
Wire real ADFS as a separate, separately-verified step afterward. This mirrors the
Phase 1 / Phase 2-storage / Phase 2-auth structure `PLAN.md` already uses — don't
collapse them into one big-bang cutover.

## 4. CORS and frontend↔backend wiring

- `PERMISSIONS_CORS_ORIGINS` (default `["http://localhost:5173"]` in `config.py`)
  must be updated to wherever the closed-network frontend is actually served from.
  Today, because the Vite dev server proxies `/api/*` to the backend
  (`frontend/vite.config.ts`), the browser only ever talks to one origin and CORS
  isn't actually exercised in normal use — but it *is* exercised the moment anything
  calls the backend directly (e.g. `/external/v1/my-access` from another internal
  app), so don't leave it pointed at `localhost:5173` in the closed network.
- `vite.config.ts`'s dev proxy target is **hardcoded** to `http://127.0.0.1:8000`.
  That's correct only if frontend and backend run on the same host in the closed
  network. If they end up on different hosts, this needs to become an actual target
  (env var or a per-environment config), not stay hardcoded.

## 5. Secrets

`backend/.env` is git-ignored and today holds a real local Postgres password in plain
text (fine for a single-dev open-network box). In the closed network, `.env` can't
just travel via `git pull` (it's excluded on purpose) — decide how it actually gets
onto that host: dropped in manually by whoever provisions the machine, or pulled from
whatever internal secrets tool exists there. Same applies to the future
`adfs_client_secret`, if ADFS ends up configured as a confidential client. This is an
infra/process decision, not something the codebase can default.

## 6. What does *not* change with this move

- **Resource tree and org hierarchy stay mocked** (`infrastructure/seed_data.py`,
  `infrastructure/auth/_mock_users_fixture.py`) — moving networks doesn't touch this;
  it only matters once a real source-of-truth sync and a real AD/ADFS-group-backed org
  hierarchy are wired in, both still open, separate pieces of deferred work (see
  `PLAN.md`'s "Known deferred work").
- **The hexagonal boundaries themselves don't change.** `domain/`/`application/` stay
  untouched by both the DB swap (already proven — see `PLAN.md`'s "Postgres
  persistence (done)") and the auth swap (same guarantee, once built) — that's the
  entire reason this architecture exists. If a closed-network change ever seems to
  require touching `domain/` or `application/`, stop and reconsider; it almost
  certainly means the change is leaking through the wrong layer.
- **Tests stay hermetic** either way — `conftest.py` always forces in-memory repos.

## 7. Verification checklist for the move

1. **Storage cutover**: `alembic upgrade head` against the new PG15 instance →
   confirm `ltree` extension + all 7 tables (`DATABASE.md`) → `python scripts/seed.py`
   → confirm row counts (41 resources / 2 teams / 5 memberships / 1 root grant line
   per top-level Workspace) → boot `uvicorn` from `backend/` → mock-login still works
   → full manual walkthrough from `PLAN.md`'s "Verification" section, same as Phase 2
   storage was originally verified, just against the new host.
2. **Package availability**: fresh `pip install -e ".[dev]"` and `npm install` from
   the internal mirror on a machine with no other network access, confirming nothing
   silently falls back to a cached/global package from the open-network box.
3. **`adfs-auth` published and installable** by version from the mirror, not by
   `file://` path.
4. **Auth cutover** (separate step, once ADFS wiring is built): repeat the full
   manual walkthrough with real ADFS, confirm token validation against real JWKS,
   confirm clock-sync-dependent expiry works as expected, confirm the browser-side
   redirect actually reaches ADFS from the closed Chrome network.
