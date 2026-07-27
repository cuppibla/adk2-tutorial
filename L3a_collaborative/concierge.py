"""L3a · Pillar 2 — collaborative agents: one flag, two worlds.

L2's graph was fixed: you drew it before any input arrived. But a chat follow-up
("should I race today?" vs "what about fueling?") should light up DIFFERENT
specialists. You know the TEAM (6 specialists); the request decides the SUBSET.

    race_concierge (coordinator)
      ├─ medical      ├─ gear
      ├─ weather      ├─ nutrition
      ├─ pacing       └─ mental

This level runs the SAME team twice — the only difference is the subagents' `mode`:

  Beat 1 · mode unset (chat, the subagent default) — run it and watch it fail the
  job: the coordinator gets NO delegation tools, only `transfer_to_agent`; it can
  hand the conversation to exactly ONE specialist; that specialist answers the
  user directly and the run ends there. No parallelism. No synthesis. Stranded.

  Beat 2 · mode="single_turn" — the coordinator gets one delegation tool PER
  specialist, calls the relevant subset IN PARALLEL (many calls, one turn), every
  specialist auto-returns its result, and the coordinator synthesizes one answer.

Same prompt, same team, one flag. The contrast is the lesson.

Where ADK 2 gives this a direct home: 1.x could build this shape by wrapping each
specialist in AgentTool and letting the coordinator call them. What changes here is
that the team and its parallelism are DECLARED (sub_agents + mode="single_turn")
instead of hand-assembled. (ParallelAgent is always-all; transfer_to_agent is serial.)

Run it:
    python -m L3a_collaborative.concierge --mode chat          # Beat 1: watch it strand
    python -m L3a_collaborative.concierge                      # Beat 2: parallel + synthesis
    python -m L3a_collaborative.concierge "My left knee twinges at mile 18 — safe to keep going?"
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
_vertex = os.getenv("GOOGLE_GENAI_USE_VERTEXAI", "").lower() in ("true", "1", "yes")
if not (os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY") or _vertex):
    sys.exit(
        "✗ No API key found.\n"
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

SPECIALIST_SPECS = [
    ("medical_specialist", "medical", "injury risk, pain, when to stop, hydration safety, heat stroke"),
    ("weather_specialist", "weather", "heat, cold, wind, rain, race-day forecast adjustments"),
    ("pacing_specialist", "pacing", "pace strategy, mile splits, heart rate, target finish time"),
    ("gear_specialist", "gear", "clothing, shoes, accessories (hats, glasses, gloves), drop-bag contents"),
    ("nutrition_specialist", "nutrition", "fueling plan, gels, electrolytes, hydration timing, pre-race meals"),
    ("mental_specialist", "mental", "race mindset, motivation, pre-race anxiety, mid-race low points"),
]

SPECIALIST_NAMES = {name for name, _, _ in SPECIALIST_SPECS}


# ─── Specialist factory. `mode` is THE variable this level teaches. ────────────

def _specialist(name: str, domain: str, focus: str, mode: str | None) -> Agent:
    # NOTE: this `if` exists ONLY so one team can be built both ways for the
    # contrast — a real app hardcodes one mode and the branch disappears.
    kwargs = {}
    if mode == "single_turn":
        # The structured contract only makes sense when the specialist is a TOOL:
        # it receives a SpecialistInput and must return a SpecialistResponse.
        # A chat specialist talks to the user in prose — no schemas.
        kwargs = dict(mode="single_turn",   # ★ THE flag this level is about
                      input_schema=SpecialistInput, output_schema=SpecialistResponse)
    return Agent(
        name=name, model=MODEL,
        # `description` is NOT optional decoration: in single_turn mode ADK turns
        # each subagent into a tool and uses this text as that tool's description,
        # so it is what the coordinator actually reads when choosing the subset.
        description=f"Marathon {domain} specialist. Consult for: {focus}.",
        instruction=f"""You are a marathon {domain} specialist. Answer ONLY questions
within your domain. Focus: {focus}

Given the question, the current race strategy, and the runner's data, produce:
- concern_level: "none" | "minor" | "moderate" | "serious"
- recommendation: ONE concrete actionable sentence
- reasoning: ONE sentence citing specific numbers from the strategy or runner data

If the question is outside your domain, set concern_level="none" and say so briefly.""",
        **kwargs,
    )


def build_team(mode: str | None) -> Agent:
    """Build a FRESH team (agents can't be shared between parents).

    The coordinator's instruction is IDENTICAL in both modes — on purpose. In chat
    mode it physically cannot comply ("call the tools in parallel" — there are no
    tools), which is exactly the point: the capability lives in the mode flag, not
    in the prompt.
    """
    team = [_specialist(n, d, f, mode) for n, d, f in SPECIALIST_SPECS]
    return Agent(
        name="race_concierge",
        model=MODEL,
        sub_agents=team,
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


# For `adk web` and imports: the version that actually does the job.
race_concierge = build_team("single_turn")


# [harness]
# ─── A run harness that shows WHO decided, WHO ran, and WHO answered. ──────────

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


async def ask(question: str, mode: str = "single_turn") -> None:
    label = "chat (the default — no mode= written)" if mode != "single_turn" else 'mode="single_turn"'
    coordinator = build_team(mode if mode == "single_turn" else None)
    runner = Runner(
        node=coordinator, app_name="l3a_concierge",
        session_service=InMemorySessionService(), auto_create_session=True,
    )
    print(f"\n━━ Subagents in {label} ━━")
    print(f"💬 Question: {question}\n")
    dispatched: list[str] = []
    returned: list[str] = []
    final_text, final_author = "", None
    t0 = time.perf_counter()
    async for event in runner.run_async(
        user_id="runner_1", session_id="s1", new_message=_build_message(question),
    ):
        author = getattr(event, "author", None)
        msg = getattr(event, "message", None)
        for part in getattr(msg, "parts", None) or []:
            fc = getattr(part, "function_call", None)
            # chat mode: the ONLY tool the coordinator has is transfer_to_agent —
            # a serial handoff of the whole conversation to one subagent.
            if fc and fc.name == "transfer_to_agent":
                target = (fc.args or {}).get("agent_name", "?")
                print(f"  [t={time.perf_counter()-t0:4.1f}s] TRANSFER → {target}"
                      "   (transfer_to_agent — the only tool chat subagents provide)")
            # single_turn mode: one delegation tool PER specialist, many calls in
            # one turn = the parallel dispatch.
            if fc and fc.name in SPECIALIST_NAMES and fc.name not in dispatched:
                dispatched.append(fc.name)
                print(f"  [t={time.perf_counter()-t0:4.1f}s] DISPATCH → {fc.name}")
            # Replies landing inside one short window = the parallel evidence.
            fr = getattr(part, "function_response", None)
            if fr and fr.name in SPECIALIST_NAMES and fr.name not in returned:
                returned.append(fr.name)
                print(f"  [t={time.perf_counter()-t0:4.1f}s]   ↩ {fr.name} replied")
            # Track WHO produced the last text — in chat mode it will be the
            # specialist (the conversation was carried away); in single_turn mode
            # it must be the coordinator's synthesis.
            if getattr(part, "text", None):
                final_text, final_author = part.text, author
    print(f"\n  Total time: {time.perf_counter()-t0:.1f}s")
    if mode == "single_turn":
        print(f"  Specialists chosen: {dispatched or ['(none)']}")
        if final_author == "race_concierge" and final_text:
            print(f"\n🧠 Concierge (synthesized):\n{final_text}\n")
        else:
            print("\n⚠️ No coordinator synthesis captured this run (rare) — re-run.")
    else:
        print(f"  Final speaker: {final_author}")
        if final_author != "race_concierge":
            print(f"\n🗣️ {final_author} (answering the user DIRECTLY):\n{final_text}")
            print(
                "\n⛔ Note what did NOT happen: no parallel dispatch, no return to the\n"
                "   coordinator, no synthesis. The conversation now BELONGS to this\n"
                "   specialist until someone transfers it away. That's chat mode —\n"
                "   right for an open-ended assistant, wrong for a pipeline step.\n"
            )
        else:
            print(f"\n🧠 Coordinator answered without delegating:\n{final_text}\n")


def main() -> None:
    args = [a for a in sys.argv[1:]]
    mode = "single_turn"
    if "--mode" in args:
        i = args.index("--mode")
        mode = args[i + 1] if i + 1 < len(args) else "single_turn"
        del args[i:i + 2]
    question = " ".join(args) or "Should I race today?"
    asyncio.run(ask(question, mode=mode))


if __name__ == "__main__":
    main()
