"""Adapters that make the levels usable from `adk web`, without touching them.

`adk web` hands a node one thing — whatever the user typed — and renders only
the events that come back. The levels were written for the CLI, where the
scenario is `argv[1]` and the teaching evidence (parallel fetch timestamps, the
router's chosen branch, the recursion trace) is `print()`ed. Point `adk web`
straight at a level and you get three problems:

  1. the chat box is really a Run button — L1/L2a/L2b call `run_async(
     new_message=None)`, so nothing you type reaches the graph. Verified: ask
     L1 "what is the capital of France?" and it answers about 78°F.
  2. the scenario is stuck on HOT (`shared/scenarios.py` default), so L2b —
     a level whose entire subject is routing — only ever takes one branch.
  3. every interesting line goes to the SERVER terminal, not the browser.

Fixing that inside the levels was the wrong trade. L2a is a lesson about
fan-out, not about parsing user input, and converting its `print()`s into
events would wreck the CLI output the codelab is built around. So the levels
stay exactly as they are and this layer adapts them from outside:

  * the typed message picks the scenario (HOT / COLD / NORMAL)
  * the level's own stdout is captured and shown in the browser
  * L3a gets the strategy + runner data its CLI harness injects

Point `adk web` here (./run.sh does), NOT at the repo root — that also keeps
`shared/` out of the dropdown, where it appears as an agent and errors if you
pick it.

The CLI runners remain the real teaching surface; this is for clicking around.
"""
from __future__ import annotations

import contextlib
import io
import json
import os
import sys
from pathlib import Path

# The level packages live one directory up. `adk web` puts THIS directory on
# sys.path (that is how it imports each wrapper), not the repo root.
REPO = Path(__file__).resolve().parent.parent
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from google.adk import Event, Workflow            # noqa: E402
from google.adk.workflow import START, node       # noqa: E402

SCENARIOS = ("HOT", "COLD", "NORMAL")


def text_of(node_input) -> str:
    """Whatever the user typed, as a plain string."""
    if isinstance(node_input, str):
        return node_input
    parts = getattr(node_input, "parts", None)
    if parts:
        return "".join(getattr(p, "text", "") or "" for p in parts)
    return "" if node_input is None else str(node_input)


def pick_scenario(typed: str) -> str | None:
    up = (typed or "").upper()
    return next((s for s in SCENARIOS if s in up), None)


def _render(value) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, (dict, list)):
        try:
            return "```json\n" + json.dumps(value, indent=2, default=str) + "\n```"
        except Exception:
            pass
    return str(value)


def adapt(inner, *, name, description, scenario=False, enrich=None, banner="",
          sub_branch=False):
    """Wrap a level's root node in a one-node Workflow that adk web can drive.

    scenario:   let the typed message choose HOT / COLD / NORMAL.
    enrich:     str -> node_input, for levels whose CLI harness builds a richer
                message than the user types (L3a).
    sub_branch: run the inner node with its events isolated. Required when the
                inner node is an Agent that delegates to sub_agents — its
                specialists' function RESPONSES otherwise look for their
                function CALLS in the wrapper's event stream and don't find
                them ("No function call event found for function responses").
    """
    @node(rerun_on_resume=True)          # required before ctx.run_node
    async def entry(ctx, node_input):
        typed = text_of(node_input)
        chosen = pick_scenario(typed) if scenario else None
        if scenario:
            # Reset every run rather than letting a previous COLD linger — a demo
            # that silently remembers state is a demo that confuses the room.
            os.environ["MARATHON_SCENARIO"] = chosen or "HOT"

        payload = enrich(typed) if enrich else node_input

        # The level prints its teaching evidence; that stdout belongs to the
        # server, so capture it and hand it to the browser instead.
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            result = await ctx.run_node(inner, node_input=payload,
                                        use_sub_branch=sub_branch)

        blocks = []
        if banner:
            blocks.append(banner)
        if scenario:
            note = "" if chosen else "  ·  type HOT, COLD or NORMAL to switch"
            blocks.append(f"**scenario: {os.environ['MARATHON_SCENARIO']}**{note}")
        trace = buf.getvalue().strip()
        if trace:
            blocks.append("```\n" + trace + "\n```")
        blocks.append(_render(result))

        # One output per node execution — ADK raises if a node sets it twice.
        yield Event(output="\n\n".join(b for b in blocks if b))

    return Workflow(name=name, description=description, edges=[(START, entry)])
