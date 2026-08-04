"""L1 · one function node feeds one agent node.

Type anything — this level has no inputs. Its conditions are hardcoded (78°F),
which is the point: the function fetches, the agent reasons. The wrapper exists
only to surface the `[fetch_conditions]` line, which otherwise prints to the
server terminal and never reaches the browser.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from _bridge import adapt                                    # noqa: E402
from L1_graph_basics.workflow import workflow as _inner      # noqa: E402

root_agent = adapt(
    _inner,
    name="l1_fetch_then_advise",
    description="A function node and an agent node as peers. Type anything to run it.",
    banner="**L1 · fetch_conditions (function, 0 LLM) → advise (agent, 1 LLM)**",
)

__all__ = ["root_agent"]
