"""L3a · collaborative agents, mode="single_turn" (Pillar 2).

Ask a real question — "should I race today?", "what about fueling?", "my knee
hurts". The coordinator picks the subset of six specialists that matters and
runs them in parallel.

Two things make this level different from the others here.

1. It is NOT wrapped in a Workflow like L1/L2/L4 are. Running a `single_turn`
   coordinator through `ctx.run_node` breaks in ADK 2.3.0 — its specialists are
   exposed as tools, and their function RESPONSES then look for their function
   CALLS in the wrapper's event stream and don't find them:
       ValueError: No function call event found for function responses ids
   `use_sub_branch=True` does not help. So the coordinator stays the root agent
   and `adk web` talks to it directly, exactly as the CLI harness does.

2. The CLI harness never sends your question alone — it sends the question PLUS
   a canned race strategy and the runner's data (`_build_message`). Without
   that the specialists are instructed to "cite specific numbers from the
   strategy" and have none. A `before_model_callback` splices the same context
   in on the coordinator's first call.

This is the `single_turn` team — beat 2. Beat 1 (the same team in `chat` mode,
which strands the run) stays a CLI-only contrast, because seeing it fail is the
whole point and a browser makes it look like a hang:
    python -m L3a_collaborative.concierge --mode chat "What about fueling?"
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from _bridge import pick_scenario                                  # noqa: E402
from L3a_collaborative.concierge import build_team, _build_message  # noqa: E402

DEFAULT_Q = "Should I race today?"
_CONTEXT_MARK = "--- context ---"


def _inject_context(callback_context, llm_request):
    """Give the coordinator the strategy + runner data the CLI harness injects.

    Runs on every model call this agent makes, so it is careful to be a no-op
    once the context is already in the conversation.
    """
    contents = getattr(llm_request, "contents", None)
    if not contents:
        return None

    last_user = next((c for c in reversed(contents) if getattr(c, "role", None) == "user"), None)
    if last_user is None or not getattr(last_user, "parts", None):
        return None

    # Gemini sends tool results back with role="user" too. On the coordinator's
    # SECOND call — the synthesis turn — the last user content is the pile of
    # specialist function_responses, and rewriting its parts would delete them:
    # the model then re-dispatches every specialist, on a freshly re-read
    # scenario, and you get two contradictory rounds of answers in one reply.
    # Only ever touch a turn that is pure text.
    if any(getattr(p, "function_response", None) or getattr(p, "function_call", None)
           for p in last_user.parts):
        return None

    typed = "".join(getattr(p, "text", "") or "" for p in last_user.parts)
    if _CONTEXT_MARK in typed:            # already enriched (or a later turn)
        return None

    # The typed message doubles as the scenario switch, same as the other levels.
    os.environ["MARATHON_SCENARIO"] = pick_scenario(typed) or "HOT"

    question = typed.strip()
    if not question or question.upper() in ("HOT", "COLD", "NORMAL"):
        question = DEFAULT_Q

    enriched = _build_message(question)   # question + strategy + runner_data
    last_user.parts = list(enriched.parts)
    return None                            # None = proceed with the modified request


# A fresh coordinator rather than the module-level `race_concierge`, so attaching
# a callback here can never leak into the CLI runner's object.
root_agent = build_team("single_turn")
root_agent.before_model_callback = _inject_context

__all__ = ["root_agent"]
