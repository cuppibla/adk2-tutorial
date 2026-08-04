"""L2a · parallel fan-out + JoinNode (Pillar 1a).

Type **HOT**, **COLD** or **NORMAL** to pick the scenario — in the CLI that is
`python -m L2a_parallel_join.workflow COLD`.

The evidence this level is about is in the captured trace: three fetches whose
timestamps overlap, then one join, then a single LLM call.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from _bridge import adapt                                # noqa: E402
from L2a_parallel_join.workflow import root as _inner    # noqa: E402

root_agent = adapt(
    _inner,
    name="l2a_fanout_join",
    description="Three parallel fetches → JoinNode → one strategy agent. Type HOT / COLD / NORMAL.",
    scenario=True,
    banner="**L2a · fan-out ×3 → JoinNode → 1 agent** — watch the fetch timestamps overlap",
)

__all__ = ["root_agent"]
