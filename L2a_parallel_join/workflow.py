"""L2a · Parallel fan-out + JoinNode (Pillar 1, part 1 of 2).

The first half of a graph workflow. Three fetches run IN PARALLEL (0 LLM), a
`JoinNode` bundles them into one typed payload, and a single strategy agent
writes the plan. There's no router yet — every run uses the same one agent.
L2b adds the deterministic router that picks a specialized agent.

    START ─► fetch_weather ──┐
    START ─► analyze_course ─┼─► JoinNode ─► strategy (1 agent)
    START ─► pull_fitness ───┘

Run it:
    python -m L2a_parallel_join.workflow          # HOT
    python -m L2a_parallel_join.workflow COLD
"""
from __future__ import annotations

import asyncio
import os
import sys
import time

from dotenv import load_dotenv

from google.adk import Agent, Event, Runner, Workflow
from google.adk.workflow import JoinNode, START
from google.adk.sessions import InMemorySessionService

from shared import BundledRunData, RaceStrategy, scenario, slow_mo

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


# ─── Fetch nodes: parallel, zero LLM. Simulated latency so you SEE concurrency. ─
#
# Each fetch prints when it starts and finishes, relative to the start of the run.
# That overlap is the actual evidence for the parallel claim — all three start at
# ~0.0s and the fan-out ends when the SLOWEST one does, not when their durations
# add up. (Wall time for the whole run is a bad proxy: it also contains the
# strategy agent's LLM call, which is several seconds on its own.)

_T0 = 0.0


def _stamp(msg: str) -> None:
    print(f"  [t={time.perf_counter() - _T0:4.1f}s] {msg}")


async def _fetch(name: str, seconds: float, key: str):
    _stamp(f"{name} started")
    await asyncio.sleep(seconds * slow_mo())
    _stamp(f"{name} finished")
    return Event(output=scenario()[key].model_dump())


async def fetch_weather(node_input):
    return await _fetch("fetch_weather", 1.5, "weather")


async def analyze_course(node_input):
    return await _fetch("analyze_course", 2.0, "course")


async def pull_fitness(node_input):
    return await _fetch("pull_fitness", 1.0, "fitness")


# ─── Join: bundle the three parallel results into one typed payload. ──────────

join_inputs = JoinNode(name="join_inputs")   # ★ waits for ALL branches, bundles outputs keyed by function name


# ─── One strategy agent (no routing yet). ─────────────────────────────────────

strategy = Agent(
    name="strategy", model=MODEL,
    input_schema=BundledRunData, output_schema=RaceStrategy,
    instruction="""You are a marathon coach. You receive BundledRunData (weather from
fetch_weather, course from analyze_course, fitness from pull_fitness). Produce a
RaceStrategy that ADAPTS to whatever the conditions are — hot, cold, or ideal.
Cite actual numbers (temps, mile numbers, the runner's pace). Each field 1-2
short sentences.""",
)


# ─── The workflow: fan-out, join, one agent. ──────────────────────────────────

root = Workflow(
    name="l2a_parallel_join",
    description="Parallel data gathering + a single strategy agent.",
    edges=[
        # ★ three edges from START — this IS the fan-out
        (START, fetch_weather, join_inputs),
        (START, analyze_course, join_inputs),
        (START, pull_fitness, join_inputs),
        (join_inputs, strategy),
    ],
)


# [harness]
def _event_text(event):
    msg = getattr(event, "message", None)
    if msg and getattr(msg, "parts", None):
        chunks = [p.text for p in msg.parts if getattr(p, "text", None)]
        if chunks:
            return "".join(chunks)
    out = getattr(event, "output", None)
    return out if isinstance(out, str) else None


async def run(scenario_name="HOT"):
    global _T0
    os.environ["MARATHON_SCENARIO"] = scenario_name.upper()
    print(f"=== L2a · scenario: {scenario_name.upper()} ===")
    runner = Runner(node=root, app_name="l2a", session_service=InMemorySessionService(), auto_create_session=True)
    t0 = _T0 = time.perf_counter()
    async for event in runner.run_async(user_id="u1", session_id="s1", new_message=None):
        t = _event_text(event)
        if t:
            print(f"\n🏁 RaceStrategy:\n{t}")
    print(f"\n  Total wall time: {time.perf_counter()-t0:.1f}s "
          f"(fan-out + join + 1 LLM call — the fetch timestamps above are the parallel evidence)")


if __name__ == "__main__":
    asyncio.run(run(sys.argv[1] if len(sys.argv) > 1 else "HOT"))
