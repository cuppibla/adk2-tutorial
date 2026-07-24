# L3 · Pillar 2 — collaborative agents (dynamic subset, run in parallel)

**The question:** you know the **team**, but the **request** decides which members should answer. How do you let an LLM pick the subset — and run them concurrently?

**The shape:**
```
race_concierge (coordinator)
  ├─ medical    ├─ gear
  ├─ weather    ├─ nutrition
  ├─ pacing     └─ mental
```
The coordinator reads the question, picks the relevant specialists, ADK runs the chosen ones **in parallel** (multiple function calls in one turn), then **synthesizes** one answer.

| Question | Specialists that fire |
|---|---|
| "What about fueling?" | nutrition only |
| "My knee hurts at mile 18" | medical only |
| "Should I race today?" | medical + weather + pacing |
| "Anything I should worry about?" | all 6 |

## Run it
```bash
python -m L3_collaborative.concierge
python -m L3_collaborative.concierge "My left knee twinges at mile 18 — safe to keep going?"
python -m L3_collaborative.concierge "Anything I should worry about overall?"
```

## What you'll see
`DISPATCH → medical_specialist` lines show exactly which subset the coordinator chose, then a single synthesized answer. Ask two different questions and watch the subset change — that contrast *is* the lesson.

## Where ADK 2 gives this a direct home
- **`Agent(sub_agents=[...])`** — a coordinator over specialists declared **`mode="single_turn"`**.
- The coordinator picks a **per-request subset** and ADK runs it **in parallel**.
- **Honest about 1.x:** you could build this shape there by wrapping each specialist in `AgentTool` — the LLM picked the subset and 1.x already dispatched multiple function calls in one turn concurrently. What ADK 2 changes is that the team becomes **declarative**: `sub_agents` plus one `mode` argument, instead of hand-assembled tool plumbing. (`ParallelAgent` is always-all and `transfer_to_agent` is serial — those were never the right tool for this.)

**Three honest caveats:**
- The run opens with `UserWarning: [EXPERIMENTAL] feature FeatureName.JSON_SCHEMA_FOR_FUNC_DECL is enabled` — ADK flagging that the specialists' pydantic `input_schema` uses its experimental JSON-schema path for tool declarations. Harmless, once per run.
- The model picks the subset, so it's **less deterministic** than L2's hard-coded router. The exact subset can vary run to run.
- Occasionally you'll see an `Error validating input: ...` line for one specialist. It is almost never the specialist's *output* — `output_schema` makes Gemini enforce that server-side. It's the **input**: the coordinator has to reproduce the whole nested `SpecialistInput` verbatim for every parallel call, and sometimes it fumbles one. ADK returns the error as that tool's result, the coordinator recovers, and the synthesis still lands. LLM nondeterminism, not a bug in the flow.

→ **Next:** [L4a](../L4a_flat_research/) — when even the *shape* of the work is unknown until runtime (then [L4b](../L4b_recursion/) makes it recursive).
