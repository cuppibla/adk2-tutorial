# L5 · Capstone — which pattern, and how they compose

You've now built all three orchestration patterns. This level has no new code — it's the mental model that makes them useful: **match the pattern to the shape of your problem.**

## The one question that picks the pattern

```
Can you draw the workflow before the input arrives?
│
├─ YES ─────────────────────────────► Pillar 1 · Graph workflow      (L2a/L2b)
│                                      known structure
│
└─ NO
   │
   ├─ Known team, request picks the subset? ─► Pillar 2 · Collaborative   (L3)
   │                                            known team, variable subset
   │
   └─ Does the shape itself depend on input? ─► Pillar 3 · Dynamic         (L4a/L4b)
                                                unknown shape
```

- **Draw it ahead of time?** → **graph workflow.** The structure is known; make it visible, testable, composable structure instead of prose in a prompt.
- **Known team, request decides the subset?** → **collaborative agents.** You have the specialists; let the coordinator pick who answers.
- **Shape depends on the input?** → **dynamic workflow.** Let the LLM shape the work at runtime; keep the boundaries (depth, width, budget) in code.

## The 1.x-vs-2 honest framing

This is **not** "2.0 can do things 1.x couldn't" — 1.x could build all of it. The shift is that **2.0 gives each shape a more direct home**, so known control flow leaves the prompt and becomes structure you can see and test.

| Pattern | The common 1.x way | What it cost you | The ADK 2 home |
|---|---|---|---|
| **Graph** (L2a/L2b) | most builds wrapped each step as an `LlmAgent` (a `BaseAgent` subclass could avoid it, but you wrote the plumbing) | **4 LLM calls** in the common version, and routing hidden in a prompt | function nodes + agent nodes as peers → **1 LLM call**, `if`-statement router |
| **Collaborative** (L3) | wrap each specialist in `AgentTool` and let the coordinator call them (`ParallelAgent` is always-all; `transfer_to_agent` is serial) | the shape worked, but as hand-assembled tool plumbing rather than a declared team | `sub_agents` + `mode="single_turn"` — the subset and its parallelism are **declared**, not assembled |
| **Dynamic** (L4a/L4b) | `ParallelAgent` (fixed list), `LoopAgent` (serial), or raw `asyncio` | recursion was buildable, but it dropped you out of the framework (lose tracing/checkpointing) | `parallel_worker` + recursive `ctx.run_node`, all inside the framework |

## They compose

The three patterns are **not mutually exclusive**. A graph node can call a collaborative coordinator; a specialist can launch a dynamic workflow. **Choose the right pattern per *part* of the problem**, not one for the whole app — that's how you avoid turning every agent system into one giant prompt.

## The lines worth remembering

> *Predictable work stays as functions; clear rules become explicit routing; reasoning uses the model.*
>
> *Functions prepare the context. Edges define the workflow. The router chooses the path. The model writes the answer.*
>
> *Let the LLM shape the work, but keep the boundaries in code.*
>
> *Match the pattern to the shape of your problem.*

## Where to go next
- Re-run any level with a different scenario (`MARATHON_SCENARIO=COLD python -m L2b_router.workflow`) or a different question (`python -m L3_collaborative.concierge "what about fueling?"`) and watch the shape change.
- Try porting your OWN problem: which parts are known-structure (L2a/L2b), which are known-team (L3), which are unknown-shape (L4a/L4b)?
