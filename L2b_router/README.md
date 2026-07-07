# L2b · Add the deterministic router (Pillar 1, part 2 of 2)

**The question:** the plan should differ for hot vs cold weather. How do you branch — *without* asking the model to decide?

**The shape (L2a + a router):**
```
… JoinNode ─► route_by_weather ─► hot_strategy
               (if-statement)   ─► normal_strategy
                                ─► cold_strategy
```

## Run it
```bash
python -m L2b_router.workflow          # HOT — Boston, 78°F
python -m L2b_router.workflow NORMAL   # Berlin, 58°F
python -m L2b_router.workflow COLD      # Chicago, 35°F
```

## What you'll see
`temp=78°F → route=HOT`, then a structured `RaceStrategy` from the matching agent. **Net cost: 1 LLM call.**

## The takeaway — three kinds of work, three homes
- Predictable work → **functions** (the 3 parallel fetches)
- A clear rule → **explicit routing** (`route_by_weather` is an `if`-statement, not a model decision)
- Reasoning → **the model** (exactly one strategy agent runs)

## What's new vs L2a
- A **router function** returns `Event(output=..., route="HOT")`.
- A **dict edge** `(route_by_weather, {"HOT": ..., "NORMAL": ..., "COLD": ...})` picks exactly one branch.
- Three **specialized** strategy agents replace L2a's single generic one.

> **Uniquely ADK 2:** the ADK 1.x way makes every node an agent, so each fetch needs its own model call — 4 calls instead of this pattern's 1.

→ **Next:** [L3](../L3_collaborative/) — when the *request* (not you) decides which specialists run.
