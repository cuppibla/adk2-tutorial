"""Build the Colab notebook FROM the repo modules — single source of truth.

The runnable `L*/` modules are the source. This script transforms each into a
self-contained notebook cell (strips package imports, `load_dotenv`, and the
`__main__` block; inlines the shared schemas as one early cell; appends a
top-level `await` driver), then writes BOTH notebooks/adk2_orchestration.ipynb (legacy, take-home only,
frozen to match the published codelab) and adk2_orchestration_workshop.ipynb
(adds the 🎓 workshop credit lane).

Each cell gets a stable `metadata.id` so the codelab can deep-link to it via
`...ipynb#scrollTo=<id>`.

Run from the repo root:
    python notebooks/build.py
"""
import json
import re
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


# Modules wrap local-only setup (the .env API-key preflight) in these markers.
# Colab sets GOOGLE_API_KEY in an earlier cell, so the block is stripped there.
LOCAL_ONLY_OPEN = "# [local-only]"
LOCAL_ONLY_CLOSE = "# [/local-only]"


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
        if s == LOCAL_ONLY_OPEN:                        # drop a local-only block
            while i < len(lines) and lines[i].strip() != LOCAL_ONLY_CLOSE:
                i += 1
            i += 1                                      # skip the closing marker
            continue
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


# ─── Single prose source ──────────────────────────────────────────────────────
# The codelab (codelab/adk2-orchestration.md) is the ONE place teaching prose
# lives. Regions wrapped in <!-- beat:X --> ... <!-- /beat:X --> markers are the
# per-level teaching cores; claat ignores the HTML comments, and this script
# extracts the same regions into the notebook's markdown cells. Edit the beat
# in the codelab -> run this script -> both artifacts agree. (This replaced the
# old hand-written summaries here, which had drifted from the codelab.)

def extract_beats(text):
    found = {}
    for m in re.finditer(r"<!-- beat:(\w+) -->\n(.*?)\n<!-- /beat:\1 -->", text, re.S):
        found.setdefault(m.group(1), []).append(m.group(2).strip())
    out = {}
    for k, parts in found.items():
        s = "\n\n".join(parts)
        # claat asides -> notebook-friendly quotes
        s = s.replace("> aside positive\n> ", "> 💡 ")
        s = s.replace("> aside negative\n> ", "> ⚠️ ")
        assert "](img/" not in s, f"beat {k} contains an image ref - move it outside the markers"
        out[k] = s
    return out


BEATS = extract_beats(read("codelab/adk2-orchestration.md"))


def extract_fence(text, name):
    """Pull a ```python fence marked <!-- cell:NAME --> out of the codelab.

    Same single-source rule as the beats, applied to the two setup cells. They
    are the only notebook code with no module to generate from (they configure
    Colab itself), so the codelab fence is their home — otherwise the same ~40
    lines live in two files and drift the first time one is edited.
    """
    m = re.search(rf"<!-- cell:{name} -->\n```python\n(.*?)```\n<!-- /cell:{name} -->",
                  text, re.S)
    assert m, f"no <!-- cell:{name} --> python fence found in the codelab"
    return m.group(1).strip()


CELLS = read("codelab/adk2-orchestration.md")


def check_excerpt_drift():
    """Every def/Agent/Workflow name shown in a codelab python excerpt must
    exist in the real modules — this is what caught the l1_workflow ghost."""
    cl = read("codelab/adk2-orchestration.md")
    src = "\n".join(p.read_text() for p in ROOT.glob("L*/*.py")) + \
          "\n".join(p.read_text() for p in ROOT.glob("shared/*.py"))
    ids = set()
    for block in re.findall(r"```python\n(.*?)```", cl, re.S):
        ids |= set(re.findall(r"^\s*(?:async )?def (\w+)", block, re.M))
        ids |= set(re.findall(r"^(\w+)\s*=\s*(?:Agent|Workflow|LlmAgent)\(", block, re.M))
    ghosts = sorted(i for i in ids if i not in src)
    assert not ghosts, f"codelab excerpts reference identifiers missing from modules: {ghosts}"


check_excerpt_drift()


# ─── Cells ────────────────────────────────────────────────────────────────────

md = lambda src, cid: {"cell_type": "markdown", "metadata": {"id": cid}, "source": src}
code = lambda src, cid: {"cell_type": "code", "metadata": {"id": cid},
                         "execution_count": None, "outputs": [], "source": src}

cells = []

cells.append(md("""# 🏃‍♀️💨 ADK 2 Orchestration — Your Marathon Coach Adventure! 🏅

Welcome, Agent Architect! 🎉 In this notebook you'll build a **Marathon Race Day Coach** and, one runnable rung at a time, master ADK 2's **three orchestration patterns**.

By the end of this adventure, you'll be able to:

- 🧩 **Compose graph workflows** — mix plain functions and agents as peers, fan out in parallel, and route with a plain `if`-statement.
- 🤝 **Coordinate collaborative agents** — let an LLM pick the *right* specialists and run them in parallel, and choose the right **mode** (`chat` / `task` / `single_turn`) for every subagent.
- 🌳 **Grow dynamic workflows** — let the LLM shape the work at runtime, with recursion kept safely bounded in code.

| Level | Idea |
|---|---|
| **P** 🎯 | Prologue — run the mega-prompt, watch it *invent* its data |
| **L0** 🐣 | `Agent` + `Runner` + a real **tool** — the atom |
| **L1** 🔗 | first `Workflow`: a function node and an agent node are peers |
| **L2a** 🌤️ | **Pillar 1a** — parallel fetch + `JoinNode` (one agent) |
| **L2b** 🚦 | **Pillar 1b** — add the deterministic router → 1 of 3 agents |
| **L3a** 🤝 | **Pillar 2** — same team, two worlds: `chat` strands the run; `single_turn` runs the subset in parallel |
| **L3b** 🎽 | **Pillar 2** — `task` mode: clarify → pause → resume → `finish_task` |
| **L4a** 🌱 | **Pillar 3a** — decompose → flat parallel research (runtime width) |
| **L4b** 🌳 | **Pillar 3b** — add recursive spawning (runtime depth) |
| **L5** 🧭 | which pattern, when (reading) |

**The through-line:** known structure → known team / variable subset → unknown shape → choose the right one 🎯

```
    ___       ___       ___       ___       ___
   |o o|     |^_^|     |•‿•|     |^o^|     |=^.^|
   |_-_|     |_-_|     |_-_|     |_-_|     |_-_|
    L0        L1       L2a·b     L3a·b     L4a·b·L5
   ready →   flows →   graph →   team →   dynamic →  🏁
```

**How each level works — three cells, one rhythm:** 📖 the *lesson* (short, every line is ADK) → 🔧 *run helpers* (folded; printing plumbing, not ADK — just run it, never required reading) → ▶ your *playground* (2 lines; edit, predict, re-run).\n\n> 🏁 Run the cells **top to bottom**, including the folded 🔧 ones. Ready? Let's go! 👇""", "intro"))

cells.append(md("""## Author ✍️

Hi, I'm **Qingyue (Annie) Wang**, a Developer Advocate and AI Engineer at **Google**, passionate about helping developers build with AI and cloud technologies :)

If you have questions about this notebook, reach me on [LinkedIn](https://www.linkedin.com/in/anniewangtech/), [X](https://twitter.com/anniewangtech), or email anniewangtech0510@gmail.com

```
  (\\__/)
  (•ㅅ•)
  /づ  🏃   Enjoy building AI Agents — now go run your marathon! :)
```""", "author"))

INSTALL = code('''# Pin the exact ADK 2 version this tutorial was verified on.
%pip install -q "google-adk==2.3.0" python-dotenv pydantic nest_asyncio
import nest_asyncio; nest_asyncio.apply()   # let Colab's running loop accept nested awaits
print("\\u2713 installed")''', "install")

# ── The setup region is the ONLY thing the two notebooks disagree about ──────
# adk2_orchestration.ipynb backs the ALREADY-PUBLISHED codelab, which walks the
# reader through these cells by name. So its setup region is frozen verbatim —
# a take-home reader must never meet a 🎓 cell nobody told them about. Levels
# and shared/ still regenerate from the modules for both notebooks; only this
# region is pinned. When the workshop codelab replaces the published one, this
# legacy list and the two-notebook split can both go.
LEGACY_SETUP = [
    md("""---
## 🔑 Part 0 · Setup & Authentication

First things first — let's get your gear on! 🎽 This step installs the exact ADK 2 version the tutorial was verified on, then wires up your **Google AI Studio** API key.

1. 👉 Get a free key at **[aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey)** — click *Create API key*, copy it (starts with `AIza…`).
2. 🔑 In Colab, click the **Secrets** icon (left sidebar) → *Add new secret* → name it **`GOOGLE_API_KEY`**, paste the value, and toggle **Notebook access ON**.
3. Run the two cells below.""", "setup"),
    INSTALL,
    code('''import os

# Google AI Studio API key — add GOOGLE_API_KEY in the 🔑 Secrets panel (or paste when prompted).
try:
    from google.colab import userdata
    key = userdata.get("GOOGLE_API_KEY")
except Exception:
    import getpass
    key = getpass.getpass("Enter your Google AI Studio API key: ")

os.environ["GOOGLE_API_KEY"] = "".join(key.split())   # drop ALL whitespace/newlines (not just the ends)
os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "False"     # use AI Studio, not Vertex AI
print("\\u2705 API key set \\u2014 using Google AI Studio.")''', "apikey"),
]

WORKSHOP_SETUP = [
    md("""---
## 🔑 Part 0 · Setup — pick your path

First things first — let's get your gear on! 🎽 Run the install cell below, then **one** of the two setup cells after it. Never both.

| | 🎓 **Workshop** | 🏠 **Take-home** |
| --- | --- | --- |
| **Who** | You're at a live workshop with a **credit claim link** | Everyone else — including workshop attendees, afterwards |
| **Runs on** | Vertex AI, on a project billed to your credit | Google AI Studio (free tier) |
| **Run** | the 🎓 cell | the 🏠 cell |

Everything from the Prologue onward is identical either way.""", "setup"),
    INSTALL,
    md("""---
### 🎓 Path A · Workshop (Google Cloud credit)

**Only if you're at a live workshop.** First claim your credit at the link your instructor shared (`https://me.developers.google.com/benefits/claim/…`) — using the **same Google account** you'll authorize below. Then run this cell and **skip Path B**.

It creates a project on your credit, enables the Vertex AI API, and points the notebook at Vertex.""", "workshop_md"),
    code(extract_fence(CELLS, "workshop"), "workshop"),
    md("""---
### 🏠 Path B · Take-home (AI Studio key)

**The default — and where workshop attendees come back to afterwards.** Get a free key at **[aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey)** (click *Create API key*, copy it — starts with `AIza…`), then in Colab click the **🔑 Secrets** icon in the left sidebar → *Add new secret* → name it exactly **`GOOGLE_API_KEY`**, paste the value, toggle **Notebook access ON**.

Ran Path A already? **Skip this cell** — it would switch you back to AI Studio.""", "takehome_md"),
    code(extract_fence(CELLS, "apikey"), "apikey"),
]

SETUP_MARK = object()          # placeholder; swapped per notebook at write time
cells.append(SETUP_MARK)

# Shared cell — generated from shared/schemas.py + shared/scenarios.py
def shared_src(model_line):
    return (
        "# Generated from shared/schemas.py + shared/scenarios.py by notebooks/build.py.\n"
        '# (No `from __future__ import annotations` — deferred string annotations break\n'
        "#  pydantic forward-refs for nested models in a single notebook namespace.)\n"
        + model_line + "\n"
        + module_to_cell(read("shared/schemas.py")) + "\n\n"
        + module_to_cell(read("shared/scenarios.py")) + "\n\n"
        'print("\\u2713 schemas + scenarios ready")'
    )


# Every level cell redefines MODEL the same way, so this one only matters if a
# level ever forgets to. On the workshop notebook that omission would silently
# 404 on Vertex, so there it reads the env var; the legacy notebook keeps the
# published literal, since nothing in it can set ADK_MODEL anyway.
SHARED_LEGACY = shared_src('MODEL = "gemini-flash-latest"\n')
SHARED_WORKSHOP = shared_src('import os\nMODEL = os.getenv("ADK_MODEL", "gemini-flash-latest")\n')

cells.append(md("""---
## 📦 Shared building blocks

Structured I/O is how ADK 2 moves typed data between function nodes and agents — like passing a clean baton 🏃‍♀️➡️🏃. These Pydantic schemas + canned marathon scenarios are reused from L2 onward. **Run this cell once**, then keep going.""", "shared_md"))
SHARED_MARK = object()         # placeholder; swapped per notebook at write time
cells.append(SHARED_MARK)

# Prologue — the mega-prompt failure, run before the ladder.
cells.append(md("---\n## 🎯 Prologue · Why Not One Big Prompt?\n\n" + BEATS["WHY"], "why_md"))
cells.append(code(module_to_cell(read("shared/prologue.py")) + "\n\nawait run()", "why"))

# Level cells — cute intro (personality layer, kept here) + teaching beat
# (extracted from the codelab) + code transformed from the module, driver appended.
LEVELS = [
    ("L0", "🐣 L0 · Your First Agent — the Pace Coach",
     "Every marathon starts with one step 🐾 — a model, an instruction, and one REAL tool.",
     "L0_first_agent/agent.py",
     'await ask("I want to finish in 3:30:00 — what pace do I need?")   # watch the 🔧 tool call\n'
     'await ask("What is the most common mistake first-time marathoners make?")  # no numbers → the model skips the tool'),
    ("L1", "🔗 L1 · Your First Workflow — code meets model",
     "Predictable work stays a function (0 LLM); only reasoning is an agent.",
     "L1_graph_basics/workflow.py", "await main()"),
    ("L2a", "🌤️ L2a · Parallel Fan-out + JoinNode (Pillar 1a)",
     "Fan out, join, decide ✨ Try `run(\"COLD\")` and watch the plan flip!",
     "L2a_parallel_join/workflow.py", 'await run("HOT")'),
    ("L2b", "🚦 L2b · Add the Deterministic Router (Pillar 1b)",
     "One `if`-statement instead of a model decision 💸 🔁 Try `run(\"NORMAL\")` too.",
     "L2b_router/workflow.py", 'await run("HOT")'),
    ("L3a", "🤝 L3a · Collaborative Agents: One Flag, Two Worlds (Pillar 2)",
     "Same team, run twice — the only diff is one flag. 💰 Beat 1 ≈ 2 LLM calls · Beat 2 ≈ 4–8 (depends on the subset).",
     "L3a_collaborative/concierge.py",
     'await ask("What about fueling?", mode="chat")   # Beat 1 — watch it strand\n'
     'await ask("Should I race today?")               # Beat 2 — one flag, two worlds'),
    ("L3b", "🎽 L3b · Task Mode: a Conversation with a Finish Line (Pillar 2)",
     "Clarify ➜ pause ➜ resume ➜ `finish_task` 🏁 (~4 LLM calls across two scripted turns).",
     "L3b_task_desk/desk.py", 'await run_desk("I need shoes for the marathon.", "Size 9, wide.")'),
    ("L4a", "🌱 L4a · Runtime-Sized Fan-out — Deep Research (Pillar 3a)",
     "The LLM picks how MANY — the width is decided at runtime.",
     "L4a_flat_research/deep_research.py", "await run()"),
    ("L4b", "🌳 L4b · Add Recursive Spawning (Pillar 3b)",
     "…and how DEEP — bounded by `MAX_DEPTH`, in code. 🌲",
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
 "L3a": """```
+-----------------------------------------------+
|       🤝  race_concierge  (coordinator)       |
|-----------------------------------------------|
|  6 specialists · same team, run twice:        |
|  chat (default)  > TRANSFER > stranded 🫠     |
|  single_turn     > parallel subset > 1 answer |
+-----------------------------------------------+
```""",
 "L3b": """```
+-----------------------------------------------+
|          🎽  race_desk  (coordinator)         |
|-----------------------------------------------|
|  gear_fitter (mode="task", output_schema)     |
|  ask > ⏸ paused > scripted reply > resume >   |
|  finish_task(GearOrder) > auto-return  🏁     |
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

HELPER_TITLE = ("#@title 🔧 Run helpers — printing only, NOT ADK. "
                "Run me once; expand only if curious.")

for cid, title, intro, modpath, driver in LEVELS:
    box = ("\n\n" + BOXES[cid]) if cid in BOXES else ""
    cells.append(md(f"---\n## {title}\n\n{intro}\n\n{BEATS[cid]}{box}", f"{cid}_md"))
    body = module_to_cell(read(modpath))
    # Modules mark where the teaching scaffold begins with `# [harness]`.
    # Everything above it is the LESSON (pure ADK); everything below is printing
    # plumbing, which ships as a separate, form-collapsed cell so the learner
    # reads ~40 lines of concept instead of a 170-line wall.
    assert "# [harness]" in body, f"{modpath}: missing # [harness] marker"
    concept, harness = body.split("# [harness]", 1)
    cells.append(code(concept.strip(), cid))
    hcell = code(HELPER_TITLE + "\n" + harness.strip(), f"{cid}_h")
    hcell["metadata"]["cellView"] = "form"
    cells.append(hcell)
    cells.append(code(f"# ▶ Your playground — edit these lines and re-run!\n{driver}", f"{cid}_run"))

cells.append(md("---\n## 🧭 L5 · Which Pattern, When? (the finish line 🏁)\n\n" + BEATS["L5"] + """

> 🏅 *Predictable work stays functions; clear rules become explicit routing; reasoning uses the model.*
> 🌟 *Let the LLM shape the work, but keep the boundaries in code.*
> 🎯 *Match the pattern to the shape of your problem.*

```
  \\o/   You finished the marathon! 🏁🎉
   |    You now know all three ADK 2 orchestration patterns — and all three modes.
  / \\   Go build something amazing — and keep the boundaries in code. 💪
```

🐾 *Made with love by Annie — happy building!*""", "L5"))

def write(filename, setup, shared):
    """Expand the two placeholders and write one notebook."""
    out_cells = []
    for c in cells:
        if c is SETUP_MARK:
            out_cells.extend(setup)
        elif c is SHARED_MARK:
            out_cells.append(code(shared, "shared"))
        else:
            out_cells.append(c)
    nb = {
        "cells": out_cells,
        "metadata": {
            "colab": {"provenance": [], "toc_visible": True},
            "kernelspec": {"display_name": "Python 3", "name": "python3"},
            "language_info": {"name": "python"},
        },
        "nbformat": 4,
        "nbformat_minor": 0,
    }
    p = ROOT / "notebooks" / filename
    p.write_text(json.dumps(nb, indent=1))
    print(f"wrote {p.relative_to(ROOT)} — {len(out_cells)} cells "
          f"({sum(1 for c in out_cells if c['cell_type']=='code')} code, "
          f"{sum(1 for c in out_cells if c['cell_type']=='markdown')} md)")
    print("  ids:", [c["metadata"]["id"] for c in out_cells][:9], "…")
    return out_cells


# Two notebooks, one source. The legacy file backs the published codelab and
# must keep showing exactly the cells that codelab names; the workshop file is
# what the new codelab links. Everything below the setup region is shared.
legacy = write("adk2_orchestration.ipynb", LEGACY_SETUP, SHARED_LEGACY)
workshop = write("adk2_orchestration_workshop.ipynb", WORKSHOP_SETUP, SHARED_WORKSHOP)

lids, wids = [c["metadata"]["id"] for c in legacy], [c["metadata"]["id"] for c in workshop]
assert "workshop" not in lids, "the legacy notebook must not contain the workshop cell"
assert wids[:8] == ["intro", "author", "setup", "install", "workshop_md",
                    "workshop", "takehome_md", "apikey"], f"unexpected workshop order: {wids[:8]}"
assert lids == [i for i in wids if i not in ("workshop_md", "workshop", "takehome_md")], \
    "the two notebooks must differ ONLY by the three workshop-lane cells"
