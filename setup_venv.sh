#!/usr/bin/env bash
# One-shot local setup for the ADK 2 tutorial (Mac/Linux).
#   ./setup_venv.sh
# Prefers uv (fast); falls back to python venv + pip.
set -euo pipefail

cd "$(dirname "$0")"

if command -v uv >/dev/null 2>&1; then
  echo "→ using uv"
  uv sync
  echo "✓ done. Run a level with:  uv run python -m L0_first_agent.agent"
else
  echo "→ uv not found, using python venv + pip"
  python3 -m venv .venv
  # shellcheck disable=SC1091
  source .venv/bin/activate
  pip install --upgrade pip
  pip install -r requirements.txt
  echo "✓ done. Activate with:  source .venv/bin/activate"
  echo "  Then run:  python -m L0_first_agent.agent"
fi

if [ ! -f .env ]; then
  cp .env.example .env
  echo "→ created .env — edit it and paste your GOOGLE_API_KEY"
fi

echo
echo "Next:"
echo "  • Browse all levels in the ADK web UI:    ./run.sh"
echo "  • Run one level with its teaching output: python -m L0_first_agent.agent"
