# L5 · Capstone — which pattern, and how they compose

You've now built all three orchestration patterns. This level has no new code — it's the mental model that makes them useful: **match the pattern to the shape of your problem.**

## The axis: who decides what runs next?

That's the one question the three pillars actually answer. Everything else follows from it:

| Pillar | Who decides what runs next | Built in |
|---|---|---|
| **1 · Graph** | **the graph you drew** | L2a / L2b |
| **2 · Collaborative** | **the LLM** | L3 |
| **3 · Dynamic** | **your Python code, at runtime** | L4a / L4b |

## Step 0: do you even need a graph?

Before any of this — ADK ships **prebuilt workflow agents**: `SequentialAgent`, `ParallelAgent`, `LoopAgent`. For a plain chain of agents, or "run these three and wait," those are the cheapest correct answer and there's no graph to assemble.

Reach past them when you need something they don't give you: **explicit routing** (L2b's `if`-statement router), a **join** that bundles parallel outputs into one typed payload (L2a's `JoinNode`), or **nodes that aren't agents** (a plain Python function, costing zero LLM calls). That last one is usually the reason.

This lab starts at graphs because the whole point is what explicit structure buys you — but "just use a `SequentialAgent`" is a real and often better answer, and a decision tree that omits it is selling you a graph you may not need.

## Then: the one question that picks the pattern

```
Would a prebuilt SequentialAgent / ParallelAgent / LoopAgent do?
│
├─ YES ──────────────────────────────► use it; stop here
│
└─ NO — I need routing, a join, or non-agent nodes
   │
   Can you draw the workflow before the input arrives?
   │
   ├─ YES ───────────────────────────► Pillar 1 · Graph workflow    (L2a/L2b)
   │                                    the graph decides
   │
   └─ NO
      │
      ├─ Known team, request picks the subset? ─► Pillar 2 · Collaborative  (L3)
      │                                            the LLM decides
      │
      └─ Does the shape itself depend on input? ─► Pillar 3 · Dynamic       (L4a/L4b)
                                                   your code decides
```

- **Draw it ahead of time?** → **graph workflow.** The structure is known; make it visible, testable, composable structure instead of prose in a prompt.
- **Known team, request decides the subset?** → **collaborative agents.** You have the specialists; let the coordinator pick who answers.
- **Shape depends on the input?** → **dynamic workflow.** Let your code shape the work at runtime; keep the boundaries (depth, width, budget) in code.

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

## What this lab did NOT teach you

Eight rungs, one app, ~30 minutes — so the scope is deliberate. Three things you'll meet in real ADK 2 work that aren't here:

- **Loops.** The lab does runtime *width* (L4a) and *depth* (L4b), but never iteration. The canonical dynamic-workflow shape is generate → review → fix in a `while` loop, and it's arguably the one you'll build most. → [`07_loop`](https://github.com/cuppibla/adk-workflows-compared/tree/main/examples/07_loop), [`08_loop_self`](https://github.com/cuppibla/adk-workflows-compared/tree/main/examples/08_loop_self)
- **Human input.** Pausing a workflow for approval via `RequestInput` — nothing here does it. → [`17_request_input`](https://github.com/cuppibla/adk-workflows-compared/tree/main/examples/17_request_input)
- **Resumability, actually demonstrated.** L4b *tells* you recursion stays inside the framework so you keep tracing and checkpointing — true, but you never see it interrupt and resume. Take that one on faith here, and go watch it work elsewhere.

Also: only one of the three collaboration modes (`single_turn`) runs in this lab — see [L3](../L3_collaborative/).

All of the above live in the companion repo, [**adk-workflows-compared**](https://github.com/cuppibla/adk-workflows-compared): 23 official ADK 2 samples, each with a 1.x port and when-to-use guidance.

## Where to go next
- Re-run any level with a different scenario (`MARATHON_SCENARIO=COLD python -m L2b_router.workflow`) or a different question (`python -m L3_collaborative.concierge "what about fueling?"`) and watch the shape change.
- Try porting your OWN problem: which parts are known-structure (L2a/L2b), which are known-team (L3), which are unknown-shape (L4a/L4b)?
