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
The strategy cites real numbers, and the wall time is near the *slowest* fetch (~2s) rather than the sum (~4.5s) — the three fetches ran concurrently.

## What's new vs L1
- **Parallel edges:** three `(START, fetch_*, join_inputs)` edges fan out from `START`.
- **`JoinNode`** waits for all three and bundles them into one payload (`BundledRunData`), keyed by function name.
- One `strategy` agent (`input_schema=BundledRunData`, `output_schema=RaceStrategy`) reads the bundle.

→ **Next:** [L2b](../L2b_router/) adds the deterministic router that picks a *specialized* agent per condition.
