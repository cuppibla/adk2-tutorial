# L2a · Parallel fan-out + JoinNode (Pillar 1, part 1 of 2)

**The question:** you can *draw the flow before the input arrives*. Start with the skeleton — gather data in parallel, bundle it, hand it to one agent.

**The shape:**
```
START ──► fetch_weather ──┐
START ──► analyze_course ─┼─► JoinNode ─► strategy (1 agent)
START ──► pull_fitness ───┘   (bundles)
```

## Run it
```bash
python -m L2a_parallel_join.workflow          # HOT
python -m L2a_parallel_join.workflow COLD
```
Slow the fetches to *watch* the parallelism: `MARATHON_SLOW_MO=3 python -m L2a_parallel_join.workflow`.

## What you'll see
Each fetch prints when it **starts** and **finishes**:

```
  [t= 0.0s] fetch_weather started
  [t= 0.0s] analyze_course started
  [t= 0.0s] pull_fitness started
  [t= 1.0s] pull_fitness finished
  [t= 1.5s] fetch_weather finished
  [t= 2.0s] analyze_course finished
```

All three start at **0.0s** and the fan-out is done at **2.0s** — the slowest fetch, not the **4.5s** their durations would add up to. That overlap *is* the parallelism.

Then the strategy cites real numbers from the bundle. The **total wall time** printed at the end is larger (~8s) because it also contains the strategy agent's LLM call — read the fetch timestamps, not the total, for the parallel claim.

## What's new vs L1
- **Parallel edges:** three `(START, fetch_*, join_inputs)` edges fan out from `START`.
- **`JoinNode`** waits for all three and bundles them into one payload (`BundledRunData`), keyed by function name.
- One `strategy` agent (`input_schema=BundledRunData`, `output_schema=RaceStrategy`) reads the bundle.

→ **Next:** [L2b](../L2b_router/) adds the deterministic router that picks a *specialized* agent per condition.
