"""L0 · Your first ADK 2 agent.

The smallest possible ADK 2 program: ONE agent, ONE Runner, ONE question.
No workflows, no schemas, no sub-agents yet — just prove the setup works and
you can get a model to answer.

    Agent  → the thing that reasons (wraps a Gemini model + an instruction)
    Runner → the thing that executes an agent inside a session and streams events

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

# 1) Define an agent — a model plus a role. That's it.
pace_coach = Agent(
    name="pace_coach",
    model=MODEL,
    instruction=(
        "You are a friendly, concise marathon coach. Answer the runner's question "
        "in 3-4 sentences. Be specific and practical. No preamble."
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
        text = _event_text(event)
        if text:
            print(text, end="", flush=True)
    print("\n")


def main() -> None:
    question = " ".join(sys.argv[1:]) or "I'm running my first marathon in 6 weeks. What's the single most important thing to get right?"
    asyncio.run(ask(question))


if __name__ == "__main__":
    main()
