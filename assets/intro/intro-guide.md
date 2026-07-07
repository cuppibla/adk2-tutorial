# ADK 2 Orchestration — series intro (felt marathon cold-open)

A ~8–11s needle-felted stop-motion cold-open: the felt mascot **runs a marathon**, through the
three pillar-colored zones, crosses the finish, and the **ADK 2 · Orchestration** felt title
reveals. Same felt world + brand mascot as the diagrams, so the whole series reads as one show.

Pipeline (same as your Agent 101 intro): **Frames-to-Video** — the 4 keyframes below are the
start/end frames; put **motion in the Veo prompt, content is already in the frames.** End frame of
clip N == start frame of clip N+1, so the seams match.

## The 4 keyframes (already generated → `assets/intro/`)

| # | file | what it shows |
|---|---|---|
| KF1 | `kf1-start.png` | mascot crouched at the felt **START** banner, "2" race bib, track curves away |
| KF2 | `kf2-run.png` | mascot mid-run through the 3 colored zones (dusty-blue → sage → honey) |
| KF3 | `kf3-finish.png` | mascot breaking the coral **FINISH** ribbon under a checkered-flag arch |
| KF4 | `kf4-title.png` | chunky felt **ADK 2 · Orchestration** title on the wall, mascot waving with a medal |

## Style tag — paste into EVERY clip
> `needle-felted stop-motion, handmade wool, warm cream studio, pastel felt in dusty-blue / sage-green / honey-yellow / coral, soft warm light, gentle handheld micro-motion, shallow depth of field, adorable, 16:9`

## The clips (Frames-to-Video, motion only)

| Clip | Start → End | Prompt (motion only) | Len |
|---|---|---|---|
| **A** | `kf1-start` → `kf2-run` | "The felt mascot pushes off the start line and begins running to the right; the camera pans to follow as the felt track scrolls past. Springy stop-motion bounce, gentle handheld." | 3–4s |
| **B** | `kf2-run` → `kf3-finish` | "The mascot keeps running happily through the three colored zones and reaches the finish, breaking the thin coral ribbon tape with its arms rising in celebration. Camera follows, then settles." | 3–4s |
| **C** | `kf3-finish` → `kf4-title` | "The checkered finish flag and floating confetti resolve upward into the chunky 3D felt 'ADK 2' title assembling on the cream wall; the mascot steps to the side and waves. Slow push-in, satisfying settle." | 2–3s |
| **→ live** | `kf4-title` → your footage | *Not Veo — in your editor:* cross-dissolve (cream wall → your background) into your talking-head. | — |

## Negative prompt — paste into every clip
> `no text changing or flickering, no extra letters, no morphing faces, no warping, no fast whip, no color shift, no distorted robot, no duplicate mascot`

## Consistency + tips
- Same **style tag** + **16:9** on every clip. If a new shot drifts, drop `kf4-title.png` or
  `kf1-start.png` in as a **reference/ingredient** so the mascot + world hold.
- Generate **2–3 takes per clip**, keep the cleanest — felt stop-motion quality varies per gen.
- Camera words that work: *pan to follow · slow push-in · gentle handheld · settle to a hold.*
- **Punchier cold-open?** Use only Clip B + Clip C (run → finish → title) for a ~5–6s version.

## Make the GIF / video
- Stitch clips A→B→C in your editor, then the live dissolve.
- **GIF:** export the stitched intro to MP4, then `ffmpeg -i intro.mp4 -vf "fps=15,scale=960:-1:flags=lanczos" intro.gif` (or a palette pass for cleaner color). Loops nicely if you end on the title hold.
- **Where it goes:** top of the codelab **Overview** step, the notebook **intro** cell, or the
  YouTube video cold-open — then dissolve into content.

## Want me to regenerate any keyframe?
Ask for variants (e.g. "3 takes of KF3", "mascot with sunglasses", "add tiny L0–L5 flags on the
track", "warmer light"). Same chat-session seeding keeps the mascot consistent.
