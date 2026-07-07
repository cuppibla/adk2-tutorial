# The codelab (claat)

`adk2-orchestration.md` is a [claat](https://github.com/googlecodelabs/tools)-format codelab that **wraps the Colab notebook** into a graded, step-by-step walkthrough — the same format as codelabs.developers.google.com. Each step maps to one Colab cell (and one repo folder).

## Preview locally

```bash
# install claat once (needs Go):
go install github.com/googlecodelabs/tools/claat@latest
export PATH="$PATH:$(go env GOPATH)/bin"

# live preview with hot reload:
claat serve            # opens a browser; edit the .md and refresh

# or build the static HTML:
claat export adk2-orchestration.md   # → ./adk2-orchestration/index.html
```

The build output folder (`adk2-orchestration/`) is git-ignored — it's regenerated from the `.md`.

## Publish

- **codelabs.developers.google.com** — submit the `.md` through the Google codelabs pipeline (the `id:` becomes the URL slug).
- **Self-host** — serve the exported `adk2-orchestration/` folder anywhere static (GitHub Pages, Firebase Hosting, etc.).

## Before publishing — update these

1. **Colab URL** — the badge and "Open in Colab" links point at `github.com/cuppibla/adk2-tutorial/.../notebooks/adk2_orchestration.ipynb`. Fix the owner/repo/branch once pushed.
2. **`feedback link`** and repo links in the metadata header.
3. `status:` is `Published` — set to `Draft` while iterating.

## Format notes (this claat build uses the goldmark parser)

- **Steps** are `##` headings; put `Duration: N` (minutes) right under each.
- **Info boxes** use blockquote syntax:
  ```
  > aside positive
  > Green "tip" box.

  > aside negative
  > Yellow "warning" box.
  ```
  (The older `Positive` / `: text` definition-list syntax does **not** render in this parser — it prints literally.)
