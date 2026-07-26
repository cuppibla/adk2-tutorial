"""L0 · Your first ADK 2 agent — a model, an instruction, and one real tool.

The smallest complete ADK 2 program: ONE agent, ONE tool, ONE Runner.
No workflows, no schemas, no sub-agents yet.

    Agent  → the thing that reasons (a Gemini model + an instruction)
    tool   → a plain Python function the MODEL decides to call when it needs it
    Runner → the thing that executes an agent inside a session and streams events

The tool matters: an LLM doing pace arithmetic in its head will happily be
wrong. `pace_splits` is deterministic Python — when the runner names a goal
time, the model calls it and gets EXACT numbers. Watch the 🔧 line in the
output: that is the model deciding, mid-answer, to use your code.

Run it:
    python -m L0_first_agent.agent
    python -m L0_first_agent.agent "What should I eat the night before a marathon?"
"""
from __future__ import annotations

import asyncio
import os
import sys

from dotenv import load_dotenv

from google.adk import Agent, Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types as gtypes

load_dotenv()  # reads GOOGLE_API_KEY / GEMINI_API_KEY from .env

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


# 1) A tool is just a Python function with a docstring and type hints —
#    ADK reads the signature and hands the model a declaration for it.
def pace_splits(target_finish: str) -> dict:
    """Convert a marathon goal time like '3:30:00' (or '3:30') into exact
    per-mile and per-km paces. Use this instead of estimating arithmetic."""
    parts = target_finish.strip().split(":")
    h, m, s = ([0, 0, 0] + [int(x) for x in parts])[-3:]
    total = h * 3600 + m * 60 + s
    fmt = lambda sec: f"{int(sec // 60)}:{int(sec % 60):02d}"
    return {
        "per_mile": fmt(total / 26.2188),
        "per_km": fmt(total / 42.195),
        "goal": f"{h}:{m:02d}:{s:02d}",
    }


# 2) Define an agent — a model, a role, and the tools it may use.
pace_coach = Agent(
    name="pace_coach",
    model=MODEL,
    tools=[pace_splits],
    instruction=(
        "You are a friendly, concise marathon coach. Answer the runner's question "
        "in 3-4 sentences. Be specific and practical. No preamble. If the runner "
        "mentions a goal time, call pace_splits for exact paces — never do the "
        "arithmetic yourself."
    ),
)


# [harness]
def _event_text(event) -> str | None:
    """Pull human-readable text out of an event, whichever field carries it."""
    if getattr(event, "message", None) and getattr(event.message, "parts", None):
        chunks = [p.text for p in event.message.parts if getattr(p, "text", None)]
        if chunks:
            return "".join(chunks)
    out = getattr(event, "output", None)
    return out if isinstance(out, str) else None


async def ask(question: str) -> None:
    # 2) A Runner executes the agent inside a session and streams back events.
    runner = Runner(
        node=pace_coach,
        app_name="l0_first_agent",
        session_service=InMemorySessionService(),
        auto_create_session=True,
    )

    # 3) Wrap the user's question as a Content message and run.
    message = gtypes.Content(role="user", parts=[gtypes.Part(text=question)])
    print(f"\n🏃 You: {question}\n")
    print("🧠 Coach: ", end="", flush=True)
    async for event in runner.run_async(
        user_id="runner_1",
        session_id="session_1",
        new_message=message,
    ):
        for part in (getattr(getattr(event, "message", None), "parts", None) or []):
            fc = getattr(part, "function_call", None)
            if fc:
                print(f"\n   🔧 model called tool → {fc.name}({dict(fc.args) if fc.args else ''})")
            fr = getattr(part, "function_response", None)
            if fr:
                print(f"   🔧 tool returned     → {fr.response}\n🧠 Coach: ", end="", flush=True)
        text = _event_text(event)
        if text:
            print(text, end="", flush=True)
    print("\n")


def main() -> None:
    question = " ".join(sys.argv[1:]) or "I want to finish in 3:30:00 — what pace do I need, and how should I run the first 5k?"
    asyncio.run(ask(question))


if __name__ == "__main__":
    main()
