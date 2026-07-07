# ADK 2 Orchestration — a graded, runnable tutorial

> Learn ADK 2's **three orchestration patterns** — graph workflows, collaborative agents, dynamic workflows — one runnable rung at a time, all through a single **Marathon Race Day Coach**.

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/drive/1J-sflaibh9kAPveOCZEW4lMpn9KZPLeI)

<!-- ↑ This points at the shared Colab copy. After pushing the repo public you can switch to the auto-updating form: colab.research.google.com/github/<owner>/<repo>/blob/main/notebooks/adk2_orchestration.ipynb -->

There are three ways to take this tutorial. **All cover the same eight levels.**
- **📖 Codelab (guided)** — a step-by-step walkthrough that wraps the Colab: [`codelab/adk2-orchestration.md`](codelab/). Best for following along start to finish.
- **▶ Colab (zero setup)** — click the badge, add your API key, run cells top to bottom. Best for "just show me it running."
- **💻 Local (GitHub)** — clone, `./setup_venv.sh`, run each level as a module. Best for editing and keeping the code.

---

## The ladder

![Your learning roadmap](assets/felt/diagram-roadmap.png)

Every level answers one question, adds one idea, and stays runnable on its own. The domain is the same throughout, so the levels **accumulate** into the full app — one **Marathon Race Day Coach**:

![Marathon Race Day Coach — architecture](assets/felt/diagram-arch.png)

| Level | The question it answers | What you learn | Run |
|---|---|---|---|
| **[L0](L0_first_agent/)** · First agent | Can I get a model to answer? | `Agent` + `Runner` — the atom | `python -m L0_first_agent.agent` |
| **[L1](L1_graph_basics/)** · First workflow | How do code and an LLM share one flow? | `Workflow(edges=...)`; function node + agent node are peers | `python -m L1_graph_basics.workflow` |
| **[L2a](L2a_parallel_join/)** · Graph 1 (Pillar 1) | I can draw the flow ahead of time | parallel fan-out · `JoinNode` · one agent | `python -m L2a_parallel_join.workflow` |
| **[L2b](L2b_router/)** · Graph 2 (Pillar 1) | Branch without asking the model | deterministic `if`-router · dict edge · **1 LLM call** | `python -m L2b_router.workflow` |
| **[L3](L3_collaborative/)** · Collaborative (Pillar 2) | Known team, request picks the subset | `Agent(sub_agents=...)` · `single_turn` · dynamic subset in parallel | `python -m L3_collaborative.concierge` |
| **[L4a](L4a_flat_research/)** · Dynamic 1 (Pillar 3) | Runtime *width* | `@node(parallel_worker=True)` · runtime-sized fan-out | `python -m L4a_flat_research.deep_research` |
| **[L4b](L4b_recursion/)** · Dynamic 2 (Pillar 3) | Runtime *depth* | recursive `ctx.run_node` · bounded `MAX_DEPTH` | `python -m L4b_recursion.deep_research` |
| **[L5](L5_capstone/)** · Capstone | Which pattern, when? | the decision tree · 1.x-vs-2 · how they compose | *(reading)* |

**The through-line:** *known structure → known team/variable subset → unknown shape → choose the right one.*

---

## Quickstart — Local

Requires **Python 3.11+** and a Gemini API key ([get one free](https://aistudio.google.com/apikey)).

```bash
git clone <this-repo> adk2-tutorial && cd adk2-tutorial
./setup_venv.sh            # uv if available, else python venv + pip; also creates .env
# edit .env → paste your GOOGLE_API_KEY
```

There are **two ways to run locally** (they use the same code):

**A) Browse everything in the ADK web UI** — like the [`adk_tutorial`](https://github.com/cuppibla/adk_tutorial) repo. Each level folder re-exports `root_agent`, so `adk web` lists them all.
```bash
./run.sh                   # → http://localhost:8080, pick a level from the dropdown
```
> Only the **`L0…L4b`** folders are runnable agents. `shared/`, `notebooks/`, `codelab/`, `L5_capstone/` may also appear in the dropdown but aren't agents.

**B) Run one level with its teaching output** — the parallel timing, the router branch, the recursion trace. This is the recommended way to *learn* each pattern, and it mirrors the Colab cells 1:1.
```bash
python -m L0_first_agent.agent
python -m L1_graph_basics.workflow
python -m L2a_parallel_join.workflow HOT
python -m L2b_router.workflow COLD
python -m L3_collaborative.concierge "Should I race today?"
python -m L4a_flat_research.deep_research
python -m L4b_recursion.deep_research
```

Always run levels as **modules from the repo root** (`python -m L2b_router.workflow`) so `from shared import ...` resolves.

## Quickstart — Colab

1. Open [`notebooks/adk2_orchestration.ipynb`](notebooks/adk2_orchestration.ipynb) in Colab (badge above, or upload it).
2. Runtime has no key — add yours via **🔑 Secrets** as `GOOGLE_API_KEY` (the first cell reads it), or paste it when prompted.
3. Run cells top to bottom. Each level is one runnable cell with a markdown explainer above it.

---

## What runs the model

- **Package:** `google-adk==2.3.0` (latest stable; every level was verified on it — see note below).
- **Model:** `gemini-flash-latest`.
- **Cost:** L0–L2b are cheap (0–1 model call each). L3 makes a handful. **L4a is ~7–9 calls; L4b is ~10–17 per run** — run those deliberately.

> **Version note.** Verified on **2.3.0** (latest stable) and also on 2.0.0b1 — the graph / collaborative / dynamic APIs (`Workflow(edges=...)`, `JoinNode`, `@node(parallel_worker=True)`, `Agent(mode="single_turn")`) are unchanged across the ADK 2 line so far. If a future release breaks them, re-verify and bump the pin.

## Repo layout
```
shared/                  # schemas + canned marathon scenarios (used by L2–L4)
L0_first_agent/          # Agent + Runner
L1_graph_basics/         # first Workflow: function node → agent node
L2a_parallel_join/       # Pillar 1a: parallel fetch + JoinNode → one agent
L2b_router/              # Pillar 1b: + deterministic router → 1 of 3 agents
L3_collaborative/        # Pillar 2: coordinator + 6 single_turn specialists
L4a_flat_research/       # Pillar 3a: decompose → flat parallel research
L4b_recursion/           # Pillar 3b: + recursive ctx.run_node, bounded depth
L5_capstone/             # decision tree + 1.x-vs-2 + composition (reading)
codelab/                 # the claat codelab that wraps the notebook
notebooks/               # the Colab notebook + build.py (generates it from the modules)
setup_venv.sh / .bat     # create venv + install deps + .env  (Mac/Linux · Windows)
run.sh                   # launch the ADK web UI (adk web) to browse all levels
```

Each `LX/__init__.py` re-exports its main node as `root_agent` (`from .workflow import root as root_agent`) — that's what lets `adk web` discover it, matching the `adk_tutorial` layout.

### The three artifacts stay in sync
The runnable `L*/` modules are the **single source of truth**. `notebooks/build.py` reads them and regenerates the Colab notebook (inlining `shared/`, stripping imports, adding stable cell ids). The [codelab](codelab/) deep-links each step to its notebook cell (`…ipynb#scrollTo=<id>`) and lists the matching `python -m …` command. Edit a module → run `python notebooks/build.py` → the notebook is current.

## A note on running it (what "easy to run" honestly means)
These are live, nondeterministic models. Two things you may occasionally see, both expected and both harmless: a **schema-validation warning** in L3 (a specialist returned prose instead of JSON; the coordinator recovers), and a **`cancelling N leftover tasks`** line at the end of L4b (ADK tearing down its parallel task group). Neither stops the run.
