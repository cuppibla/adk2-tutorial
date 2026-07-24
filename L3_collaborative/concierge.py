"""L3 · Pillar 2 — collaborative agents (dynamic subset, run in parallel).

L2's graph was fixed: you drew it before any input arrived. But a chat follow-up
("should I race today?" vs "what about fueling?") should light up DIFFERENT
specialists. You know the TEAM (6 specialists); the request decides the SUBSET.

    race_concierge (coordinator)
      ├─ medical      ├─ gear
      ├─ weather      ├─ nutrition
      ├─ pacing       └─ mental

The coordinator reads the question, picks the relevant specialists, ADK runs the
chosen ones IN PARALLEL (multiple function calls in one turn), then synthesizes
one answer. "What about fueling?" → nutrition only. "Should I race today?" →
medical + weather + pacing. "Anything I should worry about?" → all 6.

Where ADK 2 gives this a direct home: 1.x could build this shape by wrapping each
specialist in AgentTool and letting the coordinator call them. What changes here is
that the team and its parallelism are DECLARED (sub_agents + mode="single_turn")
instead of hand-assembled. (ParallelAgent is always-all; transfer_to_agent is serial.)

Run it:
    python -m L3_collaborative.concierge
    python -m L3_collaborative.concierge "My left knee twinges at mile 18 — safe to keep going?"
"""
from __future__ import annotations

import asyncio
import json
import os
import sys
import time

from dotenv import load_dotenv

from google.adk import Agent, Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types as gtypes

from shared import BundledRunData, RaceStrategy, SpecialistInput, SpecialistResponse, scenario

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


# ─── Specialist factory: six narrow single_turn agents. ───────────────────────

def _specialist(name: str, domain: str, focus: str) -> Agent:
    return Agent(
        name=name, model=MODEL, mode="single_turn",
        # `description` is NOT optional decoration: ADK turns each subagent into a
        # tool and uses this text as that tool's description, so it is what the
        # coordinator actually reads when choosing the subset. Skip it and you are
        # asking the coordinator to route on the agent's *name* alone.
        description=f"Marathon {domain} specialist. Consult for: {focus}.",
        input_schema=SpecialistInput, output_schema=SpecialistResponse,
        instruction=f"""You are a marathon {domain} specialist. Answer ONLY questions
within your domain. Focus: {focus}

Given the question, the current race strategy, and the runner's data, produce a
SpecialistResponse:
- concern_level: "none" | "minor" | "moderate" | "serious"
- recommendation: ONE concrete actionable sentence
- reasoning: ONE sentence citing specific numbers from the strategy or runner data

If the question is outside your domain, set concern_level="none" and say so briefly.""",
    )


medical_specialist = _specialist("medical_specialist", "medical",
    "injury risk, pain, when to stop, hydration safety, heat stroke")
weather_specialist = _specialist("weather_specialist", "weather",
    "heat, cold, wind, rain, race-day forecast adjustments")
pacing_specialist = _specialist("pacing_specialist", "pacing",
    "pace strategy, mile splits, heart rate, target finish time")
gear_specialist = _specialist("gear_specialist", "gear",
    "clothing, shoes, accessories (hats, glasses, gloves), drop-bag contents")
nutrition_specialist = _specialist("nutrition_specialist", "nutrition",
    "fueling plan, gels, electrolytes, hydration timing, pre-race meals")
mental_specialist = _specialist("mental_specialist", "mental",
    "race mindset, motivation, pre-race anxiety, mid-race low points")


# ─── Coordinator: holds the 6 as sub_agents and picks the subset. ─────────────

race_concierge = Agent(
    name="race_concierge",
    model=MODEL,
    sub_agents=[
        medical_specialist, weather_specialist, pacing_specialist,
        gear_specialist, nutrition_specialist, mental_specialist,
    ],
    instruction="""You are a marathon race day concierge. The runner already has a
strategy and is asking a follow-up. Six specialists are available:
medical, weather, pacing, gear, nutrition, mental.

For each question:
1. DECIDE which specialists are genuinely relevant — be precise. Examples:
   "My knee hurts" → medical only. "What about fueling?" → nutrition only.
   "Should I race today?" → medical + weather + pacing. "Anything I should worry
   about?" → all 6. Do NOT invoke specialists whose domain doesn't apply.
2. Call the relevant specialist tools IN PARALLEL (multiple function calls in one
   turn). Each takes a SpecialistInput: user_question (verbatim), current_strategy
   and runner_data (forward both from the user's initial message).
3. SYNTHESIZE their responses into one answer, under 4 sentences, leading with the
   most important concern.

The user's message contains the strategy + runner data as JSON — extract and forward them.""",
)


# ─── A run harness that shows WHICH specialists fired. ─────────────────────────

def _build_message(question: str) -> gtypes.Content:
    """Give the coordinator a question plus a (canned) strategy + runner data."""
    s = scenario()
    runner_data = BundledRunData(
        fetch_weather=s["weather"], analyze_course=s["course"], pull_fitness=s["fitness"],
    )
    # Derive the strategy from the SAME scenario the runner data came from.
    # (Hardcoding a heat-stroke warning here would contradict the 35°F numbers a
    # learner sees after `MARATHON_SCENARIO=COLD` — the specialists would be
    # handed a self-contradicting brief.)
    w = s["weather"]
    if w.temp_f >= 70:
        pacing = "Start 20s/mile slower than goal pace to bank against the heat."
        gear = "Light singlet, cap, sunglasses."
        warning = (f"{w.temp_f:.0f}°F + {w.humidity_pct}% humidity — "
                   "real heat-stroke risk at your usual 7:30 pace.")
    elif w.temp_f <= 40:
        pacing = "Hold goal pace; the cold masks effort, so do not start too fast."
        gear = "Long sleeves, gloves, throwaway layer for the corral."
        warning = (f"{w.temp_f:.0f}°F — hypothermia risk if you slow down late; "
                   "keep a dry layer at the finish.")
    else:
        pacing = "Even splits — conditions are close to ideal for goal pace."
        gear = "Singlet and shorts; no weather adjustment needed."
        warning = (f"{w.temp_f:.0f}°F and {w.conditions} — no weather red flags; "
                   "the risk is going out too fast.")
    strategy = RaceStrategy(
        target_finish="3:32:00",
        pacing_advice=pacing,
        fueling_plan="Electrolytes every aid station.",
        gear=gear,
        key_warning=warning,
    )
    body = (
        f"{question}\n\n"
        f"--- context ---\n"
        f"current_strategy: {strategy.model_dump_json()}\n"
        f"runner_data: {runner_data.model_dump_json()}"
    )
    return gtypes.Content(role="user", parts=[gtypes.Part(text=body)])


async def ask(question: str) -> None:
    runner = Runner(
        node=race_concierge, app_name="l3_concierge",
        session_service=InMemorySessionService(), auto_create_session=True,
    )
    print(f"\n💬 Question: {question}\n")
    specialist_names = {
        "medical_specialist", "weather_specialist", "pacing_specialist",
        "gear_specialist", "nutrition_specialist", "mental_specialist",
    }
    dispatched: list[str] = []
    returned: list[str] = []
    final_text = ""
    t0 = time.perf_counter()
    async for event in runner.run_async(
        user_id="runner_1", session_id="s1", new_message=_build_message(question),
    ):
        # Function calls to specialists reveal the chosen subset. (ADK's built-in
        # transfer_to_agent tool may also appear — we only count our specialists.)
        msg = getattr(event, "message", None)
        for part in getattr(msg, "parts", None) or []:
            fc = getattr(part, "function_call", None)
            if fc and fc.name in specialist_names and fc.name not in dispatched:
                dispatched.append(fc.name)
                print(f"  [t={time.perf_counter()-t0:4.1f}s] DISPATCH → {fc.name}")
            # Each specialist's answer coming back. Printing these timestamps is the
            # evidence for the parallel claim: every DISPATCH shares one timestamp
            # (one turn, many calls) and the REPLIES all land inside one short
            # window — not spaced out end-to-end the way serial calls would be.
            fr = getattr(part, "function_response", None)
            if fr and fr.name in specialist_names and fr.name not in returned:
                returned.append(fr.name)
                print(f"  [t={time.perf_counter()-t0:4.1f}s]   ↩ {fr.name} replied")
            # Only the COORDINATOR's text is the final answer. Specialists stream
            # their raw JSON through this same event stream, so without this author
            # check the last specialist's JSON blob can be printed as the answer.
            if getattr(part, "text", None) and getattr(event, "author", None) == "race_concierge":
                final_text = part.text
    print(f"\n  Specialists chosen: {dispatched or ['(none)']}")
    print(f"  Total time: {time.perf_counter()-t0:.1f}s")
    if final_text:
        print(f"\n🧠 Concierge:\n{final_text}\n")


def main() -> None:
    question = " ".join(sys.argv[1:]) or "Should I race today?"
    asyncio.run(ask(question))


if __name__ == "__main__":
    main()
