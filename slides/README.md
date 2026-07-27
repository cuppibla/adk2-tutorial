# ADK 2 Orchestration — the talk

`adk2-orchestration.pptx` · 30 slides · about 40 minutes plus questions · 16:9

---

## What this class is about

Most people meet agent frameworks the same way: you write one big prompt, hand it
every job you can think of, and it answers fluently — with numbers it invented,
steps you cannot test, and branches you cannot see. The prompt works right up
until it matters.

This session is about getting those steps **out of the prompt**. ADK 2 offers
three ways to arrange agents, and the whole talk turns on one question that
separates them:

> **Who decides what runs next — the graph you drew, the LLM, or your code?**

We answer it three times. Everything else follows from that.

## What you'll learn

- **Why orchestration exists at all** — we run the one-giant-prompt version live
  and read the output closely enough to see it inventing its own inputs.
- **What ADK and ADK 2 actually are** — an agent is a model, an instruction and
  tools; a Runner executes it. Everything after that is more agents in better
  shapes.
- **An honest ADK 1.x vs 2 comparison** — 1.x could already build all of this.
  What 2 changes is that each shape gets a direct home, so known control flow
  leaves the prompt and becomes structure you can see and test.
- **Pillar 1 · Graph workflows** — for flows you can draw before any input
  arrives: parallel fan-out, a real join, and branching decided by an
  `if`-statement instead of by the model.
- **Pillar 2 · Collaborative agents** — for when you know the team but the
  request picks the subset, plus the one question that chooses between the three
  modes: does the user need to talk to it, and until when?
- **Pillar 3 · Dynamic workflows** — for when the shape of the work depends on
  the input, including why recursion is something you write, and therefore
  something you must bound yourself.
- **How to choose** — a decision tree that starts by asking whether you need any
  of this, since a prebuilt Sequential, Parallel or Loop agent is often the
  cheapest correct answer.

## How it's taught

One app throughout — a **Marathon Race Day Coach** — assembled one runnable rung
at a time, so each pattern arrives with a reason rather than as a feature tour.

Every claim is closed by a real terminal run. When the talk says three fetches
happen in parallel, you see three timestamps at t≈0.0. When it says a task pauses
for a human, you watch the run end and then resume on the next message. Nothing
is asserted that isn't shown.

## Who it's for

Developers who have built an agent or two and have started to feel the ceiling of
a single large prompt. Python familiarity is assumed; no prior ADK experience is.

## Going further

The companion hands-on lab in this repository takes about 50 minutes and covers
the same nine rungs, with the code in your own terminal. Start at
[`codelab/`](../codelab/) or open the
[Colab notebook](https://colab.research.google.com/github/cuppibla/adk2-tutorial/blob/main/notebooks/adk2_orchestration.ipynb).

---

## About this file

16:9, 13.333×7.5in. Import into Google Slides with **File → Import slides**.

Each page is a full-frame 2× render (3840×2160) of a React deck, so the PPTX is
pixel-identical to the web version and carries the felt typography exactly. The
trade-off: **text is not editable after import.** To change a slide, edit the
source and re-export rather than editing the PPTX.

Six of the thirty pages are the lab's own diagrams used full-bleed — they were
already 2560×1440 with an eyebrow, title and mascot, so they were slides all
along. The whole-app page is `assets/felt/diagram-whole.png` cut into its three
pillar lanes, which is why it stays legible at projector size.

Source lives outside this repo (Vite + React; `slides.jsx` holds all 30 slides as
data, `layouts.jsx` the eight layout components). Regenerate with:

```
npm run build
node scripts/export_pptx.mjs <2x-render-dir> export/adk2-orchestration.pptx
```

Design tokens are lifted verbatim from `assets/diagrams.html`, so the deck and the
lab diagrams can never drift apart.
