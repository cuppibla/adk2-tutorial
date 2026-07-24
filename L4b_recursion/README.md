# L4b · Add recursive spawning (Pillar 3, part 2 of 2)

**The question:** one finding sometimes surfaces a narrow sub-topic worth its own investigation. How do you let a branch **spawn more parallel work** — and keep it bounded?

**The shape (now recursive):**
```
START ─► decompose ─► research_topic (parallel_worker, recursive) ─► synthesize
                             │  │  │
                             │  │  └─ research(q3) ─► maybe spawn children
                             │  └─── research(q2) ─► maybe spawn children
                             └────── research(q1) ─► maybe spawn children
```

## Run it
```bash
python -m L4b_recursion.deep_research
python -m L4b_recursion.deep_research "What are the most common mistakes new marathoners make?"
```
> ⚠️ 5–30 live LLM calls, 20–45s. Run it deliberately — the ceiling is 1 decompose + 7 top-level + 7×3 children + 1 synthesize.

## What you'll see
Research nodes printing `spawning N deeper` — recursion happening live — then a runtime tree shape (e.g. `5 top-level + 10 recursive children`) and a synthesized briefing. The tree differs every run.

## What's new vs L4a
- **`ctx.run_node(research_topic, [...])`** — a running worker recursively spawns more parallel work, **inside the framework** (tracing, checkpointing, resumability preserved).
- The finding schema gains `needs_deeper` + `deeper_questions`.

> **The rule:** *let the LLM shape the work, but keep the boundaries in code.* `MAX_DEPTH = 2` means depth-2 children cannot spawn — there is no depth 3.

> ⚠️ **Before you raise it:** the ceiling grows fast — `MAX_DEPTH=3` takes the worst case from ~30 calls to ~93. The run summary also only counts children one level down, so it will under-report past depth 2.

> **Where ADK 2 gives this a direct home:** recursion was always buildable in 1.x — but only by dropping out to raw `asyncio`, which cost you the framework machinery (tracing, checkpointing) for exactly the part of the system that needed it most.

> You may see `cancelling N leftover tasks` at the end — ADK tearing down its parallel task group. Harmless.

→ **Next:** [L5](../L5_capstone/) — when to reach for which pattern, and how they compose.
