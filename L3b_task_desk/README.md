# L3b · Pillar 2 — task mode: a conversation with a finish line

**The question:** [L3a](../L3a_collaborative/) left a gap. `chat` owns the whole conversation; `single_turn` never talks to the user at all. But real intake work sits in between: *"talk to the user UNTIL you've collected X — then come back with a validated object."* Which mode is that?

**The shape:**
```
race_desk (coordinator)
  └─ gear_fitter (mode="task", output_schema=GearOrder)
```

## Run it
```bash
python -m L3b_task_desk.desk
python -m L3b_task_desk.desk "I need a hydration vest" --reply "2 liters, medium"
```

## What you'll see

```
━━ TURN 1 ━━  user: 'I need shoes for the marathon.'
  race_desk → delegate: gear_fitter
  gear_fitter: What is your shoe size?

  ⏸  The run ENDED — but nothing failed. This is a PAUSED task.

━━ TURN 2 ━━  user: 'Size 9, wide.'   (same session → resumes the task)
  gear_fitter → finish_task   (payload validates as GearOrder)
  race_desk: Your order for the ... in size 9 Wide has been confirmed.
```

Three things happened that neither L3a mode can do:

1. **The run genuinely stopped mid-task** — a *paused* task, not a hang and not a failure. The agent asked its clarifying question and is holding the task open. (In `adk web` you'd just type the answer; this harness scripts it as a second message on the same session.)
2. **The next message resumed the SAME task agent** — no re-routing, no re-delegation. The session knows who was waiting.
3. **`finish_task` ended it** — a tool ADK injected *because* of `mode="task"`. The agent must call it to finish, and its payload must validate against `output_schema`. A conversation with a **typed finish line** — then control auto-returns to the coordinator, result attached.

## The one-question rule for picking a mode

> **"Does the user need to talk to it — and until WHEN?"**

| 你在造什么 | Mode | The contract |
|---|---|---|
| Support assistant / open-ended copilot — the user came to *talk to it* | `chat` (subagent default) | owns the conversation; **manual** return via transfer |
| Intake, booking, troubleshooting — "collect the fields, then come back" | `task` | clarifying questions allowed; **auto-returns** via `finish_task` with a validated object |
| Classify · extract · judge · generate — the LLM as a pure function | `single_turn` | never talks to the user; auto-returns; **the only one that runs in parallel** |

`mode` goes on **subagents only** — never on the coordinator. And workflow *nodes* default to `single_turn` (which is why L1–L2b never wrote it), while *subagents* default to `chat` (which is why L3a had to).

## Version notes (worth knowing before you build on this)

- **`task` as a static graph node is version-dependent:** on 2.0.0b1–2.3.0 (this repo's pin), `Workflow(...)` raises at construction if a `task` agent is a graph node — use exactly what this level does (a chat coordinator with task sub-agents) or dispatch via `ctx.run_node`. **Lifted in 2.5.0.**
- **"Task agents must be leaf agents"** (no subagents of their own) is a documented ADK limitation — but a *contract*, not a runtime guard: neither 2.3.0 nor 2.5.0 will stop you. Don't read the absence of an error as permission.

## Go deeper

A `task` agent embedded in a *graph workflow* (the 2.5.0+ shape), with routing that can loop the conversation back for a retry: companion repo [`22_agent_in_workflow`](https://github.com/cuppibla/adk-workflows-compared/tree/main/examples/22_agent_in_workflow) · full mode guide: [`docs/agent-modes.md`](https://github.com/cuppibla/adk-workflows-compared/blob/main/docs/agent-modes.md).

→ **Next:** [L4a](../L4a_flat_research/) — Pillar 3: when even the *shape* of the work is unknown until runtime.
