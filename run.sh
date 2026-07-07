#!/usr/bin/env bash
# Launch the ADK web UI to browse every level (L0…L4b) as an agent, the same way
# as the adk_tutorial repo. Each folder re-exports `root_agent` so `adk web`
# discovers it. (For the instructive per-level output — parallel timing, the
# recursion trace — use the CLI runners instead, e.g. `python -m L2b_router.workflow`.)
set -euo pipefail
cd "$(dirname "$0")"

# Activate the local venv if present.
if [ -d .venv ]; then
  # shellcheck disable=SC1091
  source .venv/bin/activate
fi

mkdir -p "$HOME/.adk/sessions"
DB_URI="sqlite:///$HOME/.adk/sessions/adk_web_sessions.db"

echo "🚀 Launching ADK web UI — browse L0…L4b as agents"
echo "   → http://localhost:8080"
adk web --session_service_uri "$DB_URI" --host localhost --port 8080 --reload
