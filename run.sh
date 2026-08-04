#!/usr/bin/env bash
# Launch the ADK web UI to click through every level (L0…L4b) in a browser.
#
# It serves `webapps/`, not the repo root. Those are thin adapters over the real
# levels — they let the chat box choose the scenario and they surface the
# teaching output (parallel timestamps, the router's branch, the recursion
# trace) that the levels print to stdout, which a browser never sees. Pointed at
# the repo root instead, `adk web` gives you a chat box that ignores what you
# type, a scenario stuck on HOT, and `shared/` in the dropdown as a broken
# entry. See webapps/README.md.
#
# The CLI runners are still the real teaching surface:
#     python -m L2b_router.workflow COLD
set -euo pipefail
cd "$(dirname "$0")"

# Activate the local venv if present.
if [ -d .venv ]; then
  # shellcheck disable=SC1091
  source .venv/bin/activate
fi

mkdir -p "$HOME/.adk/sessions"
DB_URI="sqlite:///$HOME/.adk/sessions/adk_web_sessions.db"

echo "🚀 ADK web UI — 8 levels, click through them in the browser"
echo "   → http://localhost:8080"
echo "   pick a level from the dropdown (top-left); what to type in each: webapps/README.md"
adk web webapps --session_service_uri "$DB_URI" --host localhost --port 8080 --reload
