"""L2b · the deterministic router (Pillar 1b) — the best level to demo live.

Type **HOT**, **COLD** or **NORMAL** and watch the trace pick a different
branch each time. One `if`-statement decides; only the chosen strategy agent
runs, so the whole graph still costs exactly one LLM call.

In the CLI: `python -m L2b_router.workflow COLD`.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from _bridge import adapt                          # noqa: E402
from L2b_router.workflow import root as _inner     # noqa: E402

root_agent = adapt(
    _inner,
    name="l2b_weather_router",
    description="A plain if-statement routes to 1 of 3 strategy agents. Type HOT / COLD / NORMAL.",
    scenario=True,
    banner="**L2b · router → 1 of 3 agents** — same graph, different branch, still one LLM call",
)

__all__ = ["root_agent"]
