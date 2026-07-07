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

This is what's uniquely ADK 2: an LLM picks a per-request subset AND runs it
concurrently. 1.x ParallelAgent is always-all; transfer_to_agent is serial.

Run it:
    python -m L3_collaborative.concierge
    python -m L3_collaborative.concierge "My left knee twinges at mile 18 — safe to keep going?"
"""
from __future__ import annotations

import asyncio
import json
import sys
import time

from dotenv import load_dotenv

from google.adk import Agent, Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types as gtypes

from shared import BundledRunData, RaceStrategy, SpecialistInput, SpecialistResponse, scenario

load_dotenv()

MODEL = "gemini-flash-latest"


# ─── Specialist factory: six narrow single_turn agents. ───────────────────────

def _specialist(name: str, domain: str, focus: str) -> Agent:
    return Agent(
        name=name, model=MODEL, mode="single_turn",
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
    strategy = RaceStrategy(
        target_finish="3:32:00",
        pacing_advice="Start 20s/mile slower than goal pace to bank against the heat.",
        fueling_plan="Electrolytes every aid station.",
        gear="Light singlet, cap, sunglasses.",
        key_warning="78°F + 70% humidity — real heat-stroke risk at your usual 7:30 pace.",
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
            if getattr(part, "text", None):
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
