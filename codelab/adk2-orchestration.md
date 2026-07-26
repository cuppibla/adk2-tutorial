summary: Build a Marathon Race Day Coach and learn ADK 2's three orchestration patterns — graph workflows, collaborative agents, and dynamic workflows — one runnable level at a time.
id: adk2-orchestration
categories: AI, Agents, Google
environments: Web
status: Published
tags: adk, agents, orchestration, gemini
authors: Annie (cuppibla)
feedback link: https://github.com/cuppibla/adk2-tutorial/issues

# ADK 2 Orchestration: Graph, Collaborative & Dynamic Workflows

## Overview
Duration: 3

ADK 2's headline is **three orchestration patterns**. This codelab teaches all three by building one app — a **Marathon Race Day Coach** — one runnable rung at a time. Each level answers a single question, adds one idea, and runs on its own.

### What you'll learn

- **Graph workflows** (Pillar 1) — when you can *draw the flow before the input arrives*.
- **Collaborative agents** (Pillar 2) — when you know the *team* but the *request* picks the subset — and all **three collaboration modes** (`chat` / `task` / `single_turn`), each run live.
- **Dynamic workflows** (Pillar 3) — when the *shape of the work itself* depends on the input.
- **How to choose** — a one-question decision tree, and how the patterns compose.

### The through-line

> known structure → known team / variable subset → unknown shape → choose the right one

![Your learning roadmap](img/roadmap-L0.png)

### What you'll build

One app — a **Marathon Race Day Coach** — that shows all three orchestration patterns. Everything runs behind a FastAPI + SSE backend; each level below is one piece of it.

![Marathon Race Day Coach — architecture](img/diagram-arch.png)

### What you'll need

- A Google account (for Colab) — **no local setup required**.
- A free **Google AI Studio** API key: [aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey).
- ~30 minutes.

> aside positive
> **The mental model to hold onto:** *Predictable work stays as functions; clear rules become explicit routing; reasoning uses the model.* Every level is a variation on that one sentence.

### Two ways to follow along

Every step below maps to **one cell in the Colab notebook** and **one folder in the GitHub repo**. Pick either:

- **▶ Colab (recommended):** [Open the notebook](https://colab.research.google.com/github/cuppibla/adk2-tutorial/blob/main/notebooks/adk2_orchestration.ipynb) → run cells top to bottom.
- **💻 Local:** `git clone` the [repo](https://github.com/cuppibla/adk2-tutorial), `./setup_venv.sh`, then run each level as a module (`python -m …`) or browse them all with `./run.sh` (`adk web`).

## Setup & Authentication
Duration: 5

Everything runs on a free **Google AI Studio** API key — no Google Cloud project, no billing, no local install. This whole step is ~3 minutes.

### 1 · Open the notebook

Click **[Open in Colab ▶](https://colab.research.google.com/github/cuppibla/adk2-tutorial/blob/main/notebooks/adk2_orchestration.ipynb)**. You'll land on the notebook — a markdown intro, then one runnable cell per level. You run cells top to bottom; each prints its own output right below it.

> aside positive
> New to Colab? A **cell** is a block of code. Click it and press **Shift+Enter** (or the ▶ button on its left) to run it. Run them **in order** from the top.

### 2 · Install ADK 2  *(~1 min)*

Run the first code cell. It pins the exact version this codelab was verified on:

```bash
%pip install -q "google-adk==2.3.0" python-dotenv pydantic nest_asyncio
```

Wait for it to finish — you'll see `✓ installed`. (The install takes ~30–60s the first time; it's cached after that.)

> aside negative
> Verified on **2.3.0** and 2.0.0b1 — every API this codelab uses behaves identically on both. But the ADK 2 line is **not** frozen: `mode="task"` could not be a static workflow graph node on 2.0.0b1–2.3.0 and **can** on 2.5.0. This codelab never uses `task` mode, so the pin is safe — just don't assume "ADK 2.x" is one behavior surface.

### 3 · Get your Gemini API key from AI Studio  *(~1 min)*

1. Open **[aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey)** in a new browser tab.
2. Sign in with your Google account.
3. Click **Create API key** (top-right).
4. Pick an existing Google project or let it create one.
5. **Copy** the key — it starts with `AIza…` and is ~40 characters.

> aside negative
> **Treat the key like a password.** Don't paste it into public chats, screenshots, or commit it to a public repo. This notebook keeps it out of the code via Colab Secrets (below).

### 4 · Add your key to Colab  *(~1 min)*

**Option A — Colab Secrets (recommended; the key stays hidden):**

1. Click the **🔑 key icon** in the Colab left sidebar.
2. Click **+ Add new secret**.
3. Set **Name** to exactly `GOOGLE_API_KEY`.
4. Paste your key into **Value**.
5. Toggle **Notebook access** to **ON**.

**Option B — paste when prompted (quick):** skip the secret; when you run the next cell it shows a hidden prompt `🔑 Enter your Google AI Studio API key:` — paste and press Enter.

### 5 · Run the key cell

It reads the secret (or falls back to the paste prompt), then points ADK at **AI Studio** (not Vertex AI):

```python
import os

# Google AI Studio API key — add GOOGLE_API_KEY in the 🔑 Secrets panel (or paste when prompted).
try:
    from google.colab import userdata
    key = userdata.get("GOOGLE_API_KEY")
except Exception:
    import getpass
    key = getpass.getpass("Enter your Google AI Studio API key: ")

os.environ["GOOGLE_API_KEY"] = "".join(key.split())    # drop any stray whitespace/newlines
os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "False"      # use AI Studio, not Vertex AI
print("✅ API key set — using Google AI Studio.")
```

**Expected output:** `✅ API key set — using Google AI Studio.`

> aside negative
> **`Forbidden control character detected in headers`?** Your key has a stray newline/space (common when pasting into a Colab Secret). The `"".join(key.split())` above strips all whitespace — make sure that line is there, then **restart the runtime** (Runtime → Restart session) and re-run from the top. (Re-pasting the secret cleanly also fixes it.)

> aside negative
> **Error about an invalid or missing key?** Check that the secret is named **exactly** `GOOGLE_API_KEY`, that **Notebook access** is ON, and that the value starts with `AIza…` (~40 chars). Then re-run the cell.

### 6 · Run the "Shared building blocks" cell

Run the **Shared building blocks** cell once. It defines the Pydantic schemas + canned marathon scenarios that every level from L2 onward reuses. You'll see `✓ schemas + scenarios ready`.

> aside positive
> **Structured I/O** is how ADK 2 moves typed data between function nodes and agents. An agent with `output_schema=RaceStrategy` is *forced* to emit valid JSON for that model, and the next node receives it **validated** — no parsing glue. It arrives as a plain **dict** (JSON text for an agent node), so you index it (`node_input["fetch_weather"]["temp_f"]`) rather than reaching for attributes.

You're set up! 🎽 On to **L0**.

## L0 · Your first ADK 2 agent
Duration: 3

![Roadmap — you are here: L0](img/roadmap-L0.png)

<!-- beat:L0 -->
**The question:** can you get a model to answer, with the minimum ADK moving parts?

**The one idea — two objects:**

- **`Agent`** — the thing that reasons (a Gemini model + an instruction).
- **`Runner`** — the thing that executes an agent inside a session and streams events.
<!-- /beat:L0 -->

▶ **Colab:** run the [`L0` cell](https://colab.research.google.com/github/cuppibla/adk2-tutorial/blob/main/notebooks/adk2_orchestration.ipynb#scrollTo=L0) · 📁 **GitHub:** [`L0_first_agent/`](https://github.com/cuppibla/adk2-tutorial/tree/main/L0_first_agent) · 💻 **Local:** `python -m L0_first_agent.agent`

![L0 flow](img/diagram-l0.png)

```python
pace_coach = Agent(
    name="pace_coach", model=MODEL,
    instruction="You are a friendly, concise marathon coach. Answer in 3-4 sentences.",
)
runner = Runner(node=pace_coach, session_service=InMemorySessionService(), auto_create_session=True)
async for event in runner.run_async(user_id="u1", session_id="s1", new_message=msg):
    ...  # events carry the model's text
```

<!-- beat:L0 -->
**What you'll see:** the coach answers your question in a few sentences. That's the whole program — one `Agent`, one `Runner`, one `run_async` loop.

> aside positive
> Everything else in this codelab is just *more agents, arranged in more interesting shapes*. This is the atom.

> 👀 **Read:** just two objects — `Agent` (reasons) and `Runner` (executes + streams events). · ▶ **Run** it. · ✏️ **Change:** rewrite the `instruction` (make the coach blunt, or make it answer in one sentence) and re-run — the instruction IS the program.
<!-- /beat:L0 -->

## L1 · Your first Workflow
Duration: 4

![Roadmap — you are here: L1](img/roadmap-L1.png)

<!-- beat:L1 -->
**The question:** how do you mix plain code and an LLM in one flow, without paying for a model call on the parts that are just code?

**The one idea:** in a `Workflow`, a **plain Python function and an LLM agent are both just nodes** in the same `edges` list.

```
START ──► fetch_conditions (function, 0 LLM) ──► advise (agent, 1 LLM)
```
<!-- /beat:L1 -->

▶ **Colab:** run the [`L1` cell](https://colab.research.google.com/github/cuppibla/adk2-tutorial/blob/main/notebooks/adk2_orchestration.ipynb#scrollTo=L1) · 📁 **GitHub:** [`L1_graph_basics/`](https://github.com/cuppibla/adk2-tutorial/tree/main/L1_graph_basics) · 💻 **Local:** `python -m L1_graph_basics.workflow`

![L1 flow](img/diagram-l1.png)

The function node prints the data it produced (no model call), then the agent gives advice that references the actual temperature and wind it received:

```python
def fetch_conditions(node_input):                # function node — 0 LLM
    return Event(output=Conditions(temp_f=78, wind_mph=12, conditions="sunny").model_dump())

advise = Agent(name="advise", model=MODEL, mode="single_turn",
               input_schema=Conditions, instruction="...give pacing + gear advice...")

l1_workflow = Workflow(edges=[(START, fetch_conditions, advise)])
```

<!-- beat:L1 -->
**What's new vs L0:** `Workflow(edges=[...])`, `START` (where input enters), a function node returning `Event(output=...)`, and `input_schema=Conditions` so the function's output is validated against that schema before the agent sees it (as JSON text — `input_schema` validates the boundary, it does not hand the agent a Python object).

> 👀 **Read:** `fetch_conditions` returns data with **no model call**; `advise` has `input_schema=Conditions`. · ▶ **Run** it. · ✏️ **Change:** set `temp_f=30` in the function and re-run — the advice flips, and the function still cost 0 LLM calls.
<!-- /beat:L1 -->

## L2a · Parallel fan-out + JoinNode (Pillar 1a)
Duration: 4

![Roadmap — you are here: L2a](img/roadmap-L2a.png)

<!-- beat:L2a -->
**The question:** you can *draw the flow before the input arrives*. Start with the skeleton: gather data in parallel, bundle it, hand it to one agent.

**The shape:**

```
START ──► fetch_weather ──┐
START ──► analyze_course ─┼─► JoinNode ─► strategy (1 agent)
START ──► pull_fitness ───┘   (bundles)
```
<!-- /beat:L2a -->

▶ **Colab:** run the [`L2a` cell](https://colab.research.google.com/github/cuppibla/adk2-tutorial/blob/main/notebooks/adk2_orchestration.ipynb#scrollTo=L2a) · 📁 **GitHub:** [`L2a_parallel_join/`](https://github.com/cuppibla/adk2-tutorial/tree/main/L2a_parallel_join) · 💻 **Local:** `python -m L2a_parallel_join.workflow`

![L2a flow](img/diagram-l2a.png)

<!-- beat:L2a -->
- The three fetches are **functions** — they run **in parallel**, 0 LLM calls.
- **`JoinNode`** waits for all three and bundles them into one typed payload (`BundledRunData`), keyed by function name.
- One `strategy` agent reads the bundle and writes a `RaceStrategy`.

**What you'll see:** each fetch prints a `started` / `finished` timestamp. All three start at **0.0s** and the fan-out ends at **2.0s** — the slowest fetch, not the **4.5s** their durations would sum to. That overlap is the parallelism. (The *total* wall time printed at the end is ~8s because it also contains the strategy agent's LLM call — read the fetch timestamps for the parallel claim, not the total.)

> aside positive
> **Where ADK 2 gives this a direct home:** function nodes and an agent node are peers in one `edges` list. 1.x could keep steps out of the model too — via a custom `BaseAgent` subclass — but that meant writing the orchestration plumbing yourself, so most builds wrapped each step as an agent.

> 👀 **Read:** three edges fan out from `START`; `JoinNode` bundles them for one agent. · ▶ **Run** it and read the *timestamps*, not the total. · ✏️ **Change:** make one fetch sleep `3.0` — predict the new fan-out end time first, then verify.
<!-- /beat:L2a -->

## L2b · Add the deterministic router (Pillar 1b)
Duration: 4

![Roadmap — you are here: L2b](img/roadmap-L2b.png)

<!-- beat:L2b -->
**The question:** the plan should differ for hot vs cold weather. How do you branch — *without* asking the model to decide?

**The shape (L2a + a router):**

```
… JoinNode ─► route_by_weather ─► hot_strategy
               (if-statement)   ─► normal_strategy
                                ─► cold_strategy
```
<!-- /beat:L2b -->

▶ **Colab:** run the [`L2b` cell](https://colab.research.google.com/github/cuppibla/adk2-tutorial/blob/main/notebooks/adk2_orchestration.ipynb#scrollTo=L2b) — try `run("NORMAL")` / `run("COLD")` · 📁 **GitHub:** [`L2b_router/`](https://github.com/cuppibla/adk2-tutorial/tree/main/L2b_router) · 💻 **Local:** `python -m L2b_router.workflow COLD`

![L2b flow](img/diagram-l2b.png)

```python
def route_by_weather(node_input):                        # an if-statement, 0 LLM
    temp = node_input["fetch_weather"]["temp_f"]
    route = "HOT" if temp >= 70 else "COLD" if temp <= 40 else "NORMAL"
    return Event(output=node_input, route=route)

(route_by_weather, {"HOT": hot_strategy, "NORMAL": normal_strategy, "COLD": cold_strategy})
```

<!-- beat:L2b -->
**The takeaway — three kinds of work, three homes:**

- Predictable work → **functions** (the 3 parallel fetches)
- A clear rule → **explicit routing** (`route_by_weather` is an `if`-statement, not a model decision)
- Reasoning → **the model** (exactly **one** strategy agent runs)

**What you'll see:** `temp=78F -> route=HOT`, then a structured `RaceStrategy`. **Net cost: 1 LLM call.**

> aside positive
> The common 1.x build wrapped each step as an agent — **4 calls** instead of this pattern's **1**. (A custom `BaseAgent` subclass could reach 1 call in 1.x as well; it just wasn't first-class, so few builds did it.)

> ⚠️ **If you add a fourth branch,** give the route-dict a `DEFAULT_ROUTE` entry too. A route the dict doesn't match isn't an error — the branch simply ends, and the program exits **0 with no output**, which is a confusing dead end to debug.

> 👀 **Read:** `route_by_weather` — the router is an `if`-statement, not an agent. · ▶ **Run** `run("COLD")` too. · ✏️ **Change:** add a `WINDY` branch with a fourth agent — and read the `DEFAULT_ROUTE` warning above *before* you do.
<!-- /beat:L2b -->

## L3a · Collaborative agents: one flag, two worlds — Pillar 2
Duration: 6

![Roadmap — you are here: L3a](img/roadmap-L3a.png)

<!-- beat:L3a -->
**The question:** you know the **team**, but the **request** decides which members should answer. How do you let an LLM pick the subset — and run them concurrently?

**The shape:** a coordinator over six specialists (medical, weather, pacing, gear, nutrition, mental). This level runs the **same team twice** — same coordinator prompt, same six specialists. The only difference is one flag on the subagents. **The contrast is the lesson.**
<!-- /beat:L3a -->

▶ **Colab:** run the [`L3a` cell](https://colab.research.google.com/github/cuppibla/adk2-tutorial/blob/main/notebooks/adk2_orchestration.ipynb#scrollTo=L3a) · 📁 **GitHub:** [`L3a_collaborative/`](https://github.com/cuppibla/adk2-tutorial/tree/main/L3a_collaborative) · 💻 **Local:** `python -m L3a_collaborative.concierge --mode chat "What about fueling?"`

![L3a flow](img/diagram-l3a.png)

<!-- beat:L3a -->
### Beat 1 · Run the default first — and watch it fail the job

No `mode=` written → subagents default to **`chat`**. What you'll see:

```
TRANSFER → nutrition_specialist   (transfer_to_agent — the only tool chat subagents provide)
Final speaker: nutrition_specialist
```

The coordinator got **no delegation tools** — chat subagents only give it `transfer_to_agent`, a serial handoff of the *whole conversation* to **one** specialist. That specialist answers the user directly, and the run ends there. No parallel dispatch. No return. No synthesis. Ask the broad question and it gets worse: six specialists, one transfer.

That's not a bug — it's chat mode doing its job. The conversation *belongs* to whoever holds it, until someone explicitly transfers away. Right for an open-ended assistant; wrong for a pipeline step.

### Beat 2 · One flag, two worlds

The only diff: `mode="single_turn"` on each specialist. Same question, run again:

```
[t= 7.8s] DISPATCH → medical_specialist      ← same timestamp =
[t= 7.8s] DISPATCH → weather_specialist         one turn, many calls
[t=14.5s]   ↩ medical_specialist replied     ← replies land inside
[t=14.5s]   ↩ weather_specialist replied        one short window
🧠 Concierge (synthesized): <one answer>
```

Now ADK injects **one delegation tool per specialist** — named after the subagent, described by its `description=` (that text is what the coordinator reads when choosing the subset; skip it and you're routing on names alone). The coordinator emits several calls in one turn, ADK runs them **in parallel**, each auto-returns its result, and the coordinator synthesizes.

| Question | Specialists that fire |
| --- | --- |
| "What about fueling?" | nutrition only |
| "My knee hurts at mile 18" | medical only |
| "Should I race today?" | medical + weather + pacing |
| "Anything I should worry about?" | all 6 |

**Why each specialist gets handed the whole briefing:** each `single_turn` subagent runs in its **own isolated session branch** — it cannot see the conversation or its peers. Nothing is ambient: the coordinator must forward the *entire* `SpecialistInput` (question + strategy + runner data) separately into every parallel call.

> 💡 **Where ADK 2 gives this a direct home:** an LLM picks a **per-request subset** AND runs it in parallel — *declared* via `sub_agents` + `mode="single_turn"`. You could assemble the same shape in 1.x by wrapping each specialist in `AgentTool`; what changes is that it is now a declaration rather than plumbing. (`ParallelAgent` is always-all and `transfer_to_agent` is serial.)

> ⚠️ Two honest caveats: (1) the model picks the subset, so it's **less deterministic** than L2's hard-coded router — the exact subset can vary run to run. (2) Occasionally you'll see an `Error validating input: ...` line for one specialist. It is almost never the specialist's *output* — `output_schema` makes Gemini enforce that server-side. It's the **input**: the coordinator has to reproduce the whole nested `SpecialistInput` verbatim for every parallel call, and sometimes it fumbles one. ADK returns the error as that tool's result, the coordinator recovers, and the synthesis still lands.

> 👀 **Read:** the `_specialist` factory — the `mode` parameter is the whole level. · ▶ **Run** both beats. · ✏️ **Change:** ask *"my knee hurts at mile 18"* — **predict the subset first**, then check the DISPATCH lines.
<!-- /beat:L3a -->

```python
# The factory's mode parameter is THE variable this level teaches:
def _specialist(name, domain, focus, mode):
    kwargs = {}
    if mode == "single_turn":   # the structured contract only makes sense for a TOOL
        kwargs = dict(mode="single_turn",
                      input_schema=SpecialistInput, output_schema=SpecialistResponse)
    return Agent(name=name, model=MODEL,
                 description=f"Marathon {domain} specialist. Consult for: {focus}.",
                 instruction=..., **kwargs)

race_concierge = Agent(name="race_concierge", model=MODEL,
                       sub_agents=[...six specialists...],   # NOTE: no `mode` on the coordinator
                       instruction="...DECIDE which specialists are relevant... call them IN PARALLEL... SYNTHESIZE...")
```

## L3b · Task mode: a conversation with a finish line — Pillar 2
Duration: 5

![Roadmap — you are here: L3b](img/roadmap-L3b.png)

<!-- beat:L3b -->
**The question:** L3a left a gap. `chat` owns the whole conversation; `single_turn` never talks to the user at all. But real intake work sits in between: *"talk to the user UNTIL you've collected X — then come back with a validated object."* Which mode is that?

**The shape:**

```
race_desk (coordinator)
  └─ gear_fitter (mode="task", output_schema=GearOrder)
```
<!-- /beat:L3b -->

▶ **Colab:** run the [`L3b` cell](https://colab.research.google.com/github/cuppibla/adk2-tutorial/blob/main/notebooks/adk2_orchestration.ipynb#scrollTo=L3b) · 📁 **GitHub:** [`L3b_task_desk/`](https://github.com/cuppibla/adk2-tutorial/tree/main/L3b_task_desk) · 💻 **Local:** `python -m L3b_task_desk.desk`

![L3b flow](img/diagram-l3b.png)

<!-- beat:L3b -->
**What you'll see:**

```
━━ TURN 1 ━━  user: 'I need shoes for the marathon.'
  race_desk → delegate: gear_fitter
  gear_fitter: What is your shoe size?
  ⏸  The run ENDED — but nothing failed. This is a PAUSED task.

━━ TURN 2 ━━  user: 'Size 9, wide.'   (same session → resumes the task)
  gear_fitter → finish_task   (payload validates as GearOrder)
  race_desk: Your order ... in size 9 Wide has been confirmed.
```

Three things happened that neither L3a mode can do:

1. **The run genuinely stopped mid-task** — a *paused* task, not a hang and not a failure. The agent asked its clarifying question and is holding the task open. (In `adk web` you'd just type the answer; the harness scripts it as a second message on the same session.)
2. **The next message resumed the SAME task agent** — no re-routing, no re-delegation. The session knows who was waiting.
3. **`finish_task` ended it** — a tool ADK injected *because* of `mode="task"`. The agent must call it to finish, and its payload must validate against `output_schema`. A conversation with a **typed finish line** — then control auto-returns to the coordinator, result attached.

### The one-question rule for picking a mode

> 💡 **"Does the user need to talk to it — and until WHEN?"** chat = indefinitely · task = until the fields are collected · single_turn = never.

| Mode | Human in the loop | Parallel? | Returns to parent |
| --- | --- | --- | --- |
| `chat` *(subagent default)* — support assistant, open-ended copilot | full conversation | no | manual (via transfer) |
| `task` — intake, booking, troubleshooting | clarifying questions only | no | automatic (via `finish_task`, with a validated object) |
| `single_turn` — classify · extract · judge · generate | none | **yes** | automatic (with its result) |

`mode` goes on **subagents only** — never on the coordinator. And workflow *nodes* default to `single_turn` (which is why L1–L2b never wrote it), while *subagents* default to `chat` (which is why L3a had to).

> ⚠️ Two version notes before you build on this: (1) **`task` as a static graph node is version-dependent** — on 2.0.0b1–2.3.0 (this codelab's pin), `Workflow(...)` raises at construction; use exactly what this level does (a chat coordinator with task sub-agents) or dispatch via `ctx.run_node`. **Lifted in 2.5.0.** (2) **"Task agents must be leaf agents"** (no subagents of their own) is a documented ADK limitation — but a *contract*, not a runtime guard: neither 2.3.0 nor 2.5.0 will stop you. Don't read the absence of an error as permission.

> 💡 **Go deeper:** a `task` agent embedded in a *graph workflow* (the 2.5.0+ shape), with routing that can loop the conversation back for a retry: companion repo [`22_agent_in_workflow`](https://github.com/cuppibla/adk-workflows-compared/tree/main/examples/22_agent_in_workflow) · full mode guide: [`docs/agent-modes.md`](https://github.com/cuppibla/adk-workflows-compared/blob/main/docs/agent-modes.md).

> 👀 **Read:** `gear_fitter` — `mode="task"` + `output_schema` is the entire contract. · ▶ **Run** it. · ✏️ **Change:** `run_desk("I need a hydration vest", "2 liters, medium")` — the clarifying question adapts, the finish line stays typed.
<!-- /beat:L3b -->

## L4a · Runtime-sized parallel fan-out (Pillar 3a)
Duration: 5

![Roadmap — you are here: L4a](img/roadmap-L4a.png)

<!-- beat:L4a -->
**The question:** the *shape* of the work depends on the input. You can't draw the graph ahead of time. Start with runtime **width**: let the LLM decide *how many* sub-questions.

**The shape (one level deep):**

```
START ─► decompose ─► research_topic (parallel_worker) ─► synthesize
                             │  │  │
                             └──┴──┴─ (flat: no children yet)
```

An open-ended question is **decomposed** into N sub-questions — **N is chosen by the LLM at runtime** (3–7) — each **researched in parallel**, then **synthesized** into one briefing.

> aside negative
> This cell makes **5–9 live LLM calls** (1 decompose + 3–7 research + 1 synthesize) and takes **~20–30s**. It costs real API quota.
<!-- /beat:L4a -->

▶ **Colab:** run the [`L4a` cell](https://colab.research.google.com/github/cuppibla/adk2-tutorial/blob/main/notebooks/adk2_orchestration.ipynb#scrollTo=L4a) · 📁 **GitHub:** [`L4a_flat_research/`](https://github.com/cuppibla/adk2-tutorial/tree/main/L4a_flat_research) · 💻 **Local:** `python -m L4a_flat_research.deep_research`

![L4a flow](img/diagram-l4a.png)

<!-- beat:L4a -->
**What you'll see:** the decomposer prints e.g. 5 sub-questions, they research in parallel, then a synthesized briefing. The *number* differs on every run — the fixed graph couldn't do that.

> aside positive
> **Where ADK 2 gives this a direct home:** `@node(parallel_worker=True)` fans one worker across a **runtime-sized** list. A 1.x `ParallelAgent` needs a fixed list known at build time; raw `asyncio` could size it at runtime, but then it is no longer a workflow ADK can trace.

**Two flags on the worker worth understanding:**

- **`rerun_on_resume=True` is mandatory** on any node that calls `ctx.run_node` — ADK raises a `ValueError` without it. On resume it must re-execute the dispatching node to rebuild the children it spawned, since those aren't in the static graph.
- **`retry_config=` bounds how this FAILS.** A parallel worker cancels every sibling and re-raises the instant one child fails — so without a retry, a single transient 429 discards the whole run, including every call already paid for. The retry lands on the inner per-item node, so each branch retries independently.

> 👀 **Read:** the two flags on `research_topic` — `parallel_worker` and `rerun_on_resume`. · ▶ **Run** it. · ✏️ **Change:** swap in your own open question — N changes because the *input* decided the width.
<!-- /beat:L4a -->

## L4b · Add recursive spawning (Pillar 3b)
Duration: 5

![Roadmap — you are here: L4b](img/roadmap-L4b.png)

<!-- beat:L4b -->
**The question:** one research finding sometimes surfaces a narrow sub-topic worth its own investigation. How do you let a branch **spawn more parallel work** — and keep it bounded?

**The shape (now recursive):**

```
START ─► decompose ─► research_topic (parallel_worker, recursive) ─► synthesize
                             │  │  │
                             │  │  └─ research(q3) ─► maybe spawn children
                             │  └─── research(q2) ─► maybe spawn children
                             └────── research(q1) ─► maybe spawn children
```

> aside negative
> This cell makes **5–30 live LLM calls** and takes **20–45s** — the ceiling is 1 decompose + 7 top-level + 7×3 children + 1 synthesize. Run it deliberately.
<!-- /beat:L4b -->

▶ **Colab:** run the [`L4b` cell](https://colab.research.google.com/github/cuppibla/adk2-tutorial/blob/main/notebooks/adk2_orchestration.ipynb#scrollTo=L4b) · 📁 **GitHub:** [`L4b_recursion/`](https://github.com/cuppibla/adk2-tutorial/tree/main/L4b_recursion) · 💻 **Local:** `python -m L4b_recursion.deep_research`

![L4b flow](img/diagram-l4b.png)

```python
@node(parallel_worker=True, rerun_on_resume=True)
async def research_topic(ctx, node_input):
    finding = coerce(await ctx.run_node(research_agent, node_input=...), ResearchFinding)
    if finding.needs_deeper and finding.deeper_questions and depth < MAX_DEPTH:   # boundary in CODE
        children = await ctx.run_node(research_topic, node_input=deeper)          # recursive fan-out
    yield Event(output={..., "children": children})
```

<!-- beat:L4b -->
**What you'll see:** research nodes printing `spawning N deeper` — recursion happening live — then a runtime tree shape (e.g. `5 top-level + 10 recursive children`). The tree differs on every run.

> aside positive
> **Where ADK 2 gives this a direct home:** runtime-sized *and* runtime-deep parallel fan-out with recursive `ctx.run_node`, all **inside the framework** — you keep tracing, checkpointing, and resumability. 1.x could recurse too, but only by dropping out to raw `asyncio`, which lost you all of that.

> aside positive
> **The rule:** *let the LLM shape the work, but keep the boundaries in code.* `MAX_DEPTH = 2` means depth-2 children cannot spawn — there is no depth 3. Width is bounded too (3–7 sub-questions).

> ⚠️ **Before you raise the knob:** the ceiling grows fast — `MAX_DEPTH=3` takes the worst case from ~30 calls to ~93. And at the very end of a run you may see a `cancelling N leftover tasks` log line: that's ADK tearing down its parallel task group after the result is already complete. Harmless — and depending on your logging config you may never see it.

> 👀 **Read:** the guard: `if finding.needs_deeper and depth < MAX_DEPTH`. · ▶ **Run** it. · ✏️ **Change:** set `MAX_DEPTH = 1` and re-run — the tree flattens (and the run gets cheaper). The boundary is YOURS, in code.
<!-- /beat:L4b -->

## L5 · Which pattern should you use?
Duration: 5

![Roadmap — you are here: L5](img/roadmap-L5.png)

<!-- beat:L5 -->
You've built all three. This is the model that makes them useful: **match the pattern to the shape of your problem.**

### The axis: who decides what runs next?

| Pillar | Who decides what runs next | Built in |
| --- | --- | --- |
| **1 · Graph** | the graph you drew | L2a / L2b |
| **2 · Collaborative** | the LLM | L3a / L3b |
| **3 · Dynamic** | your Python code, at runtime | L4a / L4b |

### Step 0: do you even need a graph?

ADK ships **prebuilt workflow agents** — `SequentialAgent`, `ParallelAgent`, `LoopAgent`. For a plain chain of agents, those are the cheapest correct answer and there's no graph to assemble. Reach past them when you need **explicit routing** (L2b's router), a **join** (L2a's `JoinNode`), or **nodes that aren't agents** (a plain function, zero LLM calls) — that last one is usually the reason.

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
   │
   └─ NO
      ├─ Known team, request picks the subset? ─► Pillar 2 · Collaborative  (L3a/L3b)
      └─ Does the shape depend on the input?  ──► Pillar 3 · Dynamic        (L4a/L4b)
```

> aside negative
> **What this codelab did not teach you.** Nine rungs, ~40 minutes — the scope is deliberate. **Loops** (generate → review → fix in a `while`) are the canonical dynamic shape and aren't here; neither is graph-workflow **human input** (`RequestInput` — L3b's paused *task* is the collaborative cousin, not the graph node); and L4b's **resumability** is asserted but never demonstrated. All of it is covered in the companion repo [**adk-workflows-compared**](https://github.com/cuppibla/adk-workflows-compared) — see [`07_loop`](https://github.com/cuppibla/adk-workflows-compared/tree/main/examples/07_loop), [`17_request_input`](https://github.com/cuppibla/adk-workflows-compared/tree/main/examples/17_request_input), and [`docs/three-pillars.md`](https://github.com/cuppibla/adk-workflows-compared/blob/main/docs/three-pillars.md).
<!-- /beat:L5 -->

![L5 · which pattern](img/diagram-table.png)

<!-- beat:L5 -->
### The honest 1.x-vs-2 framing

This is **not** "2.0 can do things 1.x couldn't" — 1.x could build all of it. The shift is that **2.0 gives each shape a more direct home**, so known control flow leaves the prompt and becomes structure you can see and test.

| Pattern | The 1.x cost | The ADK 2 home |
| --- | --- | --- |
| **Graph** | 4 LLM calls in the common build; routing hidden in a prompt | function + agent nodes as peers → 1 call, `if`-statement router |
| **Collaborative** | buildable via `AgentTool` plumbing; `ParallelAgent` always-all, `transfer_to_agent` serial | a **declared** team: `sub_agents` + `mode="single_turn"` |
| **Dynamic** | recursion drops you out of the framework | `parallel_worker` + recursive `ctx.run_node` inside the framework |

### They compose

The three patterns are **not mutually exclusive**. A graph node can call a collaborative coordinator; a specialist can launch a dynamic workflow. Choose the right pattern per *part* of the problem — that's how you avoid turning every agent system into one giant prompt.
<!-- /beat:L5 -->

## Congratulations
Duration: 1

You built a Marathon Race Day Coach and, along the way, all three of ADK 2's orchestration patterns.

### What you learned

- **L0–L1** — `Agent`, `Runner`, and your first `Workflow` (function nodes + agent nodes as peers).
- **L2a / L2b** — graph workflows: parallel fan-out + `JoinNode`, then deterministic routing — one LLM call.
- **L3a** — collaborative agents: the same team run in `chat` (stranded) then `single_turn` (parallel subset + synthesis) — one flag, two worlds.
- **L3b** — `task` mode: a paused clarifying question, a scripted resume, `finish_task` returning a validated object.
- **L4a / L4b** — dynamic workflows: runtime width (fan-out), then runtime depth (recursion) with boundaries in code.
- **L5** — the decision tree, and how the patterns compose.

### Lines worth keeping

> *Functions prepare the context. Edges define the workflow. The router chooses the path. The model writes the answer.*
>
> *Let the LLM shape the work, but keep the boundaries in code.*
>
> *Match the pattern to the shape of your problem.*

### Next steps

- Run the full app these levels were distilled from — the **Marathon Race Day Coach**, a FastAPI + SSE build with a browser UI showing all three modes live: [github.com/cuppibla/adk-2-marathon-demo](https://github.com/cuppibla/adk-2-marathon-demo).
- Go wider: [**adk-workflows-compared**](https://github.com/cuppibla/adk-workflows-compared) — all 23 official ADK 2 workflow samples, each with a 1.x port and when-to-use guidance. Start with [`docs/three-pillars.md`](https://github.com/cuppibla/adk-workflows-compared/blob/main/docs/three-pillars.md), then the things this codelab skipped: [`07_loop`](https://github.com/cuppibla/adk-workflows-compared/tree/main/examples/07_loop), [`17_request_input`](https://github.com/cuppibla/adk-workflows-compared/tree/main/examples/17_request_input), [`22_agent_in_workflow`](https://github.com/cuppibla/adk-workflows-compared/tree/main/examples/22_agent_in_workflow).
- Port your **own** problem: which parts are known-structure (L2), known-team (L3a/L3b), unknown-shape (L4)?
- Explore the code: [github.com/cuppibla/adk2-tutorial](https://github.com/cuppibla/adk2-tutorial).
