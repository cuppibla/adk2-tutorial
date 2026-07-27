"""L3b · Pillar 2 — task mode: the conversational subroutine.

L3a left a gap. `chat` owns the whole conversation; `single_turn` never talks to
the user at all. But real intake work sits in between: "talk to the user UNTIL
you've collected X — then come back with a validated object."

That's `mode="task"`:

    race_desk (coordinator)
      └─ gear_fitter (mode="task", output_schema=GearOrder)

  TURN 1  user: "I need shoes for the marathon."
          desk → delegates to gear_fitter
          gear_fitter: "What size do you wear?"        ← run ENDS here = PAUSED
  TURN 2  user: "Size 9, wide."                        ← same session, new message
          gear_fitter → finish_task(GearOrder(...))    ← validated against the schema
          control auto-returns to race_desk → one confirmation sentence

Two things to watch for in the output:
  1. The run genuinely STOPS after the clarifying question — a paused task, not a
     hang. The next message on the same session resumes the SAME task agent.
  2. `finish_task` is a tool ADK injected because of mode="task". The agent must
     call it to end, and its payload must validate as GearOrder — a conversation
     with a typed finish line.

The one-question rule for choosing a mode:
  "Does the user need to talk to it — and until WHEN?"
  chat = indefinitely · task = until the fields are collected · single_turn = never

Run it:
    python -m L3b_task_desk.desk
    python -m L3b_task_desk.desk "I need a hydration vest" --reply "2 liters, medium"
"""
from __future__ import annotations

import asyncio
import os
import sys
import time

from dotenv import load_dotenv

from google.adk import Agent, Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types as gtypes
from pydantic import BaseModel, Field

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


class GearOrder(BaseModel):
    """The task's contract: the conversation may not end until this validates."""

    item: str = Field(description="the recommended piece of race gear")
    size: str = Field(description="the runner's size, incl. width/volume if given")
    note: str = Field(description="one-line fitting note")


gear_fitter = Agent(
    name="gear_fitter",
    model=MODEL,
    mode="task",                      # ★ the whole level, in one flag
    output_schema=GearOrder,          # ★ the typed finish line the conversation must reach
    description="Race-gear fitting desk. Collects the runner's size, then returns a GearOrder.",
    instruction="""You fit race gear. You MUST know the runner's size before finishing.
If the size is not given, ask ONE short clarifying question for it.
Once you have the size, finish the task with a GearOrder (pick a sensible item).""",
)

race_desk = Agent(
    name="race_desk",
    model=MODEL,
    sub_agents=[gear_fitter],
    instruction="""You are the race-expo front desk. For any gear or equipment request,
delegate to gear_fitter. When it returns its GearOrder, confirm the order back to
the runner in ONE sentence.""",
)


# [harness]
# ─── Harness: two turns, annotated. ────────────────────────────────────────────

async def _turn(runner: Runner, text: str, t0: float) -> tuple[str | None, bool]:
    """Run one user turn; return (author_of_last_text, finish_task_seen)."""
    msg = gtypes.Content(role="user", parts=[gtypes.Part(text=text)])
    last_author, finished = None, False
    async for event in runner.run_async(user_id="runner_1", session_id="s1", new_message=msg):
        author = getattr(event, "author", None)
        for part in (getattr(getattr(event, "message", None), "parts", None) or []):
            fc = getattr(part, "function_call", None)
            if fc and fc.name == "finish_task":
                finished = True
                print(f"  [t={time.perf_counter()-t0:4.1f}s] {author} → finish_task"
                      "   (the tool mode=\"task\" injected; payload validates as GearOrder)")
            elif fc:
                print(f"  [t={time.perf_counter()-t0:4.1f}s] {author} → delegate: {fc.name}")
            if getattr(part, "text", None):
                print(f"  [t={time.perf_counter()-t0:4.1f}s] {author}: {part.text.strip()}")
                last_author = author
    return last_author, finished


async def run_desk(question: str, scripted_reply: str) -> None:
    runner = Runner(
        node=race_desk, app_name="l3b_desk",
        session_service=InMemorySessionService(), auto_create_session=True,
    )
    t0 = time.perf_counter()

    print(f"\n━━ TURN 1 ━━  user: {question!r}")
    author, finished = await _turn(runner, question, t0)
    if not finished and author == "gear_fitter":
        print(
            "\n  ⏸  The run ENDED — but nothing failed. This is a PAUSED task:\n"
            "     gear_fitter asked its clarifying question and is holding the task\n"
            "     open, waiting for the user. (In `adk web` you would just type the\n"
            "     answer; here the next turn scripts it.)"
        )

    print(f"\n━━ TURN 2 ━━  user: {scripted_reply!r}   (same session → resumes the task)")
    author, finished = await _turn(runner, scripted_reply, t0)

    print(f"\n  Total time: {time.perf_counter()-t0:.1f}s")
    if finished and author == "race_desk":
        print(
            "  ✓ finish_task fired → the validated GearOrder flowed back to race_desk\n"
            "    automatically, and the coordinator spoke last. Automatic return is the\n"
            "    difference from chat mode — nobody had to transfer control back.\n"
        )
    else:
        print("  ⚠️ Unexpected shape this run (live LLM) — re-run; the flow above is the normal case.\n")


def main() -> None:
    args = list(sys.argv[1:])
    reply = "Size 9, wide."
    if "--reply" in args:
        i = args.index("--reply")
        reply = args[i + 1] if i + 1 < len(args) else reply
        del args[i:i + 2]
    question = " ".join(args) or "I need shoes for the marathon."
    asyncio.run(run_desk(question, reply))


if __name__ == "__main__":
    main()
