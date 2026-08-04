"""L4b · recursive spawning (Pillar 3b).

Same idea as L4a, one step further: each branch may spawn 1-3 deeper questions
of its own. The depth is the model's call; the *limit* is not — `MAX_DEPTH=2`
lives in code. That's the whole lesson.

Ask something broad: *"Tell me everything I should know about racing the Boston
Marathon."* The trace shows the tree it grew.

⚠️ The most expensive level in the repo — 5 to 30 LLM calls per run, depending
on how ambitious the model gets. Run it deliberately.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from _bridge import adapt                                          # noqa: E402
from L4b_recursion.deep_research import l4b_workflow as _inner     # noqa: E402

root_agent = adapt(
    _inner,
    name="l4b_research_recursive",
    description="Decompose → recursive parallel research → synthesize. Ask a broad question.",
    banner="**L4b · runtime DEPTH** — the model grows the tree, MAX_DEPTH=2 in code bounds it",
)

__all__ = ["root_agent"]
