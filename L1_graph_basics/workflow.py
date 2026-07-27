"""L1 · Your first Workflow — a function node and an agent node, side by side.

The one idea of ADK 2 graph workflows: a plain Python function and an LLM
agent are BOTH just nodes in the same `edges` list. Predictable work (fetching,
parsing, math) stays a function and costs zero LLM calls; only the reasoning
step is an agent.

    START ──► fetch_conditions (function, 0 LLM) ──► advise (agent, 1 LLM)

Compare with L0: there we called an agent directly. Here the agent sits *inside*
a graph, and a function node prepares its input first.

Run it:
    python -m L1_graph_basics.workflow
"""
from __future__ import annotations

import asyncio
import os
import sys

from dotenv import load_dotenv
from pydantic import BaseModel

from google.adk import Agent, Event, Runner, Workflow
from google.adk.workflow import START
from google.adk.sessions import InMemorySessionService

load_dotenv()

# [local-only]
# Fail fast with one readable line. Without this, a missing key surfaces ~290
# lines of ADK/asyncio traceback with the real cause on the very last line.
_vertex = os.getenv("GOOGLE_GENAI_USE_VERTEXAI", "").lower() in ("true", "1", "yes")
if not (os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY") or _vertex):
    sys.exit(
        "\u2717 No API key found.\n"
        "  cp .env.example .env  then add GOOGLE_API_KEY=...\n"
        "  Get a free key at https://aistudio.google.com/apikey\n"
        "  (On GCP: export GOOGLE_GENAI_USE_VERTEXAI=True + GOOGLE_CLOUD_PROJECT instead.)"
    )
# [/local-only]


MODEL = os.getenv("ADK_MODEL", "gemini-flash-latest")   # AI Studio alias; on Vertex set ADK_MODEL=gemini-2.5-flash
if os.getenv("GOOGLE_GENAI_USE_VERTEXAI", "").lower() in ("true", "1", "yes") and "latest" in MODEL:
    sys.exit(
        f"\u2717 ADK_MODEL={MODEL!r} is an AI-Studio-only alias and 404s on Vertex AI.\n"
        "  export ADK_MODEL=gemini-2.5-flash   (then re-run)"
    )


# ─── A tiny schema so the function node and the agent speak the same shape ─────

class Conditions(BaseModel):
    temp_f: float
    wind_mph: float
    conditions: str


# ─── Node 1: a plain function. No model, no cost — just prepares data. ─────────

def fetch_conditions(node_input):
    """In a real app this hits a weather API. Here it returns canned data.

    Returning `Event(output=...)` is the explicit form. A function node may also
    return a bare value or a pydantic model and ADK wraps it for you — the explicit
    form is used here because L2b needs its sibling, `Event(output=..., route=...)`.
    """
    data = Conditions(temp_f=78, wind_mph=12, conditions="sunny")
    print(f"  [fetch_conditions] (function node, 0 LLM) → {data.model_dump()}")
    return Event(output=data.model_dump())


# ─── Node 2: an agent. The only step that calls the model. ────────────────────

advise = Agent(
    name="advise",
    model=MODEL,
    input_schema=Conditions,  # receives the function node's output, validated
    instruction=(
        "You are a marathon coach. Given today's race-day conditions, give the "
        "runner 2-3 sentences of specific advice on pacing and gear for THESE "
        "conditions. Reference the actual temperature and wind."
    ),
)


# ─── The workflow: two nodes, one edge chain. ─────────────────────────────────

workflow = Workflow(
    name="l1_graph_basics",
    description="One function node feeds one agent node.",
    edges=[(START, fetch_conditions, advise)],   # ★ a function and an agent — peers in one chain
)


# [harness]
def _event_text(event) -> str | None:
    if getattr(event, "message", None) and getattr(event.message, "parts", None):
        chunks = [p.text for p in event.message.parts if getattr(p, "text", None)]
        if chunks:
            return "".join(chunks)
    out = getattr(event, "output", None)
    return out if isinstance(out, str) else None


async def main() -> None:
    runner = Runner(
        node=workflow,
        app_name="l1_graph_basics",
        session_service=InMemorySessionService(),
        auto_create_session=True,
    )
    print("=== L1 workflow: fetch_conditions (function) → advise (agent) ===")
    async for event in runner.run_async(
        user_id="runner_1", session_id="session_1", new_message=None,
    ):
        text = _event_text(event)
        if text:
            print(f"\n🧠 Coach: {text}\n")


if __name__ == "__main__":
    asyncio.run(main())
