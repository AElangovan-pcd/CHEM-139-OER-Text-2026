# Deploying CHEM 139 OER pages to Instructure Canvas

This document describes how to publish the chapter HTML pages produced by
`.firecrawl/build_html.py` into Instructure Canvas, including how images
should be handled.

> The HTML files in `HTML_Files/` are the *standalone* preview build —
> they include the full `<html>` / `<head>` chrome, MathJax CDN bootstrap,
> and the JavaScript that swaps the "Show solution" pill to "Hide
> solution". Canvas's Page editor strips most of that on save. Use the
> Canvas-tailored output in `HTML_Files_Canvas/` instead.

## TL;DR

```bash
# 1. Build the preview HTML (always do this first; it reads from .docx).
python .firecrawl/build_html.py

# 2. Build the Canvas-tailored HTML.
python .firecrawl/build_canvas.py

# 3. For each chapter:
#    Open HTML_Files_Canvas/Chapter_NN.html in a text editor, copy ALL of it.
#    In Canvas: Pages -> + Page -> click </> (HTML editor) -> paste -> Save.
```

Each Canvas Page now has working `<details>`/`<summary>` "Show solution"
toggles, MathJax-rendered factor-label math (Canvas auto-typesets `\(...\)`
and `\[...\]`), figure-description boxes, problem numbering, and inline
styling that survives the Canvas sanitizer.

## Path A — One Canvas Page per chapter (recommended for student access)

This is the path that `build_canvas.py` is designed for.

### What `build_canvas.py` does

For each file in `HTML_Files/` (except `index.html` — Canvas has its own
module navigation):

| Transformation | Reason |
|---|---|
| Strip `<html>`, `<head>`, header/footer nav | Canvas Pages are content-only. |
| Drop `<script>` tags (MathJax CDN, print hooks, label-swap JS) | Canvas removes JS on save. Canvas's built-in MathJax handles equations. |
| Replace `<summary>Show solution</summary>` with two `<span>`s | CSS-only `Show solution` ↔ `Hide solution` swap that works without JS. |
| Inline static CSS rules onto each element via `style="…"` | Canvas allows the `style` attribute but may strip large `<style>` blocks. |
| Keep a small `<style>` block at the top for `[open]`, `:hover`, `::before`, `@media print` | These selectors *cannot* be inlined. Most Canvas instances preserve `<style>` inside Page content; if yours strips it, the page still works — only the open-state label swap and hover effect are lost. |
| Wrap the body in `<div class="oer-page">` | Scopes the `<style>` rules so they cannot leak into Canvas chrome. |
| Rewrite `<img src="…">` via an optional `image_map.json` | See **Images** below. |

### Pasting into Canvas

1. In Canvas, navigate to the course → **Pages** → **+ Page**.
2. Title the page (e.g. `Chapter 2 — Unit Systems and Dimensional Analysis`).
3. Click the **`</>` HTML editor** button at the top right of the editor.
4. Open `HTML_Files_Canvas/Chapter_02.html` in a plain-text editor (VS Code,
   Notepad++, TextEdit). Copy the entire file contents.
5. Paste into the Canvas HTML editor. Click **Save & Publish**.
6. View the page; click any "Show solution" pill — it should expand and the
   pill text should switch to "Hide solution". Math should typeset within
   1–2 seconds via Canvas's MathJax.

### Bulk publishing (optional)

The Canvas API can create Pages programmatically from these files. A short
Python script using `requests` + an [API token](https://community.canvaslms.com/t5/Admin-Guide/How-do-I-manage-API-access-tokens-as-an-admin/ta-p/89)
posts each `.html` to
`POST /api/v1/courses/<course_id>/pages` with the `body` set to the file
contents. Useful when you have to refresh 14 pages after every chapter
revision. Ask if you'd like that script added to `.firecrawl/`.

## Path B — Host the HTML elsewhere, embed via `<iframe>`

If your Canvas admin is restrictive about `<style>` or you want to keep
the original chrome / MathJax CDN setup, host `HTML_Files/` on a static
host and embed each chapter via iframe:

```html
<iframe src="https://YOUR-HOST/Chapter_02.html"
        width="100%" height="1200"
        style="border:0;"
        loading="lazy"
        title="Chapter 2 — Unit Systems and Dimensional Analysis">
</iframe>
```

Hosting options:

* **GitHub Pages** — free, public; push the repo, enable Pages, point at
  `HTML_Files/`. Works fine for OER content under CC BY 4.0.
* **Netlify / Vercel** — same idea; drag-and-drop deploys.
* **Canvas Files area** — upload the `HTML_Files/` folder; reference each
  page at
  `https://<your>.instructure.com/courses/<id>/files/<file_id>/preview`.
  Useful if your institution's CSP blocks external iframes.

For external hosts, your Canvas admin may need to add the host to the
**Account → Settings → Content Security Policy** allow-list before
Canvas will render the iframe.

## Images

### Current state

The HTML pages currently contain **no `<img>` tags**. Per the project's
text-first accessibility design (see `CLAUDE.md`), figures live in the
`.docx` source as **FIGURE DESCRIPTION blocks** — text descriptions and
alt-text used by screen readers and graphic designers, not raster images.
The build pipeline carries those blocks through unchanged.

### When you add real images

Canvas serves images via per-file URLs that only Canvas can mint —
something like
`https://<your>.instructure.com/courses/<id>/files/<file_id>/preview`.
Hand-writing `src="/files/123"` or relative paths **will not work** for
students who don't have direct file access; Canvas's auth layer rejects
such requests.

The recommended workflow:

1. **Upload images** to Canvas Files. Mirror the project's structure —
   create one folder per chapter (`Chapter_01/`, `Chapter_02/`, …).
2. **Get a file ID** for each image. The Canvas File picker shows it; the
   API also returns it (`GET /api/v1/courses/<id>/files`).
3. **Build an `image_map.json`** — a flat dict mapping the image filename
   (or path) you'll use in the OER source to the canonical Canvas URL.
   Example:

   ```json
   {
     "images/figure_2_1_density_cubes.svg":
       "https://yourschool.instructure.com/courses/12345/files/678901/preview",
     "images/figure_2_2_temperature_scales.svg":
       "https://yourschool.instructure.com/courses/12345/files/678902/preview"
   }
   ```

4. **Re-run the Canvas build** with the map:

   ```bash
   python .firecrawl/build_canvas.py --image-map image_map.json
   ```

   Every `<img src="...">` whose source matches a key in the map is
   rewritten to the Canvas URL. The HTML you paste then renders images
   without further intervention.

5. **Re-paste** the affected pages into Canvas. (Or use the bulk-publish
   API script.)

The point of the image-map indirection is that you never put Canvas-
specific URLs into the `.docx` source. The same OER content can ship to a
public web build (paths are relative), to one school's Canvas (mapped to
that school's file IDs), to another school's Canvas, and so on, just by
swapping the JSON.

### Inline raster vs. linked

For small icons / equations / diagrams, you can also embed images as
**Base64 data URIs** directly in the HTML — no upload needed, but the
page weight grows. `data:image/svg+xml;base64,…` works for SVG figures
under ~50 KB. For the typical chemistry textbook figure (a few hundred
KB), per-file Canvas Files upload is the right call.

## Math rendering

Canvas ships **MathJax 3** globally and recognises `\(...\)` (inline) and
`\[...\]` (display) delimiters — the same delimiters `build_html.py`
emits. So equations should auto-typeset on save without any per-page
configuration.

Two caveats:

* **`\cancel{...}` extension** — used heavily in the dimensional-analysis
  factor-label rewrites — is **not** in the default Canvas MathJax bundle
  on every Canvas instance. If your `\cancel{km}` lines render as raw
  text instead of crossed-out, ask your Canvas admin to enable the
  `cancel` package via custom JS:

  ```js
  // Add to Account → Settings → Custom JavaScript
  window.MathJax = window.MathJax || {};
  window.MathJax.loader = window.MathJax.loader || {};
  (window.MathJax.loader.load = window.MathJax.loader.load || []).push("[tex]/cancel");
  (window.MathJax.tex = window.MathJax.tex || {}).packages =
    {"[+]": ["cancel"]};
  ```

  No admin? Pre-render the math to SVG with `mjpage` (npm:
  `mathjax-node-cli`) and bake it into the HTML before pasting. Ask if
  you want a pre-render flag added.

* **Inline math** — currently the build only emits **display** math (`\[...\]`).
  If you ever change the converter to emit inline math, use `\(...\)`,
  not `$...$` or `$$...$$` — Canvas does **not** recognise dollar-sign
  delimiters by default.

## Show / Hide solution toggle

The local HTML preview uses JavaScript to swap the pill text on
`<details>` `toggle` events. Canvas strips JS, so the Canvas build
substitutes a **CSS-only swap** that depends on the `details[open]`
attribute selector.

The CSS sits in a small `<style>` block at the top of each Canvas page.
If your Canvas instance preserves `<style>` (most do, even strict
sanitizers preserve it inside Page content), the swap works. If your
Canvas strips `<style>` outright, the toggle still **functions**
(clicking expands the solution) — you just lose the label switch and the
arrow rotation. The pedagogy still holds.

## Updating a published page

When a chapter changes:

1. Edit the source `.docx`.
2. Re-run `python .firecrawl/build_html.py`.
3. Re-run `python .firecrawl/build_canvas.py [--image-map …]`.
4. Open the corresponding Canvas Page → **Edit** → **`</>`** → select all
   → paste the new content → Save.

For frequent updates, the Canvas API bulk-publish script is faster.

## Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| Pill renders as `Show solutionHide solution` (both labels) | Canvas stripped the `<style>` block. | Either ask admin to allow `<style>` in Pages, or remove the `<style>` block and accept the static "Show solution" label. |
| Math renders as `\[2.50 \cancel{\text{km}} ...\]` literally | Canvas's MathJax has not loaded yet (race) **or** `\cancel` extension is missing. | Reload the page; if persistent, see the `cancel` extension fix above. |
| Solution boxes are unstyled grey rectangles | The inline-CSS pass was bypassed (e.g. you pasted from `HTML_Files/` instead of `HTML_Files_Canvas/`). | Repaste from the `HTML_Files_Canvas/` version. |
| Tables overflow the Canvas content area | Canvas's responsive layout is narrower than the standalone preview's 800 px max-width. | Either accept the horizontal scroll Canvas provides, or hand-edit the table's inline `style="max-width:…"`. |
| Images broken (404) | Canvas File URLs not yet in `image_map.json`, or images uploaded to a different course. | Update the JSON and rebuild. Each course needs its own map (file IDs are course-scoped). |

## What's in `HTML_Files_Canvas/`

After running the build:

```
HTML_Files_Canvas/
├── 00_Front_Matter.html
├── Book_Index.html
├── Chapter_01.html
├── Chapter_02.html
├── …
├── Chapter_10.html
├── Formula_and_Constant_Reference_Sheet.html
└── Periodic_Table_Reference_Page.html
```

Each file is body-only HTML — paste-ready into a Canvas Page's HTML
editor. No build chain or runtime is required on Canvas's side beyond
the MathJax that Canvas itself provides.
