"""Draw the whole app from the code — including the parts a graph cannot show.

ADK exposes a Workflow's structure at `wf.graph.edges`, so the static half of
this lab can be drawn straight from the real objects instead of by hand. Run
this and the picture can never drift from the code.

What the introspection actually finds is itself the lesson:

    Pillar 1 (L1/L2a/L2b)  -> the FULL graph, routes and all
    Pillar 2 (L3a/L3b)     -> no edges at all; only `sub_agents` + `mode`
    Pillar 3 (L4a/L4b)     -> 3 edges, identical in both, and the recursion
                              that distinguishes them is nowhere in them

So the diagram encodes one visual rule: SOLID = present in `graph.edges`
(knowable before any input arrives), DASHED = decided at runtime. What you can
draw ahead of time IS Pillar 1; what you cannot draw is why 2 and 3 exist.

Run from the repo root:
    python scripts/graph_dump.py            # writes the HTML + prints the graph
    python scripts/graph_dump.py --png      # also renders assets/felt/diagram-whole.png
"""
from __future__ import annotations

import html
import importlib
import subprocess
import sys
import warnings
from pathlib import Path

warnings.filterwarnings("ignore")

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

OUT_HTML = ROOT / "assets" / "diagram-whole.html"
OUT_PNG = ROOT / "assets" / "felt" / "diagram-whole.png"
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

LEVELS = [
    ("L1", "L1_graph_basics.workflow", "workflow"),
    ("L2a", "L2a_parallel_join.workflow", "root"),
    ("L2b", "L2b_router.workflow", "root"),
    ("L3a", "L3a_collaborative.concierge", "race_concierge"),
    ("L3b", "L3b_task_desk.desk", "race_desk"),
    ("L4a", "L4a_flat_research.deep_research", "l4a_workflow"),
    ("L4b", "L4b_recursion.deep_research", "l4b_workflow"),
]


# ── introspection ────────────────────────────────────────────────────────────

def inspect():
    found = {}
    for tag, mod, obj in LEVELS:
        o = getattr(importlib.import_module(mod), obj)
        g = getattr(o, "graph", None)
        found[tag] = {
            "name": getattr(o, "name", None),
            "type": type(o).__name__,
            "edges": [(e.from_node.name, e.to_node.name, type(e.to_node).__name__, e.route)
                      for e in g.edges] if g is not None else [],
            "sub_agents": [(s.name, getattr(s, "mode", None))
                           for s in (getattr(o, "sub_agents", None) or [])],
        }
    from shared.schemas import DecomposerOutput, ResearchFinding
    import L4b_recursion.deep_research as l4b

    def bound(model, field, key):
        for m in model.model_fields[field].metadata:
            if hasattr(m, key):
                return getattr(m, key)
        return None

    found["_bounds"] = {
        "fan_min": bound(DecomposerOutput, "sub_questions", "min_length"),
        "fan_max": bound(DecomposerOutput, "sub_questions", "max_length"),
        "child_max": bound(ResearchFinding, "deeper_questions", "max_length"),
        "max_depth": l4b.MAX_DEPTH,
    }
    return found


# ── tiny SVG helpers (all geometry is computed, never eyeballed) ─────────────

def node(x, y, w, h, label, sub="", tone="ink", dashed=False, rx=13):
    fill = {"ink": "#FFFDF8", "blue": "#EEF4FA", "sage": "#EEF4E8", "honey": "#FBF3DC"}[tone]
    edge = {"ink": "#C9BBA6", "blue": "#7EA8C9", "sage": "#9DBF8E", "honey": "#EBC468"}[tone]
    d = ' stroke-dasharray="7 5"' if dashed else ""
    op = ' opacity=".92"' if dashed else ""
    t = (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="{fill}" '
         f'stroke="{edge}" stroke-width="3"{d}{op}/>')
    ty = y + h / 2 + (0 if not sub else -9)
    t += (f'<text x="{x + w/2}" y="{ty}" class="nt" text-anchor="middle" '
          f'dominant-baseline="middle">{label}</text>')
    if sub:
        t += (f'<text x="{x + w/2}" y="{y + h/2 + 15}" class="ns" text-anchor="middle" '
              f'dominant-baseline="middle">{html.escape(sub)}</text>')
    return t


def arrow(x1, y1, x2, y2, dashed=False, label="", tone="#B8A88F", curve=0, lx=None):
    d = ' stroke-dasharray="7 6"' if dashed else ""
    if curve:
        mid = (x1 + x2) / 2
        path = f"M{x1},{y1} C{mid},{y1} {mid},{y2} {x2},{y2}"
    else:
        path = f"M{x1},{y1} L{x2},{y2}"
    head = "arrowD" if dashed else "arrow"
    s = (f'<path d="{path}" fill="none" stroke="{tone}" stroke-width="3"{d} '
         f'marker-end="url(#{head})"/>')
    if label:
        lx = lx if lx is not None else (x1 + x2) / 2
        ly = (y1 + y2) / 2 - 9
        s += (f'<rect x="{lx-31}" y="{ly-13}" width="62" height="23" rx="11" fill="#FBF1E2" '
              f'stroke="{tone}" stroke-width="1.6"/>'
              f'<text x="{lx}" y="{ly+3}" class="rt" text-anchor="middle">{html.escape(label)}</text>')
    return s


def lane_svg(w, h, body):
    return (f'<svg viewBox="0 0 {w} {h}" width="{w}" height="{h}">'
            f'<defs>'
            f'<marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="5.5" '
            f'markerHeight="6" orient="auto"><path d="M0,0 L10,5 L0,10 z" fill="#B8A88F"/></marker>'
            f'<marker id="arrowD" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="5.5" '
            f'markerHeight="6" orient="auto"><path d="M0,0 L10,5 L0,10 z" fill="#B8A88F"/></marker>'
            f'</defs>{body}</svg>')


# ── the three lanes, laid out from the introspected data ─────────────────────

def lane_graph(d):
    """Pillar 1 — L2b's real graph. Every edge here came from graph.edges."""
    e = d["L2b"]["edges"]
    fetches = sorted({n for _, n, _, r in e if n.startswith(("fetch_", "analyze_", "pull_"))})
    routes = [(n, r) for _, n, _, r in e if r]
    b = node(2, 100, 94, 62, "START", tone="ink", rx=31)
    for i, f in enumerate(fetches):
        y = 34 + i * 88
        b += node(142, y, 246, 62, f, tone="blue")
        b += arrow(98, 131, 138, y + 31, curve=1)
        b += arrow(390, y + 31, 436, 131, curve=1)
    b += node(440, 92, 166, 78, "JoinNode", "waits for all 3", tone="ink")
    b += arrow(608, 131, 652, 131)
    b += node(656, 92, 238, 78, "route_by_weather", "an if-statement", tone="blue")
    for i, (tgt, r) in enumerate(routes):
        y = 34 + i * 88
        b += node(982, y, 194, 62, tgt, tone="blue")
        b += arrow(896, 131, 978, y + 31, label=r, curve=1, lx=937)
    return lane_svg(1180, 290, b)


def lane_collab(d):
    """Pillar 2 — no edges exist. Only sub_agents + mode."""
    subs = [n for n, _ in d["L3a"]["sub_agents"]]
    b = node(2, 88, 258, 82, "race_concierge", "coordinator", tone="sage")
    # One dashed arrow into a dashed team container: the coordinator wires
    # itself to no particular specialist — it picks a subset per request.
    b += arrow(262, 129, 344, 129, dashed=True)
    b += ('<rect x="348" y="16" width="620" height="216" rx="22" fill="none" '
          'stroke="#7EA06F" stroke-width="3.2" stroke-dasharray="10 8"/>')
    b += '<text x="372" y="50" class="ns">sub_agents &#183; mode="single_turn"</text>'
    for i, s in enumerate(subs):
        col, row = i % 3, i // 3
        b += node(372 + col * 196, 70 + row * 74, 180, 54,
                  s.replace("_specialist", ""), tone="sage", dashed=True, rx=16)
    b += '<text x="348" y="268" class="rt2">the LLM picks the subset &#8212; a different one per request</text>'
    return lane_svg(1180, 290, b)


def lane_dynamic(d):
    """Pillar 3 — 3 static edges; the real shape is spawned at runtime."""
    bd = d["_bounds"]
    b = node(2, 98, 94, 62, "START", tone="ink", rx=31)
    b += arrow(98, 129, 138, 129)
    b += node(142, 90, 198, 78, "decompose", "picks N", tone="honey")
    b += arrow(342, 129, 384, 129)
    b += ('<rect x="388" y="14" width="560" height="220" rx="22" fill="none" '
          'stroke="#C99E3C" stroke-width="3.2" stroke-dasharray="10 8"/>')
    b += '<text x="412" y="48" class="ns">research_topic &#183; parallel_worker</text>'
    for i, lab in enumerate(["q1", "q2", "\u2026qN"]):
        b += node(414, 66 + i * 58, 158, 48, lab, tone="honey", dashed=True, rx=16)
    for src_y, lab in [(66, "q1\u00b7a"), (182, "qN\u00b7a")]:
        b += arrow(576, src_y + 24, 634, src_y + 24, dashed=True)
        b += node(638, src_y, 150, 48, lab, tone="honey", dashed=True, rx=16)
    b += ('<text x="713" y="146" class="ns2" text-anchor="middle">'
          'depth 2 &#8212; the cap</text>')
    b += arrow(950, 129, 994, 129)
    b += node(998, 90, 180, 78, "synthesize", "merges the tree", tone="honey")
    b += (f'<text x="388" y="268" class="rt3">N = {bd["fan_min"]}\u2013{bd["fan_max"]} at runtime '
          f'&#183; each branch may spawn \u2264{bd["child_max"]} children '
          f'&#183; bounded by MAX_DEPTH = {bd["max_depth"]}</text>')
    return lane_svg(1180, 290, b)


# ── page ─────────────────────────────────────────────────────────────────────

def build(d):
    n_static = len(d["L2b"]["edges"])
    n_l4 = len(d["L4a"]["edges"])
    lanes = [
        ("Pillar 1 · Graph", "L2b", "blue",
         f"{n_static} edges in <code>graph.edges</code> — every one of them solid below",
         lane_graph(d)),
        ("Pillar 2 · Collaborative", "L3a", "sage",
         f"<b>0 edges.</b> {len(d['L3a']['sub_agents'])} <code>sub_agents</code>, "
         f"mode <code>single_turn</code> — that is the whole structure",
         lane_collab(d)),
        ("Pillar 3 · Dynamic", "L4a / L4b", "honey",
         f"{n_l4} edges — and they are <b>identical</b> in L4a and L4b, "
         f"so the recursion is not in them",
         lane_dynamic(d)),
    ]
    rows = "".join(
        f'<section class="lane lane--{tone}">'
        f'<div class="lane__head"><span class="pill pill--{tone}">{title}</span>'
        f'<span class="lvl">{lvl}</span>'
        f'<p class="lane__note">{note}</p></div>'
        f'<div class="lane__art">{svg}</div></section>'
        for title, lvl, tone, note, svg in lanes)

    return f"""<!doctype html><meta charset="utf-8">
<title>The whole app — and what a graph can't show you</title>
<style>
@import url('https://fonts.googleapis.com/css2?family=Fredoka:wght@500;600;700&family=Nunito:wght@600;700;800&family=Space+Mono:wght@400;700&display=swap');
:root{{
  --cream:#FBF1E2; --ink:#4A4036; --muted:#8A7C6A; --line:#D8C7AE; --card:#FFFDF8;
  --blue:#7EA8C9; --blue-b:#5E86A8; --sage:#9DBF8E; --sage-b:#7EA06F;
  --honey:#EBC468; --honey-b:#C99E3C;
}}
*{{box-sizing:border-box}}
body{{margin:0;font-family:'Nunito',system-ui,sans-serif;color:var(--ink)}}
.slide{{width:1280px;height:1380px;padding:40px 36px 22px;display:flex;flex-direction:column;
  background:radial-gradient(1200px 700px at 80% -12%,#fff8ec 0,transparent 60%),var(--cream)}}
.head{{display:flex;align-items:flex-start;gap:18px;margin-bottom:6px}}
.bug{{width:78px;height:78px;object-fit:contain;margin-top:2px}}
.eyebrow{{font-family:'Space Mono',monospace;font-size:15px;letter-spacing:.15em;
  color:var(--muted);text-transform:uppercase}}
h1{{font-family:'Fredoka',sans-serif;font-weight:700;font-size:44px;margin:3px 0 0;line-height:1.05}}
.sub{{font-size:18px;color:var(--muted);font-weight:700;margin:7px 0 0}}
.legend{{margin-left:auto;background:var(--card);border:2px solid var(--line);border-radius:14px;
  padding:15px 20px;display:flex;flex-direction:column;gap:11px;min-width:360px}}
.legend b{{font-family:'Space Mono',monospace;font-size:13px;letter-spacing:.11em;
  text-transform:uppercase;color:var(--muted)}}
.lg{{display:flex;align-items:center;gap:12px;font-size:15px;font-weight:700;line-height:1.35}}
.lg svg{{flex:none}}
.lanes{{display:flex;flex-direction:column;gap:14px;margin-top:16px;flex:1}}
.lane{{display:flex;flex-direction:column;gap:5px;background:var(--card);border:2.5px solid var(--line);
  border-radius:22px;padding:16px 14px 10px}}
.lane--blue{{border-color:#CFE0EE;background:#F7FBFD}}
.lane--sage{{border-color:#D5E5CC;background:#F8FBF6}}
.lane--honey{{border-color:#F0DFB4;background:#FDFAF1}}
.lane__head{{display:flex;align-items:baseline;gap:12px;flex-wrap:wrap}}
.lane__note{{font-size:16px;color:var(--muted);font-weight:700;margin:0;line-height:1.4;flex:1;min-width:340px}}
.lane__note code{{font-family:'Space Mono',monospace;font-size:14.5px;background:#F0E6D5;
  padding:1px 5px;border-radius:5px;color:var(--ink)}}
.lane__note b{{color:var(--ink)}}
.pill{{display:inline-block;font-family:'Space Mono',monospace;font-size:14px;font-weight:700;
  letter-spacing:.05em;color:#fff;padding:5px 14px;border-radius:20px}}
.pill--blue{{background:var(--blue-b)}} .pill--sage{{background:var(--sage-b)}}
.pill--honey{{background:var(--honey-b)}}
.lvl{{font-family:'Space Mono',monospace;font-size:14px;color:var(--muted)}}
.lane__art{{display:flex;justify-content:center;margin-top:2px}}
.nt{{font-family:'Space Mono',monospace;font-weight:700;font-size:20.5px;fill:#4A4036}}
.ns{{font-family:'Nunito',sans-serif;font-weight:700;font-size:16px;fill:#8A7C6A}}
.rt{{font-family:'Space Mono',monospace;font-weight:700;font-size:15px;fill:#5E86A8}}
.rt2{{font-family:'Nunito',sans-serif;font-weight:700;font-size:17.5px;fill:#7EA06F}}
.ns2{{font-family:'Space Mono',monospace;font-weight:400;font-size:16px;fill:#8A7C6A}}
.rt3{{font-family:'Nunito',sans-serif;font-weight:700;font-size:17.5px;fill:#C99E3C}}
.foot{{display:flex;align-items:center;margin-top:8px;padding-top:9px;
  border-top:2px solid var(--line)}}
.punch{{font-family:'Fredoka',sans-serif;font-weight:600;font-size:25px;line-height:1.32}}
.punch em{{font-style:normal;color:var(--honey-b)}}
.prov{{margin-left:auto;text-align:right;font-family:'Space Mono',monospace;font-size:13px;
  color:var(--muted);line-height:1.6;flex:none}}
</style>
<div class="slide">
  <div class="head">
    <img class="bug" src="./felt/mascot-think.png" alt="">
    <div>
      <div class="eyebrow">L5 · one app, all three pillars</div>
      <h1>The Whole App — and What a Graph Can't Show You</h1>
      <p class="sub">Drawn from the running code: every solid line below was read out of <code>Workflow.graph.edges</code>.</p>
    </div>
    <div class="legend">
      <b>How to read this</b>
      <div class="lg"><svg width="34" height="10"><path d="M1,5 H33" stroke="#B8A88F" stroke-width="2.6"/></svg>
        <span><b>in <code>graph.edges</code></b> — fixed before any input arrives</span></div>
      <div class="lg"><svg width="34" height="10"><path d="M1,5 H33" stroke="#B8A88F" stroke-width="2.6" stroke-dasharray="7 6"/></svg>
        <span><b>decided at runtime</b> — nothing in the graph to draw</span></div>
    </div>
  </div>
  <div class="lanes">{rows}</div>
  <div class="foot">
    <div class="prov">generated from the code · <b>scripts/graph_dump.py</b> ·
      google-adk 2.3.0 · marathon race day coach</div>
  </div>
</div>
"""


def main() -> None:
    d = inspect()
    print("── introspected ──")
    for tag, _, _ in LEVELS:
        v = d[tag]
        bits = f"{len(v['edges'])} edges"
        if v["sub_agents"]:
            bits += f", {len(v['sub_agents'])} sub_agents ({v['sub_agents'][0][1]})"
        print(f"  {tag:4} {v['type']:9} {bits}")
    print("  bounds:", d["_bounds"])

    OUT_HTML.write_text(build(d))
    print(f"\nwrote {OUT_HTML.relative_to(ROOT)}")

    if "--png" in sys.argv:
        subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars",
                        "--window-size=1280,1380", "--force-device-scale-factor=2",
                        f"--screenshot={OUT_PNG}", "--virtual-time-budget=6000",
                        f"file://{OUT_HTML}"], check=True,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print(f"wrote {OUT_PNG.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
