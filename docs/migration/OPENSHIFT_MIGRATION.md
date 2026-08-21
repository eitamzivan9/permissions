# Deploying to OpenShift (Closed Network)

**Status: planning only — nothing in this document is built yet.** This is a reference
for the eventual move to running this app on OpenShift inside the organization's closed
network. Like `CLOSED_NETWORK_MIGRATION.md`, treat every "not built yet" item below the
way `CLAUDE.md` already treats deferred work: don't silently build it, ask first — several
of these are decisions only the project owner can make (build strategy, manifest format,
who provisions Secrets, etc.).

**How this document relates to `CLOSED_NETWORK_MIGRATION.md`**: that document covers what
changes about the app's *dependencies* when it moves networks — a different Postgres, real
ADFS, offline package sourcing. This document covers a separate concern layered on top:
*how the app actually gets deployed and run*, once OpenShift is the thing running it
instead of `docker compose` on a dev machine. Read `CLOSED_NETWORK_MIGRATION.md` first —
several sections below assume that work is done, and duplicate nothing from it (each
section links back to the relevant part instead).

---

## 0. What OpenShift actually is, briefly

Kubernetes runs containers across a *cluster* of machines instead of one — you hand it
container images, and it decides which machine each runs on, restarts them if they crash,
runs multiple copies for reliability/load, and routes traffic to whichever copies are
healthy. OpenShift is Red Hat's platform built on top of Kubernetes, adding a web console,
its own build system, an internal container registry, and — the part that matters most
here — a much stricter default security posture, which is exactly why it's common in
government/enterprise "closed network" environments: it's designed to run fully
air-gapped, with tight control over what a container is allowed to do.

The practical consequence: `docker-compose.yml` (one file, one machine) doesn't port
directly to OpenShift. OpenShift wants a *set* of separate resource objects instead — a
`Deployment` (how many copies of a container to run), a `Service` (internal networking —
OpenShift's equivalent of the automatic `db`/`backend` hostnames Compose gives you for
free), a `Route` (external access — OpenShift's equivalent of Compose's `ports:`), and
`Secret`/`ConfigMap` (replacing `.env` files and `environment:` blocks). **None of these
exist in this repo yet.**

---

## 1. Container image changes needed

- **Run as non-root.** Neither `backend/Dockerfile` nor `frontend/Dockerfile` has a
  `USER` instruction today, so both run as root under plain Docker. OpenShift's default
  security policy (a Security Context Constraint) specifically forbids this — it assigns
  each pod an arbitrary, unpredictable non-root UID unless the image is built to tolerate
  it (writable directories owned by group `0` with group-writable permissions, no
  hardcoded UID/path assumptions). This is the single most common "worked in Docker,
  breaks immediately in OpenShift" surprise. Both Dockerfiles need this addressed before
  either image will run there at all.
- **Frontend needs a real production build, not the dev server.** Today the frontend
  container's entire job is `npm run dev` — Vite's *development* server, meant for local
  editing with hot-reload, not for production traffic.
  `CLOSED_NETWORK_MIGRATION.md` already flags this as a known "not yet." A production
  image would run `vite build` once to produce static files, then serve them with
  something lightweight (nginx is the usual choice) — a different, smaller image than
  what exists today. This also removes Vite's own dev-server `/api` proxy (see
  "Networking, CORS, and Routes" below for what replaces it).
- **Backend shouldn't run with `--reload` in production.** `docker-entrypoint.sh`'s
  final line passes `--reload` to uvicorn unconditionally — a dev convenience (auto-restart
  on file change) with no place in a deployed image. Needs to become conditional (an env
  var / build arg) or simply dropped for whatever image ships to OpenShift.
- **Migrations must come out of the container's automatic entrypoint.** Locally, one
  backend container starts and `docker-entrypoint.sh` runs `alembic upgrade head` once.
  The moment this runs as multiple OpenShift replicas — the entire point of a cluster is
  redundancy — every replica would race to run migrations against the database
  simultaneously on startup. The standard fix is a separate one-shot Job that runs
  migrations *before* the app Deployment rolls out, not baked into every replica's
  startup. Nothing like that exists yet.
- **Where do built images actually come from?** This is an open decision, not yet made:
  does OpenShift build the image itself from source (its Source-to-Image / BuildConfig
  mechanism — which would then need to reach the same internal package mirror
  `CLOSED_NETWORK_MIGRATION.md` section 2 describes), or does something else (an external
  CI pipeline) build the image and simply push the finished result into OpenShift's
  internal registry? Both are normal patterns; nobody has decided which one this project
  uses.

## 2. Health checks

No `/health` or `/ready` endpoint exists anywhere in the backend today —
`docker-compose.yml`'s `healthcheck:` only exists for the `db` service (via Postgres's
own `pg_isready`); the backend and frontend have no equivalent. OpenShift/Kubernetes rely
on `readinessProbe` (should traffic be routed to this pod yet?) and `livenessProbe` (is
this pod healthy, or should it be restarted?) — both need something to poll. A minimal
`/health` endpoint (no auth required, cheap to compute — e.g. confirming the DB connection
pool is reachable) needs to be added before meaningful probes can be configured.

## 3. OpenShift resource objects needed (none exist yet)

At minimum: a `Deployment` and `Service` each for backend and frontend, a `Route` for
external access, `Secret`s for the database connection string (and, later, any ADFS
client secret), and the migration `Job` from section 1. A `PersistentVolumeClaim` is
**not** expected to be needed for this app specifically — see "Database" below, this
server doesn't deploy its own Postgres in this environment.

**Open decision, not yet made**: raw YAML manifests, a Helm chart, or Kustomize overlays?
All three are normal choices with real tradeoffs (Helm/Kustomize pay off more once
there's a dev/staging/prod split to manage); don't default to one silently.

## 4. Database

No new concept here — this is `CLOSED_NETWORK_MIGRATION.md` section 1, restated in this
context: the real closed-network Postgres instance is what the backend connects to (via
`PERMISSIONS_DATABASE_URL`, delivered as a `Secret` — see "Secrets" below), and it isn't
something this app deploys or manages. `docker-compose.yml`'s `db` service (a
Postgres *container*) is a local-dev convenience only and has no equivalent in the
OpenShift deployment at all.

## 5. Packages and build-time dependencies

Also no new concept — `CLOSED_NETWORK_MIGRATION.md` section 2 (the internal pip/npm
mirror, and `adfs-auth` needing to be published there before the `file://` path
dependency can go away) applies exactly as written. The one OpenShift-specific wrinkle:
whichever build strategy gets chosen in section 1 above (OpenShift building the image
itself vs. an external pipeline) determines *what* needs network access to that mirror —
an OpenShift BuildConfig would need to reach it directly from inside the cluster; an
external CI pipeline would need to reach it from wherever that pipeline runs instead.
Settle the build-strategy question first; this follows from it.

## 6. Auth / ADFS

The real gap here is exactly what `CLOSED_NETWORK_MIGRATION.md` section 3 already
describes in full — nothing about *that* gap is OpenShift-specific, so it isn't repeated
here. One thing OpenShift *does* add on top of it: if the eventual real-ADFS OIDC flow
uses a server-side store for `state`/`code_verifier` between the redirect-out and
redirect-back (one of the two options that document leaves open, the other being a
signed cookie), that store must be shared across replicas once the backend runs as more
than one pod — an in-process dict would only work by accident, since a user's redirect
could come back to a *different* replica than the one that started their login. This
doesn't change which option to pick (still an open decision per that document), but it
does rule out "just keep it in memory" the moment there's more than one replica.

## 7. Networking, CORS, and Routes

`CLOSED_NETWORK_MIGRATION.md` section 4 already flags that `PERMISSIONS_CORS_ORIGINS`
and `vite.config.ts`'s hardcoded dev-proxy target both assume `localhost`. Under
OpenShift, "wherever the frontend/backend end up running" becomes concretely "whatever
hostname the Route assigns" — still not decided, but now with a real mechanism attached
to it. This also reopens a question implicitly answered by the dev-server today: once the
frontend is a static build behind nginx (section 1) rather than the Vite dev server, does
`/api/*` still get proxied server-side (nginx forwarding to the backend Service, keeping
the browser talking to one origin, no CORS actually exercised) — or does the frontend call
an absolute backend URL directly, which *does* need CORS configured for real? Either is
workable; this is an open decision, not something to default silently.

## 8. Secrets

Same underlying question `CLOSED_NETWORK_MIGRATION.md` section 5 already leaves open —
"`backend/.env` can't just travel via `git pull`; decide how config actually gets onto the
target host" — OpenShift's specific answer to that question is `Secret` objects (mounted
into the pod as environment variables or files). What's still undecided: *who* creates and
manages those Secrets — a person running `oc create secret` by hand, a GitOps pipeline, or
an integration with whatever secrets-management tool the closed network already has. Same
applies to a future `adfs_client_secret` if ADFS ends up configured as a confidential
client.

## 9. Scaling considerations

The good news: this app's architecture is well-suited to running as multiple replicas once
the items above are addressed. Auth is stateless JWT-bearer today (no server-side session
state to desynchronize across replicas), and the hexagonal `domain`/`application` split
means none of that code needs to change for any of this. The concrete blockers to actually
scaling past one replica are the ones already listed above: migrations baked into every
pod's entrypoint (section 1) and, once real ADFS is wired in, an in-process-only OIDC
state store (section 6). Address both before running more than one backend replica in
practice; a single replica works fine without touching either.

## 10. What does not change

Same guarantee `CLOSED_NETWORK_MIGRATION.md` already states for its own scope, restated
here because it's just as true for this move: `domain/` and `application/` stay untouched.
Everything in this document is a deployment/infrastructure concern layered on top of the
existing hexagonal architecture — if getting this running on OpenShift ever seems to
require touching `domain/` or `application/`, stop and reconsider; it almost certainly
means the change is leaking through the wrong layer.

## 11. Recommended order

Do this *after* `CLOSED_NETWORK_MIGRATION.md`'s Postgres-and-auth groundwork is done and
verified there, not in parallel with it — OpenShift adds a new axis of complexity
(deployment/orchestration) on top of the network/dependency swap that document covers, and
conflating "did the network move work" with "did the OpenShift deployment work" makes
either one harder to debug if something breaks. Suggested sequence once this section's
prerequisites are settled:

1. Add the non-root `USER` setup to both Dockerfiles; sanity-check locally by running the
   built image with an arbitrary non-root UID (`docker run --user 1000:0 ...`) and
   confirming it still starts.
2. Add the `/health` endpoint; build the frontend as a real production image (static
   build + nginx) instead of the dev server.
3. Split migrations out of `docker-entrypoint.sh` into a standalone Job/script that runs
   once, separately from the app Deployment's rollout.
4. Write the actual resource manifests (format per the open decision in section 3),
   including `readinessProbe`/`livenessProbe` wired to the new health endpoint.
5. Provision Secrets (section 8) and point them at the real closed-network Postgres
   (section 4) — same instance `CLOSED_NETWORK_MIGRATION.md`'s Phase covers.
6. Deploy to a non-production OpenShift project/namespace first. Full manual walkthrough
   (same shape as `PLAN.md`'s "Verification" section) against that deployment.
7. Scale the backend Deployment to 2+ replicas and re-run the walkthrough — this is the
   concrete test of the stateless-auth claim in section 9, not just a theoretical one.
