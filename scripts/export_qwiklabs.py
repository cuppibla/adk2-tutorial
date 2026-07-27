"""Render the Qwiklabs (CloudVLab) lab from the SAME codelab source.

Single-prose-source, third artifact: codelab/adk2-orchestration.md is already
the one place teaching prose lives (the Colab notebook is extracted from it by
notebooks/build.py). This script renders the Google Cloud Skills Boost version
into qwiklabs/adk2001-adk2-orchestration/, matching the structure Christina Lin
established in CloudVLab/gcp-devrel-content (commit bb0a8bb):

    instructions/en.md      <- transformed from the codelab
    instructions/img/*.png  <- copied from codelab/img
    qwiklabs.yaml           <- template (env untouched) + duration/description
    QL_OWNER / .elixirignore / README.md  <- preserved verbatim

Lab-specific divergences (everything else flows from the source):
  - Task 1 is Christina's Cloud Shell + Vertex AI setup, preserved as a
    template (qwiklabs/_templates/task1.md) + `export ADK_MODEL=gemini-2.5-flash`
    because the AI-Studio alias gemini-flash-latest 404s on Vertex.
  - Our "Setup & Authentication" step (Colab/AI-Studio) is dropped in its favor.
  - Every level's Colab/GitHub/Local link row becomes a "Run it" bash block —
    the v1 lab never told students to run anything; this fixes that.

Run from the repo root:  python scripts/export_qwiklabs.py
"""
from __future__ import annotations

import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "codelab" / "adk2-orchestration.md"
TPL = ROOT / "qwiklabs" / "_templates"
OUT = ROOT / "qwiklabs" / "adk2001-adk2-orchestration"

LAB_TITLE = "Build with ADK 2 Orchestration Patterns"

# Commands per step (replaces the codelab's Colab/GitHub/Local row).
RUN_COMMANDS = {
    "Prologue": ["python -m shared.prologue"],
    "L0": ["python -m L0_first_agent.agent",
           'python -m L0_first_agent.agent "What is the most common mistake first-time marathoners make?"'],
    "L1": ["python -m L1_graph_basics.workflow"],
    "L2a": ["python -m L2a_parallel_join.workflow HOT",
            "python -m L2a_parallel_join.workflow COLD"],
    "L2b": ["python -m L2b_router.workflow HOT",
            "python -m L2b_router.workflow COLD"],
    "L3a": ['python -m L3a_collaborative.concierge --mode chat "What about fueling?"',
            'python -m L3a_collaborative.concierge "Should I race today?"'],
    "L3b": ["python -m L3b_task_desk.desk",
            'python -m L3b_task_desk.desk "I need a hydration vest" --reply "2 liters, medium"'],
    "L4a": ["python -m L4a_flat_research.deep_research"],
    "L4b": ["python -m L4b_recursion.deep_research"],
}


def md_inline_to_html(s: str) -> str:
    """Inline markdown -> the HTML Qwiklabs infoboxes use."""
    s = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', s)
    s = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", s)
    s = re.sub(r"(?<!\*)\*([^*\n]+)\*(?!\*)", r"<i>\1</i>", s)
    s = re.sub(r"`([^`]+)`", r"<code>\1</code>", s)
    return s


def asides_to_infoboxes(text: str) -> str:
    """claat `> aside positive|negative` blocks -> <ql-infobox>."""
    out, lines, i = [], text.split("\n"), 0
    while i < len(lines):
        m = re.match(r"> aside (positive|negative)\s*$", lines[i])
        if not m:
            out.append(lines[i]); i += 1; continue
        kind = m.group(1); i += 1
        body = []
        while i < len(lines) and lines[i].startswith(">"):
            body.append(lines[i][1:].lstrip()); i += 1
        html = "<br>".join(md_inline_to_html(l) for l in body if l.strip())
        if kind == "positive":
            out.append(f"<ql-infobox>\n<strong>Tip:</strong> {html}\n</ql-infobox>")
        else:
            out.append(f"<ql-warningbox>\n<p><strong>Important:</strong> {html}</p>\n</ql-warningbox>")
    return "\n".join(out)


def python_fences_to_blocks(text: str) -> str:
    """Python fences are illustrative EXCERPTS, never paste-me steps.

    Qwiklabs renders every ql-code-block with a copy button, so an unlabelled
    excerpt looks exactly like an instruction. Labelling them also keeps this
    lab clear of the platform's worst known trap: agy001 burned five commits
    fighting the renderer mangling pasted Python indentation before settling
    for a warning box (7c9ef3b). Students here clone and run — never paste —
    and this label is what keeps it that way.
    """
    def repl(m):
        code = m.group(1)
        attr = " templated" if "{{{" in code else ""
        return ("_Excerpt from the file you just cloned — read it, don't paste it; "
                "you run it with the command above._\n\n"
                f'<ql-code-block language="python"{attr}>\n{code}</ql-code-block>')
    return re.sub(r"```python\n(.*?)```", repl, text, flags=re.S)


def run_block(step_key: str) -> str:
    cmds = RUN_COMMANDS[step_key]
    blocks = "\n\n".join(f'<ql-code-block language="bash">\n{c}\n</ql-code-block>' for c in cmds)
    return f"### Run it\n\nIn Cloud Shell, from the `adk2-tutorial` directory:\n\n{blocks}"


def transform_step(title: str, body: str, task_no: int, step_key: str | None) -> str:
    body = re.sub(r"^Duration: \d+\n", "", body, flags=re.M)
    body = re.sub(r"^<!-- /?beat:\w+ -->\n", "", body, flags=re.M)
    # the Colab/GitHub/Local row (levels) or bare Local row (prologue) -> Run it
    link_row = re.compile(r"^(?:▶ \*\*Colab:\*\*|💻 \*\*Local:\*\*).*$", re.M)
    if step_key and step_key in RUN_COMMANDS:
        body, n = link_row.subn(run_block(step_key), body, count=1)
        assert n == 1, f"no link row found in step {title!r}"
    else:
        body = link_row.sub("", body)
    body = python_fences_to_blocks(body)
    body = asides_to_infoboxes(body)
    body = body.replace("the playground has you try exactly this",
                        "the ✏️ Change step below has you try exactly this")
    body = body.replace("codelab", "lab").replace("Codelab", "Lab")
    return f"## Task {task_no}. {title}\n\n{body.strip()}\n"


def transform_overview(body: str) -> str:
    body = re.sub(r"^Duration: \d+\n", "", body, flags=re.M)
    # lab-appropriate "What you'll need"
    body = re.sub(
        r"### What you'll need\n.*?(?=\n> aside|\n### )",
        "### What you'll need\n\n"
        "- Just this lab — it provisions a **temporary Google Cloud project** for you.\n"
        "- No personal API key, no local install: everything runs in **Cloud Shell**.\n"
        "- ~55 minutes (the two L4 levels are the long ones — budget them).\n\n",
        body, flags=re.S)
    # drop the Colab/local "Two ways to follow along" section entirely
    body = re.sub(r"### Two ways to follow along\n.*$", "", body, flags=re.S)
    body = python_fences_to_blocks(body)
    body = asides_to_infoboxes(body)
    body = body.replace("codelab", "lab").replace("Codelab", "Lab")
    return "## Overview\n\n" + body.strip() + "\n"


def main() -> None:
    src = SRC.read_text()
    src = src[src.index("# ADK 2 Orchestration"):]  # drop claat frontmatter

    # split into (title, body) steps
    parts = re.split(r"^## (.+)$", src, flags=re.M)
    steps = [(parts[i], parts[i + 1]) for i in range(1, len(parts) - 1, 2)]

    KEY = lambda t: (t.split(" ")[0].rstrip(":·") if t.split(" ")[0] in RUN_COMMANDS
                     else ("Prologue" if t.startswith("Prologue") else None))

    out = [f"# {LAB_TITLE}\n\n## adk2001\n\n![[/fragments/labmanuallogo]]\n"]
    task_no = 2  # Task 1 is the preserved environment setup
    for title, body in steps:
        if title.startswith("Overview"):
            out.append(transform_overview(body))
            t1 = (TPL / "task1.md").read_text()
            t1 = "\n".join(l for l in t1.split("\n") if not l.startswith("<!--"))
            out.append(t1.strip() + "\n")
        elif title.startswith("Setup & Authentication"):
            continue  # replaced by Christina's Cloud Shell Task 1
        elif title.startswith("Congratulations"):
            step = transform_step(title, body, task_no, None); task_no += 1
            anchor = "### Next steps\n"
            assert anchor in step
            step = step.replace(anchor, anchor + "\n"
                "- **Take it home:** your lab project is temporary, but the same tutorial "
                "runs as a zero-setup [Colab notebook]"
                "(https://colab.research.google.com/github/cuppibla/adk2-tutorial/blob/main/notebooks/adk2_orchestration.ipynb) "
                "— re-run any level anytime (uses your own free AI Studio key, unlike this lab).\n", 1)
            out.append(step)
        else:
            k = KEY(title)
            out.append(transform_step(title, body, task_no, k)); task_no += 1

    en = "\n".join(out)
    # During the lab students stay on the provisioned project — the ONLY Colab
    # link allowed is the take-home pointer injected into Congratulations.
    n_colab = en.count("colab.research.google.com")
    assert n_colab == 1, f"expected exactly 1 Colab link (the take-home), found {n_colab}"

    inst = OUT / "instructions"
    if (inst / "img").exists():
        shutil.rmtree(inst / "img")
    (inst / "img").mkdir(parents=True, exist_ok=True)
    # Ship only what en.md references — codelab/img keeps assets this lab does
    # not use (e.g. the retired architecture diagram), and orphan binaries in a
    # published lab are just weight nobody can trace.
    used = set(re.findall(r"\(img/([^)]+)\)", en))
    for p in sorted((ROOT / "codelab" / "img").glob("*.png")):
        if p.name in used:
            shutil.copy2(p, inst / "img" / p.name)
    (inst / "en.md").write_text(en)
    shutil.copy2(TPL / "qwiklabs.yaml", OUT / "qwiklabs.yaml")
    shutil.copy2(TPL / "QL_OWNER", OUT / "QL_OWNER")
    shutil.copy2(TPL / "README.md", OUT / "README.md")
    shutil.copy2(TPL / "elixirignore", OUT / ".elixirignore")
    if (OUT / "tf").exists():
        shutil.rmtree(OUT / "tf")
    shutil.copytree(TPL / "tf", OUT / "tf")

    tasks = re.findall(r"^## (Task \d+\..*|Overview.*)$", en, flags=re.M)
    print(f"wrote {inst / 'en.md'} — {len(en.splitlines())} lines")
    for t in tasks:
        print("  ", t)
    print("img:", len(list((inst / 'img').glob('*.png'))), "files")


if __name__ == "__main__":
    main()
