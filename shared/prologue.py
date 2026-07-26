"""Prologue · Why not one big prompt?

Before the ladder: the version everyone builds first. ONE agent whose
instruction promises everything the next nine levels will construct properly —
fetch the weather, analyze the course, check the runner's fitness, route by
conditions, produce the full strategy.

Run it and read the answer closely. The numbers are confident, specific — and
INVENTED. The agent has no weather API, no course data, no fitness log; it
cannot fetch anything. It either fabricates the inputs or hedges everything.
Both are the same disease: every step lives inside one opaque model call, so
nothing can be fetched, tested, routed, or trusted.

The whole ladder exists to take those steps OUT of the prompt:
functions fetch (L1–L2a), an if-statement routes (L2b), specialists divide the
work (L3a–L3b), and code bounds the shape (L4a–L4b).

Run it:
    python -m shared.prologue
"""
from __future__ import annotations

import asyncio
import os
import sys

from dotenv import load_dotenv

from google.adk import Agent, Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types as gtypes

load_dotenv()

# [local-only]
if not (os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")):
    sys.exit(
        "✗ No API key found.\n"
        "  cp .env.example .env  then add GOOGLE_API_KEY=...\n"
        "  Get a free key at https://aistudio.google.com/apikey"
    )
# [/local-only]

MODEL = "gemini-flash-latest"

# The mega-prompt: one agent, promised everything. (Deliberately bad — this is
# the "before" picture.)
mega_coach = Agent(
    name="mega_coach",
    model=MODEL,
    instruction="""You are a complete marathon race-day strategy system. You have
access to today's weather forecast, the official course elevation data, and the
runner's training history. For any race the runner names, do ALL of the following:
1. Report today's race-day weather (temperature, wind, humidity).
2. Analyze the course's hardest mile and its grade.
3. Assess the runner's current fitness from their training log.
4. If it is hot, produce a heat strategy; if cold, a cold strategy; otherwise a
   normal-conditions strategy.
5. Output the full plan with SPECIFIC numbers throughout.""",
)


async def run(question: str = "Plan my race-day strategy for the Chicago Marathon.") -> None:
    runner = Runner(node=mega_coach, app_name="prologue",
                    session_service=InMemorySessionService(), auto_create_session=True)
    print(f"\n🏃 You: {question}\n\n🤖 mega_coach:")
    async for event in runner.run_async(
        user_id="u1", session_id="s1",
        new_message=gtypes.Content(role="user", parts=[gtypes.Part(text=question)]),
    ):
        for part in (getattr(getattr(event, "message", None), "parts", None) or []):
            if getattr(part, "text", None):
                print(part.text, end="", flush=True)
    print(
        "\n\n⚠️  Now read it again and ask: where did the temperature come from?\n"
        "    The hardest-mile grade? Your weekly mileage? There is no weather API\n"
        "    here, no course data, no training log — one opaque model call either\n"
        "    INVENTED those numbers or hedged them into uselessness. You cannot\n"
        "    test step 4's routing, you cannot swap step 1 for a real API, and\n"
        "    every run pays for all five steps. Hold that feeling — the next nine\n"
        "    levels take these steps out of the prompt, one at a time.\n"
    )


def main() -> None:
    q = " ".join(sys.argv[1:]) or "Plan my race-day strategy for the Chicago Marathon."
    asyncio.run(run(q))


if __name__ == "__main__":
    main()
