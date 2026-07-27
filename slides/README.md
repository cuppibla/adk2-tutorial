# Talk slides

`adk2-orchestration.pptx` — a 30-slide live-talk deck that walks through this lab,
structured **Why → What → How**: why orchestration is needed at all, what ADK and
ADK 2 actually are (including an honest 1.x-vs-2 comparison), then each of the
three pillars with a real terminal run as evidence.

16:9, 13.333×7.5in. Import into Google Slides with **File → Import slides**.

## How it was made

Each page is a full-frame 2× render (3840×2160) of the React deck, so the PPTX is
pixel-identical to the web version and carries the felt typography exactly. The
trade-off: **text is not editable after import.** To change a slide, edit the
source and re-export rather than editing the PPTX.

Six of the thirty pages are the lab's own diagrams used full-bleed — they were
already 2560×1440 with an eyebrow, title and mascot, so they were slides all
along. The whole-app page is `assets/felt/diagram-whole.png` cut into its three
pillar lanes, which is why it stays legible at projector size.

Source lives outside this repo (Vite + React, `slides.jsx` holds all 30 slides as
data, `layouts.jsx` the eight layout components). Regenerate with:

```
npm run build
node scripts/export_pptx.mjs <2x-render-dir> export/adk2-orchestration.pptx
```

Design tokens are lifted verbatim from `assets/diagrams.html`, so the deck and the
lab diagrams can never drift apart.
