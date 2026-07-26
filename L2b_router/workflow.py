"""L2b · Add the deterministic router (Pillar 1, part 2 of 2).

L2a bundled three parallel fetches into one agent. Now we add a DETERMINISTIC
router — a plain `if`-statement, not a model decision — that branches on
temperature and picks exactly one of three specialized strategy agents.

    START ─► fetch_weather ──┐
    START ─► analyze_course ─┼─► JoinNode ─► route_by_weather ─► hot_strategy
    START ─► pull_fitness ───┘   (bundles)   (if-statement)   ─► normal_strategy
                                                             ─► cold_strategy

The takeaway — three kinds of work, three homes:
  • Predictable work → FUNCTIONS (the 3 fetches, 0 LLM calls)
  • A clear rule    → EXPLICIT ROUTING (route_by_weather is an if-statement)
  • Reasoning       → THE MODEL (exactly ONE strategy agent writes the answer)

Net cost: 1 LLM call. To be fair to 1.x: a custom `BaseAgent` subclass could keep
these steps out of the model there too — but you wrote the orchestration plumbing
yourself, so most builds wrapped each step as an agent and paid 4 calls.

Run it:
    python -m L2b_router.workflow          # HOT — Boston, 78°F
    python -m L2b_router.workflow NORMAL   # Berlin, 58°F
    python -m L2b_router.workflow COLD      # Chicago, 35°F
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
if not (os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")):
    sys.exit(
        "\u2717 No API key found.\n"
        "  cp .env.example .env  then add GOOGLE_API_KEY=...\n"
        "  Get a free key at https://aistudio.google.com/apikey"
    )
# [/local-only]


MODEL = "gemini-flash-latest"


# ─── Fetch nodes (same as L2a): parallel, zero LLM. ───────────────────────────

async def fetch_weather(node_input):
    await asyncio.sleep(1.5 * slow_mo())
    return Event(output=scenario()["weather"].model_dump())


async def analyze_course(node_input):
    await asyncio.sleep(2.0 * slow_mo())
    return Event(output=scenario()["course"].model_dump())


async def pull_fitness(node_input):
    await asyncio.sleep(1.0 * slow_mo())
    return Event(output=scenario()["fitness"].model_dump())


join_inputs = JoinNode(name="join_inputs")


# ─── The new part: a deterministic router. An if-statement, not the model. ────

def route_by_weather(node_input):
    """node_input is the JoinNode payload, keyed by upstream function names.
    Emit `route=` to pick exactly one downstream branch."""
    temp = node_input["fetch_weather"]["temp_f"]
    if temp >= 70:
        route = "HOT"
    elif temp <= 40:
        route = "COLD"
    else:
        route = "NORMAL"
    print(f"  [router] temp={temp}°F → route={route}  (an if-statement, 0 LLM)")
    return Event(output=node_input, route=route)


# ─── Three specialized strategy agents. Only one ever runs. ───────────────────

_FMT = """
You receive BundledRunData (weather/course/fitness). Produce a RaceStrategy.
Cite actual numbers (temps, mile numbers, the runner's pace). Each field 1-2
short sentences.
"""

hot_strategy = Agent(
    name="hot_strategy", model=MODEL,
    input_schema=BundledRunData, output_schema=RaceStrategy,
    instruction=f"""You are a marathon coach planning a race in HOT conditions.
Heat is the primary risk: slow down, hydrate aggressively, dress cool, set a
goal time SLOWER than ideal.{_FMT}""",
)

normal_strategy = Agent(
    name="normal_strategy", model=MODEL,
    input_schema=BundledRunData, output_schema=RaceStrategy,
    instruction=f"""You are a marathon coach planning a race in IDEAL conditions.
This is a PR-attempt day. Recommend even or slightly negative splits; the main
risk is going out too fast on cool, fast-feeling pavement.{_FMT}""",
)

cold_strategy = Agent(
    name="cold_strategy", model=MODEL,
    input_schema=BundledRunData, output_schema=RaceStrategy,
    instruction=f"""You are a marathon coach planning a race in COLD conditions.
Recommend layered, shed-able gear, a careful warm-up, and fueling that accounts
for cold-suppressed thirst. If winds are strong, advise drafting.{_FMT}""",
)


# ─── The workflow: L2a + the router and its dict-edge. ────────────────────────

root = Workflow(
    name="marathon_strategy",
    description="Parallel data gathering + deterministic routing to one of three agents.",
    edges=[
        (START, fetch_weather, join_inputs),
        (START, analyze_course, join_inputs),
        (START, pull_fitness, join_inputs),
        (join_inputs, route_by_weather),
        (route_by_weather, {
            "HOT": hot_strategy,
            "NORMAL": normal_strategy,
            "COLD": cold_strategy,
        }),
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
    os.environ["MARATHON_SCENARIO"] = scenario_name.upper()
    print(f"=== L2b · scenario: {scenario_name.upper()} ===")
    runner = Runner(node=root, app_name="l2b", session_service=InMemorySessionService(), auto_create_session=True)
    t0 = time.perf_counter()
    async for event in runner.run_async(user_id="u1", session_id="s1", new_message=None):
        t = _event_text(event)
        if t:
            print(f"\n🏁 RaceStrategy:\n{t}")
    print(f"\n  Wall time: {time.perf_counter()-t0:.1f}s (3 fetches parallel; strategy = 1 LLM call)")


if __name__ == "__main__":
    asyncio.run(run(sys.argv[1] if len(sys.argv) > 1 else "HOT"))
