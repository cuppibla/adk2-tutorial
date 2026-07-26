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

> ⚠️ **If you add a fourth branch,** give the route-dict a `DEFAULT_ROUTE` entry too. A route the dict doesn't match isn't an error — the branch simply ends, and the program exits **0 with no output**, which is a confusing dead end to debug.

> **Where ADK 2 gives this a direct home:** 1.x could reach 1 call too — via a custom `BaseAgent` subclass — but only if you wrote the orchestration plumbing yourself, so most builds wrapped each step as an agent and paid 4. Here a plain function and an `if`-statement are first-class nodes.

→ **Next:** [L3a](../L3a_collaborative/) — when the *request* (not you) decides which specialists run.
