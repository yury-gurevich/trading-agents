"""Root conftest — load .env before any test so os.getenv() picks up local config.

Shell environment takes precedence over .env (override=False), so CI secrets
set as GitHub Actions env vars are never shadowed by the local file.
"""

from dotenv import load_dotenv

load_dotenv(override=False)
