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

MODEL = "gemini-flash-latest"


# ─── Fetch nodes: parallel, zero LLM. Simulated latency so you SEE concurrency. ─

async def fetch_weather(node_input):
    await asyncio.sleep(1.5 * slow_mo())
    return Event(output=scenario()["weather"].model_dump())


async def analyze_course(node_input):
    await asyncio.sleep(2.0 * slow_mo())
    return Event(output=scenario()["course"].model_dump())


async def pull_fitness(node_input):
    await asyncio.sleep(1.0 * slow_mo())
    return Event(output=scenario()["fitness"].model_dump())


# ─── Join: bundle the three parallel results into one typed payload. ──────────

join_inputs = JoinNode(name="join_inputs")


# ─── One strategy agent (no routing yet). ─────────────────────────────────────

strategy = Agent(
    name="strategy", model=MODEL, mode="single_turn",
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
        (START, fetch_weather, join_inputs),
        (START, analyze_course, join_inputs),
        (START, pull_fitness, join_inputs),
        (join_inputs, strategy),
    ],
)


def _event_text(event):
    msg = getattr(event, "message", None)
    if msg and getattr(msg, "parts", None):
        chunks = [p.text for p in msg.parts if getattr(p, "text", None)]
        if chunks:
            return "".join(chunks)
    out = getattr(event, "output", None)
    return out if isinstance(out, str) else None


async def run(scenario_name="HOT"):
    os.environ["MARATHON_SCENARIO"] = scenario_name.upper()
    print(f"=== L2a · scenario: {scenario_name.upper()} ===")
    runner = Runner(node=root, app_name="l2a", session_service=InMemorySessionService(), auto_create_session=True)
    t0 = time.perf_counter()
    async for event in runner.run_async(user_id="u1", session_id="s1", new_message=None):
        t = _event_text(event)
        if t:
            print(f"\n🏁 RaceStrategy:\n{t}")
    print(f"\n  Wall time: {time.perf_counter()-t0:.1f}s (3 fetches ran in parallel)")


if __name__ == "__main__":
    asyncio.run(run(sys.argv[1] if len(sys.argv) > 1 else "HOT"))
