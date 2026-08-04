"""Dump the circuit-map atlas — the introspected truth every map view renders.

Pattern Kitchen's circuit map (/race/map?cell=…) lights up a diagram per Colab
cell. Its structural data comes from HERE, not from anyone's memory of the
code: each level is imported and its real objects are read — `wf.graph.nodes`,
`wf.graph.edges` (with routes), `agent.sub_agents` + mode, `agent.tools`, and
the L4 bounds. If a level changes shape, rerunning this script changes the map.

The teaching claims the map makes are ASSERTED before writing, so the atlas
cannot ship while contradicting the code it claims to depict:

  * Pillar 2 levels have no graph at all (they are agents, not workflows)
  * L4a and L4b have identical edge lists — the recursion is invisible to
    the graph, which is the whole L4b lesson
  * L2b's routes are exactly HOT / NORMAL / COLD

Run from the repo root (venv active):
    python scripts/atlas_dump.py

Writes assets/atlas.json. Pattern Kitchen keeps a checked-in copy at
src/lib/atlas.json — regenerate here, then copy across:
    cp assets/atlas.json ~/Documents/Demo/pattern-kitchen/src/lib/atlas.json
"""
from __future__ import annotations

import importlib
import json
import sys
import warnings
from pathlib import Path

warnings.filterwarnings("ignore")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

OUT = ROOT / "assets" / "atlas.json"

# (tag, module, object) — every runnable level, both pillar shapes.
LEVELS = [
    ("P",   "shared.prologue",               "mega_coach"),
    ("L0",  "L0_first_agent.agent",          "pace_coach"),
    ("L1",  "L1_graph_basics.workflow",      "workflow"),
    ("L2a", "L2a_parallel_join.workflow",    "root"),
    ("L2b", "L2b_router.workflow",           "root"),
    ("L3a", "L3a_collaborative.concierge",   "race_concierge"),
    ("L3b", "L3b_task_desk.desk",            "race_desk"),
    ("L4a", "L4a_flat_research.deep_research", "l4a_workflow"),
    ("L4b", "L4b_recursion.deep_research",   "l4b_workflow"),
]

# graph node classes -> the map's node kinds
KIND = {"BaseNode": "start", "FunctionNode": "fn", "JoinNode": "join", "LlmAgent": "agent"}


def tool_name(t):
    return getattr(t, "__name__", None) or getattr(t, "name", None) or str(t)


def level_entry(mod, obj):
    o = getattr(importlib.import_module(mod), obj)
    g = getattr(o, "graph", None)
    entry = {
        "object": obj,
        "name": getattr(o, "name", None),
        "type": type(o).__name__,
        # null vs [] is meaningful: Pillar 2 has NO graph object, not an empty one
        "graph": None,
        "sub_agents": [{"name": s.name, "mode": getattr(s, "mode", None)}
                       for s in (getattr(o, "sub_agents", None) or [])],
        "tools": [tool_name(t) for t in (getattr(o, "tools", None) or [])],
    }
    if g is not None:
        entry["graph"] = {
            "nodes": [{"id": n.name, "kind": KIND.get(type(n).__name__, "fn")}
                      for n in g.nodes],
            "edges": [{"from": e.from_node.name, "to": e.to_node.name,
                       **({"route": e.route} if e.route else {})}
                      for e in g.edges],
        }
    return entry


def main():
    atlas = {"_generated_by": "scripts/atlas_dump.py — do not edit by hand",
             "levels": {}}
    for tag, mod, obj in LEVELS:
        atlas["levels"][tag] = level_entry(mod, obj)

    from shared.schemas import DecomposerOutput, ResearchFinding
    import L4b_recursion.deep_research as l4b

    def bound(model, field, key):
        for m in model.model_fields[field].metadata:
            if hasattr(m, key):
                return getattr(m, key)
        return None

    atlas["bounds"] = {
        "fan_min": bound(DecomposerOutput, "sub_questions", "min_length"),
        "fan_max": bound(DecomposerOutput, "sub_questions", "max_length"),
        "child_max": bound(ResearchFinding, "deeper_questions", "max_length"),
        "max_depth": l4b.MAX_DEPTH,
    }

    lv = atlas["levels"]

    # ── the teaching claims, enforced ────────────────────────────────────────
    for tag in ("P", "L0", "L3a", "L3b"):
        assert lv[tag]["graph"] is None, f"{tag} grew a graph — the map's Pillar-2/agent story is now wrong"
    for tag in ("L1", "L2a", "L2b", "L4a", "L4b"):
        assert lv[tag]["graph"], f"{tag} lost its graph"

    assert lv["L4a"]["graph"]["edges"] == lv["L4b"]["graph"]["edges"], (
        "L4a and L4b edge lists differ — the 'identical graphs, different runtime' "
        "lesson (and its map view) no longer holds")

    routes = sorted(e["route"] for e in lv["L2b"]["graph"]["edges"] if "route" in e)
    assert routes == ["COLD", "HOT", "NORMAL"], f"L2b routes changed: {routes}"

    starts = [e for e in lv["L2a"]["graph"]["edges"] if e["from"] == "__START__"]
    assert len(starts) == 3, f"L2a fan-out is {len(starts)} wide, map says 3"

    assert lv["L0"]["tools"] == ["pace_splits"], f"L0 tools changed: {lv['L0']['tools']}"
    assert lv["P"]["tools"] == [], "the prologue mega-coach acquired a tool — its lesson is that it has none"
    assert {s["mode"] for s in lv["L3a"]["sub_agents"]} == {"single_turn"}
    assert [s["mode"] for s in lv["L3b"]["sub_agents"]] == ["task"]

    OUT.write_text(json.dumps(atlas, indent=2) + "\n")
    print(f"wrote {OUT.relative_to(ROOT)}")
    for tag, e in lv.items():
        shape = (f"{len(e['graph']['nodes'])}n/{len(e['graph']['edges'])}e"
                 if e["graph"] else
                 f"no graph · {len(e['sub_agents'])} sub_agents" if e["sub_agents"] else
                 f"no graph · tools={e['tools'] or '[]'}")
        print(f"  {tag:<4} {e['type']:<9} {shape}")
    print(f"  bounds: {atlas['bounds']}")


if __name__ == "__main__":
    main()
