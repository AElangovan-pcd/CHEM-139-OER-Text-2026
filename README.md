# CHEM 139 — Introduction to Chemical Principles (2026 ed.)

[![License: CC BY 4.0](https://img.shields.io/badge/License-CC%20BY%204.0-lightgrey.svg)](https://creativecommons.org/licenses/by/4.0/)

An Open Educational Resource (OER) introductory chemistry textbook for one-quarter / one-semester community-college courses. Designed to be used without prior chemistry; assumes high-school algebra. This repo holds the **authored content** (Microsoft Word `.docx` per chapter) plus a small build pipeline that turns it into an HTML preview and Canvas-ready Pages.

> **Suggested pacing**: 10-week course = 2 weeks on Ch 1, 1 week each on Ch 2–10.

## What's in this repo

| Path | What |
|---|---|
| `Chapter_NN_*.docx` | Ten chapter source files. Each follows a common template (see [`CLAUDE.md`](CLAUDE.md)). |
| `Front_Matter_Preface_License.docx` | Preface, license, chapter map, accessibility statement, data-source provenance. |
| `Index.docx`, `Formula_and_Constant_Reference_Sheet.docx`, `Periodic_Table_Reference_Page.docx` | Reference back matter. |
| `Images/Chapter_NN/ManifestForChapter_NN.docx` | Per-chapter image manifests for instructors / graphic designers. The chapters themselves ship with **text descriptions** (FIGURE DESCRIPTION blocks) in place of pictures — see "Why text-first" below. |
| `Briefs/Brief_Figure_X.Y.md` | Standalone Markdown lifts of figure descriptions, sized for designer reconstruction. |
| `HTML_Files/` | Generated standalone HTML preview (one page per chapter + `index.html`). Open `HTML_Files/index.html` in any browser. |
| `HTML_Files_Canvas/` | Generated Canvas Page-ready body markup. See [`CANVAS_DEPLOYMENT.md`](CANVAS_DEPLOYMENT.md) for the workflow. |
| `.firecrawl/` | Editorial scaffolding: build scripts (`build_html.py`, `build_canvas.py`, `rewrite_engine.py`, `rewrite_ch08.py`, …) and Firecrawl-scraped OpenStax source material used during authoring. |
| [`CLAUDE.md`](CLAUDE.md) | Project conventions for future editorial collaborators (human or LLM). |
| [`CANVAS_DEPLOYMENT.md`](CANVAS_DEPLOYMENT.md) | End-to-end guide for publishing chapters into Instructure Canvas. |

## Build the HTML

Two Python dependencies: [`python-docx`](https://pypi.org/project/python-docx/) and [`mammoth`](https://pypi.org/project/mammoth/), plus `beautifulsoup4`.

```bash
pip install python-docx mammoth beautifulsoup4

# Standalone HTML preview (open HTML_Files/index.html afterward)
python .firecrawl/build_html.py

# Canvas Page-ready body markup (paste each into a Canvas Page's </> editor)
python .firecrawl/build_canvas.py
```

The standalone build produces collapsible "Show solution / Hide solution" toggles, MathJax-rendered factor-label math (with `\cancel{}` crossing out cancelled units), and shaded FIGURE DESCRIPTION boxes. The Canvas build inlines CSS, swaps the JS toggle for a CSS-only equivalent, and strips any `<script>` tags Canvas would reject.

## Editing the chapters

Source of truth is the `.docx` files — open in Word or LibreOffice. The chapter template (Heading 1 title, Chapter Opener, Learning Outcomes, numbered Parts → Sections, FIGURE DESCRIPTION blocks, Concepts to Remember, Key Terms, Practice Problems, Multi-Concept Problems, Multiple-Choice Practice Test, Instructor Notes) is load-bearing — instructor- and student-facing front matter promises this consistency. Don't break it; see `CLAUDE.md` for the full set of conventions.

After editing a `.docx`, rerun the two build commands above to refresh the HTML.

### Programmatic edits

When a change is too repetitive for hand-editing — e.g. rewriting every Solution paragraph in a chapter into factor-label form with strikethrough on cancelled units and an italic explanation — use `python-docx` rather than surgically editing `word/document.xml`. Several precedents live in `.firecrawl/`:

| Script | What it does |
|---|---|
| `rewrite_engine.py` | Generic rewrite engine that takes a per-chapter `REWRITES` data list. |
| `rewrite_solutions_ch02.py`, `rewrite_ch08.py` | Per-chapter REWRITES data for the dimensional-analysis pass (Ch 2) and the mole-concept pass (Ch 8). |
| `auto_rewrite_solutions.py` | Best-effort parser that auto-applies strikethrough where existing Solutions already use a factor-label form. |
| `a11y_pass.py`, `a11y_fix.py`, `a11y_sublists.py` | WCAG 2.2 cleanup — converts typed-numbered "1. " problems into real Word ordered-list items, fixes sub-list indentation, etc. |
| `insert_practice.py`, `additional_problems.py` | Adds new "Additional Practice Problems by Topic" sections to each chapter. |
| `build_periodic_table.py` | Generates the periodic table reference page. |

All scripts back up the original to `.firecrawl/backups/` before writing.

## Why text-first figures?

The chapters ship with FIGURE DESCRIPTION blocks rather than embedded raster images. This is a **deliberate accessibility choice** under WCAG 2.2 — the descriptions double as screen-reader alt-text and as reconstruction notes for graphic designers. When the designer pass produces real figures, the per-chapter manifest in `Images/Chapter_NN/` says where those figures should be sourced (preferring CC BY 4.0 / public-domain providers like OpenStax Chemistry 2e, Wikimedia Commons, NIST Chemistry WebBook, NASA, USGS).

For Canvas deployment, see the **Images** section of `CANVAS_DEPLOYMENT.md` — the build pipeline supports an `image_map.json` so once images are uploaded to a specific Canvas course's Files area, one JSON flips every `<img src="…">` to the canonical Canvas URL without changing the source content.

## Status of the dimensional-analysis rewrite

A multi-pass effort to render every numerical Solution in factor-label form, with cancelled units shown by Word strikethrough and an italic explanatory paragraph naming what cancels and why the answer has the sig figs it has.

| Chapter | Status | Notes |
|---|---|---|
| Ch 2 — Unit Systems & Dimensional Analysis | ✅ Complete | 62 Solutions rewritten; 55 LaTeX math chains in HTML. |
| Ch 8 — Mole Concept | ✅ Complete | 56 Solutions rewritten; 107 LaTeX math chains in HTML. |
| Ch 9 — Chemical Calculations / Stoichiometry | ⏳ Pending | Math-heavy — next priority. |
| Ch 10 — States of Matter / Gas Laws | ⏳ Pending | Math-heavy — second priority. |
| Ch 1 — Science & Measurement | ⏳ Pending | Mostly conceptual; ~15 numerical Solutions. |
| Ch 3, 4, 5, 6, 7 | ⏳ Light pass pending | Mostly qualitative Solutions; a small number of numerical ones to convert. |
| Worked Examples in chapter prose (all chapters) | ⏳ Pending | "Step N — …" lines need the same treatment as the labelled Solutions. |

## Numerical-data sources

Numerical content matches the front-matter promises:

- **Atomic masses** — IUPAC 2021 standard atomic weights
- **Physical constants** — CODATA 2018
- **Authoritative references** — NIST, IUPAC, BIPM, CODATA, USGS, CRC Handbook

If a number disagrees with these references, the references win and the discrepancy gets flagged.

## License

This work is licensed under a [Creative Commons Attribution 4.0 International License (CC BY 4.0)](https://creativecommons.org/licenses/by/4.0/).

You are free to share and adapt the material, including for commercial use, as long as you give appropriate credit. Anything you contribute back must remain CC BY 4.0-compatible — see the *License compatibility* section of [`CLAUDE.md`](CLAUDE.md) for the rules around incorporating third-party material (CC BY-SA, CC BY-NC, CC BY-ND, etc.).

## Contact

Author: A. Elangovan ([aelangovan.pcd@gmail.com](mailto:aelangovan.pcd@gmail.com))

For corrections, errata, or pedagogical suggestions, open an issue on this repository.
