# L4a · Runtime-sized parallel fan-out (Pillar 3, part 1 of 2)

**The question:** the *shape* of the work depends on the input — you can't draw the graph ahead of time. Start with runtime **width**: let the LLM decide *how many* sub-questions.

**The shape (one level deep):**
```
START ─► decompose ─► research_topic (parallel_worker) ─► synthesize
                             │  │  │
                             └──┴──┴─ (flat: no children)
```
An open-ended question is **decomposed** into N sub-questions — **N is chosen at runtime** (3–7) — each **researched in parallel**, then **synthesized**.

## Run it
```bash
python -m L4a_flat_research.deep_research
python -m L4a_flat_research.deep_research "How should I train for my first marathon in 6 months?"
```
> ⚠️ ~7–9 live LLM calls, ~20–30s. Costs real API quota.

## What you'll see
The decomposer prints e.g. 5 sub-questions, they research in parallel, then a synthesized briefing. The *number* differs every run — a fixed graph couldn't do that.

## What's new
- **`@node(parallel_worker=True)`** — one worker definition, fanned out across a runtime-sized list.
- The decomposer's `sub_questions` schema is bounded (`min_length=3, max_length=7`).

> **Uniquely ADK 2 (so far):** a 1.x `ParallelAgent` needs a fixed list known at build time; here the list size is decided at runtime.

→ **Next:** [L4b](../L4b_recursion/) makes the *depth* runtime too — branches recursively spawn their own deeper questions.
