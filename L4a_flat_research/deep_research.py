"""L4a · Runtime-sized parallel fan-out (Pillar 3, part 1 of 2).

The first half of a dynamic workflow. An open-ended question is DECOMPOSED into
N sub-questions — N is chosen by the LLM at runtime (3-7) — then each is
researched IN PARALLEL, and the findings are synthesized. The tree is one level
deep: no recursion yet. L4b adds recursive spawning.

    START ─► decompose ─► research_topic (parallel_worker) ─► synthesize
                                 │  │  │
                                 └──┴──┴─ (flat: no children)

This already shows what a fixed graph can't: the WIDTH of the fan-out is decided
at runtime. L4b will make the DEPTH runtime too.

Run it:
    python -m L4a_flat_research.deep_research
    python -m L4a_flat_research.deep_research "How should I train for my first marathon in 6 months?"

NOTE: makes several live LLM calls (5-9: 1 decompose + 3-7 research + 1 synthesize).
Costs real API quota.
"""
from __future__ import annotations

import asyncio
import json
import os
import sys
import time

from dotenv import load_dotenv

from google.adk import Agent, Event, Runner, Workflow
from google.adk.workflow import RetryConfig, START, node
from google.adk.sessions import InMemorySessionService
from google.genai import types as gtypes

from shared import DecomposerOutput, DeepResearchBriefing, ResearchFinding

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


# ─── Three single-turn agents: decompose, research, synthesize. ───────────────

decompose_agent = Agent(
    name="decompose_agent", model=MODEL,
    output_schema=DecomposerOutput,
    instruction="""You are a research coordinator for marathon/endurance questions.
Break the user's open-ended question into 3-7 specific, non-overlapping,
independently-researchable sub-questions, each covering a distinct angle.""",
)

research_agent = Agent(
    name="research_agent", model=MODEL,
    output_schema=ResearchFinding,
    instruction="""You are a marathon research specialist. Given ONE specific
research question, produce a finding: a 2-3 sentence summary and 3-5 specific
insights. (For this level, keep needs_deeper=False.)""",
)

synthesize_agent = Agent(
    name="synthesize_agent", model=MODEL,
    output_schema=DeepResearchBriefing,
    instruction="""You are a marathon coach synthesizing a JSON list of findings
into one briefing for the runner: a HEADLINE, 3-6 thematic SECTIONS with specific
facts, 2-4 KEY_WARNINGS, and a closing SUMMARY. Write for the runner, be direct.""",
)


def _coerce(payload, schema_cls):
    if isinstance(payload, schema_cls):
        return payload
    if isinstance(payload, dict):
        return schema_cls.model_validate(payload)
    if isinstance(payload, str):
        return schema_cls.model_validate_json(payload)
    if hasattr(payload, "parts") and payload.parts:
        text = getattr(payload.parts[0], "text", None)
        if text:
            return schema_cls.model_validate_json(text)
    raise ValueError(f"Cannot coerce {type(payload).__name__} into {schema_cls.__name__}")


def _extract_text(node_input):
    if isinstance(node_input, str):
        return node_input
    if hasattr(node_input, "parts") and node_input.parts:
        return getattr(node_input.parts[0], "text", None) or str(node_input)
    return str(node_input)


# ─── Node 1: decompose into a runtime-sized list of sub-questions. ────────────

@node(rerun_on_resume=True)
async def decompose(ctx, node_input):
    user_query = _extract_text(node_input)
    plan = _coerce(await ctx.run_node(decompose_agent, node_input=user_query), DecomposerOutput)
    print(f"  [decompose] {len(plan.sub_questions)} sub-questions (width chosen at runtime):")
    for q in plan.sub_questions:
        print(f"    • {q[:80]}")
    yield Event(output=[{"question": q, "original_query": user_query} for q in plan.sub_questions])


# ─── Node 2: parallel_worker — one research task per item. Flat (no recursion). ─

# ─── Bounding the RATE, not just the shape. ───────────────────────────────────
#
# The fan-out width is already bounded by the schema (max_length=7). This bounds
# how it FAILS: a parallel worker cancels every sibling and re-raises the moment
# one child raises, so without a retry a single transient 429 throws away a whole
# run — including every call you already paid for. `retry_config` is applied to
# the INNER per-item node, so each branch retries on its own and a transient blip
# is absorbed before it can take the others down.
#
# Note `max_concurrency` is a real field on the parallel worker but is NOT
# reachable through the public `node()` API in ADK 2.3.0 — so on a rate-limited
# key, the schema bound is what keeps the in-flight count sane.
RESEARCH_RETRY = RetryConfig(max_attempts=3, initial_delay=2.0, backoff_factor=2.0)

# ★ parallel_worker: one worker per list item — and the list's SIZE arrives at runtime.
#   There is no dynamic=True switch anywhere; this flag and ctx.run_node ARE dynamic.
@node(parallel_worker=True, rerun_on_resume=True,
      retry_config=RESEARCH_RETRY)
async def research_topic(ctx, node_input):
    question = node_input["question"]
    ctxq = node_input.get("original_query", "")
    print(f"  [research] {question[:70]}")
    finding = _coerce(await ctx.run_node(
        research_agent,
        node_input=f"ORIGINAL QUERY: {ctxq}\n\nRESEARCH QUESTION: {question}",
    ), ResearchFinding)
    yield Event(output={"question": question, "summary": finding.summary, "key_facts": finding.key_facts})


# ─── Node 3: synthesize the flat list of findings. ────────────────────────────

@node(rerun_on_resume=True)
async def synthesize(ctx, node_input):
    print(f"  [synthesize] merging {len(node_input)} findings")
    briefing = _coerce(await ctx.run_node(
        synthesize_agent, node_input=json.dumps(node_input, indent=2)), DeepResearchBriefing)
    yield Event(output={"briefing": briefing.model_dump(), "findings": node_input})


l4a_workflow = Workflow(
    name="l4a_flat_research",
    description="Decompose (runtime width) → flat parallel research → synthesize.",
    edges=[(START, decompose, research_topic, synthesize)],
)


# [harness]
async def run(query="Tell me everything I should know about racing the Boston Marathon."):
    print(f"=== L4a · flat research ===\n  QUERY: {query}\n")
    runner = Runner(node=l4a_workflow, app_name="l4a", session_service=InMemorySessionService(), auto_create_session=True)
    t0 = time.perf_counter()
    final = None
    async for event in runner.run_async(
        user_id="u1", session_id="s1",
        new_message=gtypes.Content(role="user", parts=[gtypes.Part(text=query)]),
    ):
        out = getattr(event, "output", None)
        if isinstance(out, dict) and "briefing" in out:
            final = out
    if final:
        b = final["briefing"]
        print(f"\n  {len(final['findings'])} sub-questions researched in parallel | {time.perf_counter()-t0:.1f}s")
        print(f"\n📋 {b['headline']}\n")
        for i, s in enumerate(b["sections"], 1):
            print(f"  {i}. {s[:180]}")


if __name__ == "__main__":
    asyncio.run(run(" ".join(sys.argv[1:]) or "Tell me everything I should know about racing the Boston Marathon — course, weather, pitfalls, pacing, and what to wear."))
