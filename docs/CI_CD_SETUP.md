# CI/CD Setup

`.gitlab-ci.yml` (repo root) is written, committed, and pushed on the `ci-cd` branch. It
defines three jobs: `backend-tests` and `db-tests` (both install the backend in a venv;
`backend-tests` runs the hermetic `pytest -v`, `db-tests` runs `pytest tests/db -v`
against a `postgres:17.7` service container) and `frontend-checks` (`npm ci`, lint,
build).

**Confirmed done, 2026-08-21**: the manual Token Access step below has been completed —
verified directly from a real pipeline run
(`gitlab.com/eitamzivan9/premissions/-/pipelines`, `ci-cd` branch, commit `02610bca`):
`db-tests`' log shows `pip install -e ".[dev]"` successfully cloning `adfs-auth` via
`CI_JOB_TOKEN` (`Cloning https://gitlab-ci-token:****@gitlab.com/eitamzivan9/adfs-auth.git`
→ `Resolved ... to commit 791e3d2`) and all three jobs passing. Nothing in
`.gitlab-ci.yml` is branch-specific, so this holds after merging `ci-cd` into `main`
too — kept below as a reference for what the setting is and how to re-verify it if it
ever needs redoing (e.g. after rotating/regenerating access on the `adfs-auth` side).

## Why it's needed

`backend/pyproject.toml` depends on `adfs-auth` via a hardcoded local path
(`file:///C:/Users/Eitam/adfs-auth`), which only exists on this dev machine (see
`CLOSED_NETWORK_MIGRATION.md`). The CI job works around this by rewriting that one
dependency line at runtime to fetch `adfs-auth` from its own GitLab repo
(`gitlab.com/eitamzivan9/adfs-auth`) instead, authenticating with GitLab's built-in
`CI_JOB_TOKEN`. For that fetch to be allowed, the `adfs-auth` project must explicitly
grant `premissions` access.

## Steps

1. Go to `gitlab.com/eitamzivan9/adfs-auth` — the **adfs-auth** project (the setting
   is made on the target repo being fetched, not on `premissions`).
2. Open **Settings → CI/CD** (left sidebar).
3. Expand the **Token Access** section.
4. Under the allowlist, add the `premissions` project — either by its project path
   (`eitamzivan9/premissions`) or project ID (found on the `premissions` project's
   Settings → General page).
5. Click **Save changes**.

## How to verify it worked

1. Go to `gitlab.com/eitamzivan9/premissions/-/pipelines`.
2. Find the pipeline run for the `ci-cd` branch.
3. Check the `backend-tests` job:
   - **Green** → either this setting is now correctly in place, or `adfs-auth` is
     public enough that job-token access wasn't required (check under `adfs-auth`'s
     Settings → General → Visibility).
   - **Failed on the `git clone`/`pip install` step with an auth or 403 error** → this
     Token Access setting is what's missing; redo the steps above.

## After this works

- Merging the `ci-cd` branch into `main` is safe — confirmed above, the pipeline isn't
  branch-scoped.
- Longer-term, per `migration/CLOSED_NETWORK_MIGRATION.md`: publish `adfs-auth` as a
  proper versioned package to an internal/public index and drop the `file://`/git-URL
  workaround entirely — this setup is a stopgap, not the intended end state.
