"""Forces the test suite to always run against Phase 1 in-memory repositories,
regardless of whether backend/.env sets PERMISSIONS_DATABASE_URL for normal
`uvicorn` runs. Tests must stay hermetic — set before any other import so
config.get_settings() never sees the .env value (env vars take precedence over
.env in pydantic-settings, but only if set before Settings() is instantiated)."""

import os

os.environ["PERMISSIONS_DATABASE_URL"] = ""
