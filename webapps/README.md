# Clicking through the levels in `adk web`

The levels were written for the CLI. This directory holds thin adapters that
make them usable in a browser, without changing a line of the teaching code.

## Start it

```bash
./run.sh
```

That's it — the script activates `.venv`, then runs `adk web webapps` on
**http://localhost:8080**. Open that, pick a level from the dropdown at the
top-left, and type in the chat box.

To stop it: `Ctrl-C` in the terminal.

<details>
<summary>What <code>./run.sh</code> actually runs</summary>

```bash
adk web webapps --session_service_uri "sqlite:///$HOME/.adk/sessions/adk_web_sessions.db" \
                --host localhost --port 8080 --reload
```

The `webapps` argument matters — see [Why this layer exists](#why-this-layer-exists).
</details>

**Workshop credit?** `adk web` reads your local `.env`, so copy
`.env.workshop.example` → `.env` (the four Vertex variables), and run
`gcloud auth application-default login` once. Otherwise it uses the AI Studio
key in `.env` like everything else.

## What to type in each level

| Dropdown entry | Type this | What you should see |
| --- | --- | --- |
| **L0_pace_coach** | `I want to finish in 3:30:00 — what pace do I need?` | The model decides to call the pace tool. Then ask `What is the most common mistake first-time marathoners make?` — no numbers, so it skips the tool. That contrast is the level. |
| **L1_fetch_then_advise** | anything, e.g. `go` | `[fetch_conditions] (function node, 0 LLM)` then the agent's advice. This level has no inputs — a function and an agent as peers is the whole idea. |
| **L2a_fanout_join** | `COLD` (or `HOT` / `NORMAL`) | Three fetches whose timestamps **overlap**, one `JoinNode`, then a single LLM call. |
| **L2b_weather_router** | `COLD`, then run it again with `HOT` | `[router] temp=35.0°F → route=COLD  (an if-statement, 0 LLM)` — and a different branch on `HOT`. Same graph, different path, still one LLM call. **The best one to demo live.** |
| **L3a_concierge** | `my knee hurts, should I still race?` | The coordinator picks only the specialists that matter (medical + weather here) and runs them in parallel. Prefix with `COLD` to change the conditions they reason about. |
| **L3b_gear_desk** | `I need a hydration vest` → it asks your size → answer `medium` | `task` mode: the sub-agent pauses mid-task for a clarifying question, then finishes with a validated `GearOrder`. This one is *better* in the browser than in the CLI, where the answer has to be scripted. |
| **L4a_research_flat** | `What should I know about racing Boston?` | `decompose` picks N sub-questions **at runtime** (5 for that query), all researched in parallel. ⚠️ 5–9 LLM calls. |
| **L4b_research_recursive** | same question | Same, but branches spawn their own sub-branches — the tree's depth is the model's call, `MAX_DEPTH=2` in code is the limit. ⚠️ 5–30 LLM calls. |

`L5` has no agent — it's the reading level (the decision tree), so it isn't here.

## Why this layer exists

Point `adk web` at the repo root instead and three things go wrong:

1. **The chat box is really a Run button.** L1/L2a/L2b call
   `run_async(new_message=None)` — nothing you type reaches the graph. Verified:
   ask L1 *"what is the capital of France?"* and it answers about 78°F.
2. **The scenario is stuck on HOT** (`shared/scenarios.py` default), because the
   CLI takes it from `argv[1]` and `adk web` never calls `run()`. So L2b — a
   level whose entire subject is routing — only ever takes one branch.
3. **The teaching evidence goes to the server terminal**, not the browser. The
   parallel timestamps, the router's decision, the recursion trace are all
   `print()`. And `shared/` shows up in the dropdown as an agent that errors
   when picked, because it has an `__init__.py`.

Fixing that inside the levels was the wrong trade: L2a is a lesson about
fan-out, not about parsing user input, and turning its `print()`s into events
would wreck the CLI output the codelab is built around. So the levels stay
untouched and the adapters handle it from outside — the typed message picks the
scenario, stdout is captured into the reply, and L3a gets the strategy + runner
data its CLI harness injects.

Two things worth knowing if you edit these:

- **A node may set its output only once.** `yield Event(output=…)` twice raises
  `ValueError`; the adapter builds one combined block.
- **L3a is not wrapped in a `Workflow` like the others.** Running a
  `single_turn` coordinator through `ctx.run_node` breaks in ADK 2.3.0 — its
  specialists are exposed as tools, and their function *responses* then hunt for
  their function *calls* in the wrapper's event stream:
  `ValueError: No function call event found for function responses ids`.
  `use_sub_branch=True` doesn't help. It uses a `before_model_callback` instead.

## This is for clicking, not for learning

The browser shows you *that* it happened. The CLI shows you *how*, with the
per-level output the codelab is written around:

```bash
python -m L2b_router.workflow COLD
python -m L3a_collaborative.concierge --mode chat "What about fueling?"   # beat 1 — no web equivalent
python -m L4b_recursion.deep_research
```

`--mode chat` in particular has no browser equivalent: watching that run strand
itself is the point, and in a browser it just looks like a hang.
