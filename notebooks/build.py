"""Build the Colab notebook FROM the repo modules — single source of truth.

The runnable `L*/` modules are the source. This script transforms each into a
self-contained notebook cell (strips package imports, `load_dotenv`, and the
`__main__` block; inlines the shared schemas as one early cell; appends a
top-level `await` driver), then writes notebooks/adk2_orchestration.ipynb.

Each cell gets a stable `metadata.id` so the codelab can deep-link to it via
`...ipynb#scrollTo=<id>`.

Run from the repo root:
    python notebooks/build.py
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


# ─── Source transform ─────────────────────────────────────────────────────────

def _strip_docstring(lines):
    """Drop a leading triple-quoted module docstring."""
    i = 0
    while i < len(lines) and lines[i].strip() == "":
        i += 1
    if i < len(lines) and lines[i].lstrip().startswith('"""'):
        first = lines[i].lstrip()
        # single-line docstring?
        if first.count('"""') >= 2:
            return lines[i + 1:]
        i += 1
        while i < len(lines) and '"""' not in lines[i]:
            i += 1
        return lines[i + 1:]
    return lines


def module_to_cell(src, drop_shared=True):
    """Transform a module's source into inline notebook-cell code."""
    lines = _strip_docstring(src.split("\n"))
    out, i = [], 0
    while i < len(lines):
        ln = lines[i]
        s = ln.strip()
        if s == "from __future__ import annotations":
            i += 1; continue
        if s.startswith("from dotenv import"):
            i += 1; continue
        if s.startswith("load_dotenv("):
            i += 1; continue
        if drop_shared and (s.startswith("from shared import") or s.startswith("from .schemas import")):
            if "(" in ln and ")" not in ln:            # multiline parenthesized import
                while i < len(lines) and ")" not in lines[i]:
                    i += 1
                i += 1                                  # skip the ')' line
            else:
                i += 1
            continue
        if s.startswith('if __name__ == "__main__"'):
            break                                       # drop the CLI runner to EOF
        out.append(ln)
        i += 1
    return "\n".join(out).strip()


def read(rel):
    return (ROOT / rel).read_text()


# ─── Cells ────────────────────────────────────────────────────────────────────

md = lambda src, cid: {"cell_type": "markdown", "metadata": {"id": cid}, "source": src}
code = lambda src, cid: {"cell_type": "code", "metadata": {"id": cid},
                         "execution_count": None, "outputs": [], "source": src}

cells = []

cells.append(md("""# 🏃‍♀️💨 ADK 2 Orchestration — Your Marathon Coach Adventure! 🏅

Welcome, Agent Architect! 🎉 In this notebook you'll build a **Marathon Race Day Coach** and, one runnable rung at a time, master ADK 2's **three orchestration patterns**.

By the end of this adventure, you'll be able to:

- 🧩 **Compose graph workflows** — mix plain functions and agents as peers, fan out in parallel, and route with a plain `if`-statement.
- 🤝 **Coordinate collaborative agents** — let an LLM pick the *right* specialists for each question and run them in parallel.
- 🌳 **Grow dynamic workflows** — let the LLM shape the work at runtime, with recursion kept safely bounded in code.

| Level | Idea |
|---|---|
| **L0** 🐣 | `Agent` + `Runner` — the atom |
| **L1** 🔗 | first `Workflow`: a function node and an agent node are peers |
| **L2a** 🌤️ | **Pillar 1a** — parallel fetch + `JoinNode` (one agent) |
| **L2b** 🚦 | **Pillar 1b** — add the deterministic router → 1 of 3 agents |
| **L3** 🤝 | **Pillar 2** — coordinator picks a dynamic subset of 6 specialists, in parallel |
| **L4a** 🌱 | **Pillar 3a** — decompose → flat parallel research (runtime width) |
| **L4b** 🌳 | **Pillar 3b** — add recursive spawning (runtime depth) |
| **L5** 🧭 | which pattern, when (reading) |

**The through-line:** known structure → known team / variable subset → unknown shape → choose the right one 🎯

```
    ___       ___       ___       ___       ___
   |o o|     |^_^|     |•‿•|     |^o^|     |=^.^|
   |_-_|     |_-_|     |_-_|     |_-_|     |_-_|
    L0        L1       L2a·b       L3      L4a·b·L5
   ready →   flows →   graph →   team →   dynamic →  🏁
```

> 🏁 Run the cells **top to bottom**. Ready? Let's go! 👇""", "intro"))

cells.append(md("""## Author ✍️

Hi, I'm **Qingyue (Annie) Wang**, a Developer Advocate and AI Engineer at **Google**, passionate about helping developers build with AI and cloud technologies :)

If you have questions about this notebook, reach me on [LinkedIn](https://www.linkedin.com/in/anniewangtech/), [X](https://twitter.com/anniewangtech), or email anniewangtech0510@gmail.com

```
  (\\__/)
  (•ㅅ•)
  /づ  🏃   Enjoy building AI Agents — now go run your marathon! :)
```""", "author"))

cells.append(md("""---
## 🔑 Part 0 · Setup & Authentication

First things first — let's get your gear on! 🎽 This step installs the exact ADK 2 version the tutorial was verified on, then wires up your **Google AI Studio** API key.

1. 👉 Get a free key at **[aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey)** — click *Create API key*, copy it (starts with `AIza…`).
2. 🔑 In Colab, click the **Secrets** icon (left sidebar) → *Add new secret* → name it **`GOOGLE_API_KEY`**, paste the value, and toggle **Notebook access ON**.
3. Run the two cells below.""", "setup"))

cells.append(code('''# Pin the exact ADK 2 version this tutorial was verified on.
%pip install -q "google-adk==2.3.0" python-dotenv pydantic nest_asyncio
import nest_asyncio; nest_asyncio.apply()   # let Colab's running loop accept nested awaits
print("\\u2713 installed")''', "install"))

cells.append(code('''import os

# Google AI Studio API key — add GOOGLE_API_KEY in the 🔑 Secrets panel (or paste when prompted).
try:
    from google.colab import userdata
    key = userdata.get("GOOGLE_API_KEY")
except Exception:
    import getpass
    key = getpass.getpass("Enter your Google AI Studio API key: ")

os.environ["GOOGLE_API_KEY"] = "".join(key.split())   # drop ALL whitespace/newlines (not just the ends)
os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "False"     # use AI Studio, not Vertex AI
print("\\u2705 API key set \\u2014 using Google AI Studio.")''', "apikey"))

# Shared cell — generated from shared/schemas.py + shared/scenarios.py
shared_src = (
    "# Generated from shared/schemas.py + shared/scenarios.py by notebooks/build.py.\n"
    '# (No `from __future__ import annotations` — deferred string annotations break\n'
    "#  pydantic forward-refs for nested models in a single notebook namespace.)\n"
    'MODEL = "gemini-flash-latest"\n\n'
    + module_to_cell(read("shared/schemas.py")) + "\n\n"
    + module_to_cell(read("shared/scenarios.py")) + "\n\n"
    'print("\\u2713 schemas + scenarios ready")'
)
cells.append(md("""---
## 📦 Shared building blocks

Structured I/O is how ADK 2 moves typed data between function nodes and agents — like passing a clean baton 🏃‍♀️➡️🏃. These Pydantic schemas + canned marathon scenarios are reused from L2 onward. **Run this cell once**, then keep going.""", "shared_md"))
cells.append(code(shared_src, "shared"))

# Level cells — code transformed from the modules, driver appended.
LEVELS = [
    ("L0", "🐣 L0 · Your First Agent — the Pace Coach",
     "Every marathon starts with one step. Two objects: an **`Agent`** reasons; a **`Runner`** executes it and streams events. That's the atom — everything after this is just more agents in more interesting shapes.",
     "L0_first_agent/agent.py", 'await ask("What is the most common mistake first-time marathoners make?")'),
    ("L1", "🔗 L1 · Your First Workflow — code meets model",
     "A plain Python function and an LLM agent are **both just nodes** in one `edges` list. Predictable work stays a function (0 LLM); only reasoning is an agent. `START ──► fetch_conditions (0 LLM) ──► advise (1 LLM)`.",
     "L1_graph_basics/workflow.py", "await main()"),
    ("L2a", "🌤️ L2a · Parallel Fan-out + JoinNode (Pillar 1a)",
     "Gather race-day data **in parallel** (3 functions, 0 LLM), a **`JoinNode`** bundles it, and one strategy agent writes the plan. No router yet. ✨ Try `run(\"COLD\")` and watch it adapt!",
     "L2a_parallel_join/workflow.py", 'await run("HOT")'),
    ("L2b", "🚦 L2b · Add the Deterministic Router (Pillar 1b)",
     "Now a **deterministic `if`-statement router** branches on temperature to one of three specialized agents — hot / normal / cold. **Net cost: 1 LLM call.** 🔁 Try `run(\"NORMAL\")`.",
     "L2b_router/workflow.py", 'await run("HOT")'),
    ("L3", "🤝 L3 · Collaborative Agents — the Race Concierge (Pillar 2)",
     "Known **team** (6 specialists 🩺🌦️⏱️🎽🥤🧠); the **question** picks who answers. The coordinator runs the chosen subset **in parallel** and synthesizes one reply. 💡 Change the question and re-run — the contrast *is* the lesson!\n\n*Note: occasionally a specialist returns prose not JSON and you'll see a validation warning — the coordinator recovers. 🙂*",
     "L3_collaborative/concierge.py", 'await ask("Should I race today?")'),
    ("L4a", "🌱 L4a · Runtime-Sized Fan-out — Deep Research (Pillar 3a)",
     "An open-ended question is **decomposed** into N sub-questions (**width chosen at runtime**), each researched **in parallel**, then synthesized. One level deep — no recursion yet.\n\n⚠️ ~7-9 live LLM calls, ~20-30s.",
     "L4a_flat_research/deep_research.py", "await run()"),
    ("L4b", "🌳 L4b · Add Recursive Spawning (Pillar 3b)",
     "Now each finding can **recursively spawn** deeper questions via `ctx.run_node` (**depth chosen at runtime**), safely bounded by `MAX_DEPTH`. Recursion runs **inside the framework** — you keep tracing & checkpointing. 🌲\n\n⚠️ ~10-17 live LLM calls, 20-45s.",
     "L4b_recursion/deep_research.py", "await run()"),
]

# Cute ASCII "agent cards" (Annie's crash-course style) shown above each level's code.
BOXES = {
 "L0": """```
+---------------------------------------------+
|           🏃  pace_coach   (Agent)          |
|---------------------------------------------|
|  model : gemini-flash-latest                |
|  role  : friendly, concise marathon coach   |
|  runs  : Runner  >  Session  >  events      |
+---------------------------------------------+
```""",
 "L1": """```
+---------------------------------------------+
|          🔗  l1_workflow  (Workflow)        |
|---------------------------------------------|
|  START > fetch_conditions > advise          |
|          (function, 0 LLM)   (agent, 1 LLM) |
+---------------------------------------------+
```""",
 "L2a": """```
+---------------------------------------------+
|       🌤️  l2a_parallel_join  (Workflow)     |
|---------------------------------------------|
|  fetch_weather  --+                          |
|  analyze_course --+--> JoinNode --> strategy |
|  pull_fitness   --+   (parallel,0LLM)   (1)  |
+---------------------------------------------+
```""",
 "L2b": """```
+---------------------------------------------+
|      🚦  marathon_strategy  (Workflow)      |
|---------------------------------------------|
|  3 parallel fetches > JoinNode > router     |
|  > hot / normal / cold      (1 LLM call)    |
+---------------------------------------------+
```""",
 "L3": """```
+-----------------------------------------------+
|       🤝  race_concierge  (coordinator)       |
|-----------------------------------------------|
|  6 specialists (single_turn):                 |
|  medical.weather.pacing.gear.nutrition.mental |
|  reads the question > picks a subset >        |
|  runs them in parallel > synthesizes 1 answer |
+-----------------------------------------------+
```""",
 "L4a": """```
+---------------------------------------------+
|      🌱  l4a_flat_research  (Workflow)       |
|---------------------------------------------|
|  decompose > research x N (parallel) >      |
|  synthesize     (width chosen at runtime)   |
+---------------------------------------------+
```""",
 "L4b": """```
+---------------------------------------------+
|        🌳  deep_research  (Workflow)         |
|---------------------------------------------|
|  decompose > research > (recurse: children) |
|  > synthesize    MAX_DEPTH = 2  guard-rail  |
+---------------------------------------------+
```""",
}

for cid, title, intro, modpath, driver in LEVELS:
    box = ("\n\n" + BOXES[cid]) if cid in BOXES else ""
    cells.append(md(f"---\n## {title}\n\n{intro}{box}", f"{cid}_md"))
    body = module_to_cell(read(modpath))
    cells.append(code(f"{body}\n\n{driver}", cid))

cells.append(md("""---
## 🧭 L5 · Which Pattern, When? (the finish line 🏁)

One question picks your pattern:

```
Can you draw the workflow before the input arrives?
├─ YES ───────────────────────────────► Pillar 1 · graph workflow   (L2a/L2b) 🚦
└─ NO
   ├─ Known team, request picks the subset? ─► Pillar 2 · collaborative (L3) 🤝
   └─ Does the shape depend on the input?  ──► Pillar 3 · dynamic       (L4a/L4b) 🌳
```

**Not** "2.0 can do what 1.x couldn't" — 1.x could build all of it. 2.0 gives each shape a **more direct home**, so known control flow leaves the prompt and becomes structure you can see and test. And they **compose**: a graph node can call a collaborative coordinator; a specialist can launch a dynamic workflow. 🧩

> 🏅 *Predictable work stays functions; clear rules become explicit routing; reasoning uses the model.*
> 🌟 *Let the LLM shape the work, but keep the boundaries in code.*
> 🎯 *Match the pattern to the shape of your problem.*

```
  \\o/   You finished the marathon! 🏁🎉
   |    You now know all three ADK 2 orchestration patterns.
  / \\   Go build something amazing — and keep the boundaries in code. 💪
```

🐾 *Made with love by Annie — happy building!*""", "L5"))

nb = {
    "cells": cells,
    "metadata": {
        "colab": {"provenance": [], "toc_visible": True},
        "kernelspec": {"display_name": "Python 3", "name": "python3"},
        "language_info": {"name": "python"},
    },
    "nbformat": 4,
    "nbformat_minor": 0,
}

out = ROOT / "notebooks" / "adk2_orchestration.ipynb"
out.write_text(json.dumps(nb, indent=1))
print(f"wrote {out.relative_to(ROOT)} — {len(cells)} cells "
      f"({sum(1 for c in cells if c['cell_type']=='code')} code, "
      f"{sum(1 for c in cells if c['cell_type']=='markdown')} md)")
print("cell ids:", [c["metadata"]["id"] for c in cells])
