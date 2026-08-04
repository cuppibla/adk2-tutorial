"""L4a · runtime-sized parallel fan-out (Pillar 3a).

Ask a broad question — the broader it is, the wider the graph it builds. Try:
*"Tell me everything I should know about racing the Boston Marathon."*

This level already consumes what you type (its `decompose` node reads the
message), so the wrapper is only here to surface the trace: how many
sub-questions the model chose, and that they ran in parallel.

⚠️ The expensive one — 5-9 LLM calls per run. Don't lean on the button.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from _bridge import adapt                                            # noqa: E402
from L4a_flat_research.deep_research import l4a_workflow as _inner   # noqa: E402

root_agent = adapt(
    _inner,
    name="l4a_research_flat",
    description="Decompose → flat parallel research → synthesize. Ask a broad question.",
    banner="**L4a · runtime WIDTH** — the model picks how many branches; code caps it at 7",
)

__all__ = ["root_agent"]
