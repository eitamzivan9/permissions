# CI/CD Setup — Remaining Manual Step

`.gitlab-ci.yml` (repo root) is already written, committed, and pushed on the `ci-cd`
branch. It defines two jobs: `backend-tests` (installs the backend in a venv, runs
`pytest -v`) and `frontend-checks` (`npm ci`, lint, build).

One manual, one-time step is still needed before `backend-tests` can succeed on a real
GitLab runner — everything else is done.

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

- Merge the `ci-cd` branch into `main` so the pipeline runs on every future push, not
  just this branch.
- Longer-term, per `CLOSED_NETWORK_MIGRATION.md`: publish `adfs-auth` as a proper
  versioned package to an internal/public index and drop the `file://`/git-URL
  workaround entirely — this setup is a stopgap, not the intended end state.
