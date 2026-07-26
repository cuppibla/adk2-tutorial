# L3a · Pillar 2 — collaborative agents: one flag, two worlds

**The question:** you know the **team**, but the **request** decides which members should answer. How do you let an LLM pick the subset — and run them concurrently?

**The shape:**
```
race_concierge (coordinator)
  ├─ medical    ├─ gear
  ├─ weather    ├─ nutrition
  ├─ pacing     └─ mental
```

This level runs the **same team twice** — same coordinator prompt, same six specialists. The only difference is one flag on the subagents. The contrast *is* the lesson.

## Beat 1 · Run the default first — and watch it fail the job

```bash
python -m L3a_collaborative.concierge --mode chat "What about fueling?"
```

No `mode=` written → subagents default to **`chat`**. What you'll see:

```
TRANSFER → nutrition_specialist   (transfer_to_agent — the only tool chat subagents provide)
Final speaker: nutrition_specialist
```

The coordinator got **no delegation tools** — chat subagents only give it `transfer_to_agent`, a serial handoff of the *whole conversation* to **one** specialist. That specialist answers the user directly, and the run ends there. No parallel dispatch. No return. No synthesis. Ask the broad question and it gets worse: six specialists, one transfer.

That's not a bug — it's chat mode doing its job. The conversation *belongs* to whoever holds it, until someone explicitly transfers away. Right for an open-ended assistant; wrong for a pipeline step.

## Beat 2 · One flag, two worlds

```bash
python -m L3a_collaborative.concierge "Anything I should worry about overall?"
```

The only diff in the code: `mode="single_turn"` on each specialist. What you'll see:

```
[t= 7.8s] DISPATCH → medical_specialist      ← same timestamp =
[t= 7.8s] DISPATCH → weather_specialist         one turn, many calls
[t= 7.8s] DISPATCH → ...all six...
[t=14.5s]   ↩ medical_specialist replied     ← replies land inside
[t=14.5s]   ↩ ...all six...                     one short window
🧠 Concierge (synthesized): <one answer>
```

Now ADK injects **one delegation tool per specialist** (named after the subagent — and its `description=` is what the coordinator reads when choosing; skip it and you're routing on names alone). The coordinator emits several calls in one turn, ADK runs them **in parallel**, each auto-returns its result, and the coordinator synthesizes.

| Question | Specialists that fire |
|---|---|
| "What about fueling?" | nutrition only |
| "My knee hurts at mile 18" | medical only |
| "Should I race today?" | medical + weather + pacing |
| "Anything I should worry about?" | all 6 |

## Why each specialist gets handed the whole briefing

Each `single_turn` subagent runs in its **own isolated session branch**. While they run in parallel, a specialist sees only events from its own branch — it cannot see the conversation, or what its peers are saying. When all branches finish, the coordinator collects the results.

That isolation is why the coordinator has to forward the *entire* `SpecialistInput` — question, strategy, and runner data — separately into every parallel call. Nothing is ambient; each specialist gets a self-contained briefing or it gets nothing. It's also the reason for the input-validation caveat below: that briefing is a large nested object, and the coordinator has to reproduce it correctly once per specialist.

## Where ADK 2 gives this a direct home
- **Honest about 1.x:** you could build this shape there by wrapping each specialist in `AgentTool` — the LLM picked the subset and 1.x already dispatched multiple function calls in one turn concurrently. What ADK 2 changes is that the team becomes **declarative**: `sub_agents` plus one `mode` argument, instead of hand-assembled tool plumbing. (`ParallelAgent` is always-all and `transfer_to_agent` is serial — those were never the right tool for this.)

**Three honest caveats:**
- The run opens with `UserWarning: [EXPERIMENTAL] feature FeatureName.JSON_SCHEMA_FOR_FUNC_DECL is enabled` — ADK flagging that the specialists' pydantic `input_schema` uses its experimental JSON-schema path for tool declarations. Harmless, once per run.
- The model picks the subset, so it's **less deterministic** than L2's hard-coded router. The exact subset can vary run to run.
- Occasionally you'll see an `Error validating input: ...` line for one specialist. It is almost never the specialist's *output* — `output_schema` makes Gemini enforce that server-side. It's the **input**: the coordinator has to reproduce the whole nested `SpecialistInput` verbatim for every parallel call, and sometimes it fumbles one. ADK returns the error as that tool's result, the coordinator recovers, and the synthesis still lands. LLM nondeterminism, not a bug in the flow.

→ **Next:** [L3b](../L3b_task_desk/) — the third mode, `task`: a conversation with a finish line. Then [L4a](../L4a_flat_research/) — when even the *shape* of the work is unknown until runtime.
