"""L4b · Add recursive spawning (Pillar 3, part 2 of 2).

L4a fanned out a runtime-sized list, one level deep. Now each research finding
may RECURSIVELY spawn 1-3 deeper questions via `ctx.run_node(research_topic, ...)`
— so the tree's DEPTH is also decided by the LLM at runtime. The boundary stays
in code: MAX_DEPTH.

    START ─► decompose ─► research_topic (parallel_worker, recursive) ─► synthesize
                                 │  │  │
                                 │  │  └─ research(q3) ─► maybe spawn children
                                 │  └─── research(q2) ─► maybe spawn children
                                 └────── research(q1) ─► maybe spawn children

What's uniquely ADK 2: recursive parallel fan-out INSIDE the framework, so you keep
tracing, checkpointing, and resumability. In 1.x, real recursion forces you to
drop out to raw asyncio and lose all of it. The rule: let the LLM shape the work,
but keep the boundaries in code.

Run it:
    python -m L4b_recursion.deep_research
    python -m L4b_recursion.deep_research "How should I train for my first marathon in 6 months?"

NOTE: makes MANY live LLM calls (5-30) and takes 20-45s. Costs real API quota.
Ceiling = 1 decompose + 7 top-level + 7*3 children + 1 synthesize.
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
_vertex = os.getenv("GOOGLE_GENAI_USE_VERTEXAI", "").lower() in ("true", "1", "yes")
if not (os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY") or _vertex):
    sys.exit(
        "\u2717 No API key found.\n"
        "  cp .env.example .env  then add GOOGLE_API_KEY=...\n"
        "  Get a free key at https://aistudio.google.com/apikey\n"
        "  (On GCP: export GOOGLE_GENAI_USE_VERTEXAI=True + GOOGLE_CLOUD_PROJECT instead.)"
    )
# [/local-only]


MODEL = os.getenv("ADK_MODEL", "gemini-flash-latest")   # AI Studio alias; on Vertex set ADK_MODEL=gemini-2.5-flash

# The boundary kept in CODE. The LLM decides width and depth, but never past this.
MAX_DEPTH = 2


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
research question, produce a 2-3 sentence summary and 3-5 insights. Set
needs_deeper=True ONLY if your findings surface a genuinely narrow technical
sub-topic that deserves its own investigation; then give 1-3 specific
deeper_questions.""",
)

synthesize_agent = Agent(
    name="synthesize_agent", model=MODEL,
    output_schema=DeepResearchBriefing,
    instruction="""You are a marathon coach synthesizing a nested JSON tree of
findings into one briefing: a HEADLINE, 3-6 SECTIONS combining related findings
with specific facts, 2-4 KEY_WARNINGS, and a closing SUMMARY. Write for the runner.""",
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


@node(rerun_on_resume=True)
async def decompose(ctx, node_input):
    user_query = _extract_text(node_input)
    plan = _coerce(await ctx.run_node(decompose_agent, node_input=user_query), DecomposerOutput)
    print(f"  [decompose] {len(plan.sub_questions)} sub-questions (width chosen at runtime):")
    for q in plan.sub_questions:
        print(f"    • {q[:80]}")
    yield Event(output=[{"question": q, "depth": 1, "original_query": user_query} for q in plan.sub_questions])


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

@node(parallel_worker=True, rerun_on_resume=True,
      retry_config=RESEARCH_RETRY)
async def research_topic(ctx, node_input):
    question = node_input["question"]
    depth = node_input["depth"]
    ctxq = node_input.get("original_query", "")
    print(f"  [research d={depth}] {question[:66]}")
    finding = _coerce(await ctx.run_node(
        research_agent,
        node_input=f"ORIGINAL QUERY: {ctxq}\n\nRESEARCH QUESTION: {question}",
    ), ResearchFinding)

    children = []
    # ★ the brake — YOU wrote the recursion below, so YOU write its boundary.
    if finding.needs_deeper and finding.deeper_questions and depth < MAX_DEPTH:
        deeper = [{"question": dq, "depth": depth + 1, "original_query": ctxq}
                  for dq in finding.deeper_questions]
        print(f"  [research d={depth}] spawning {len(deeper)} deeper (depth chosen at runtime)")
        children = await ctx.run_node(research_topic, node_input=deeper)   # ★ calls ITSELF — ordinary Python recursion, no framework magic

    yield Event(output={"question": question, "depth": depth, "summary": finding.summary,
                        "key_facts": finding.key_facts, "children": children})


@node(rerun_on_resume=True)
async def synthesize(ctx, node_input):
    print(f"  [synthesize] merging {len(node_input)} top-level findings + their children")
    briefing = _coerce(await ctx.run_node(
        synthesize_agent, node_input=json.dumps(node_input, indent=2)), DeepResearchBriefing)
    yield Event(output={"briefing": briefing.model_dump(), "research_tree": node_input})


l4b_workflow = Workflow(
    name="deep_research",
    description="Decompose → recursive parallel research → synthesize.",
    edges=[(START, decompose, research_topic, synthesize)],
)


# [harness]
async def run(query="Tell me everything I should know about racing the Boston Marathon."):
    print(f"=== L4b · recursive deep research ===\n  QUERY: {query}\n")
    runner = Runner(node=l4b_workflow, app_name="l4b", session_service=InMemorySessionService(), auto_create_session=True)
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
        tree = final["research_tree"]
        top = len(tree)
        deeper = sum(len(n.get("children", [])) for n in tree)
        b = final["briefing"]
        print(f"\n  Tree (runtime-decided): {top} top-level + {deeper} recursive children | {time.perf_counter()-t0:.1f}s")
        print(f"\n📋 {b['headline']}\n")
        for i, s in enumerate(b["sections"], 1):
            print(f"  {i}. {s[:180]}")


if __name__ == "__main__":
    asyncio.run(run(" ".join(sys.argv[1:]) or "Tell me everything I should know about racing the Boston Marathon — course, weather, pitfalls, pacing, and what to wear."))
