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

## What's uniquely ADK 2
- **`Agent(sub_agents=[...])`** — a coordinator over specialists declared **`mode="single_turn"`**.
- The coordinator picks a **per-request subset** and ADK runs it **in parallel**. In 1.x, `ParallelAgent` is always-all and `transfer_to_agent` is serial — neither does dynamic-subset-in-parallel.

**Two honest caveats (LLMs are nondeterministic):**
- The model picks the subset, so it's **less deterministic** than L2's hard-coded router. The exact subset can vary run to run.
- Occasionally a specialist returns prose instead of clean JSON and you'll see a schema-validation warning in the logs — the coordinator recovers and still synthesizes. That's LLM nondeterminism, not a bug in the flow.

→ **Next:** [L4a](../L4a_flat_research/) — when even the *shape* of the work is unknown until runtime (then [L4b](../L4b_recursion/) makes it recursive).
