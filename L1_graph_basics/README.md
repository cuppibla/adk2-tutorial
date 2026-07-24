# L1 · Your first Workflow — function node + agent node

**The question:** how do you mix plain code and an LLM in one flow, without paying for a model call on the parts that are just code?

**The one idea:** in an ADK 2 `Workflow`, a **plain Python function and an LLM agent are both just nodes** in the same `edges` list.

```
START ──► fetch_conditions (function, 0 LLM) ──► advise (agent, 1 LLM)
```

Predictable work (fetching, parsing, math) stays a **function** and costs zero LLM calls. Only the reasoning step is an **agent**.

## Run it
```bash
python -m L1_graph_basics.workflow
```

## What you'll see
`fetch_conditions` prints the canned data it produced (no model call), then `advise` gives gear + pacing advice that references the actual temperature and wind it received.

## What's new vs L0
- **`Workflow(name=, description=, edges=[(START, fetch_conditions, advise)])`** — an edge chain. `START` is where input enters.
- A **function node** returns its result wrapped in `Event(output=...)`.
- The agent has **`input_schema=Conditions`** so the function node's output is **validated** against that schema at the node boundary. Note what it is *not*: downstream nodes get a plain **dict** (an agent node gets it as JSON text), which is why L2b's router reads `node_input["fetch_weather"]["temp_f"]` and not `node_input.fetch_weather`.

→ **Next:** [L2a](../L2a_parallel_join/) grows this into **Pillar 1** — three functions in *parallel* and a `JoinNode` — then [L2b](../L2b_router/) adds a deterministic router.
