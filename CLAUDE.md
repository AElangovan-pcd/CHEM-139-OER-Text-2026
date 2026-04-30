# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repo is

CHEM 139 — *General Chemistry Prep*, an Open Educational Resource (OER) textbook for one-quarter / one-semester community-college introductory chemistry (2026 edition). It is **content first, with a small build pipeline** — the source of truth is one Microsoft Word `.docx` per chapter, and a handful of Python scripts in `.firecrawl/` regenerate three publication artefacts (standalone HTML preview, Canvas Page-ready HTML, IMSCC Common Cartridge). There is no test suite, lockfile, or CI. Tasks here are mostly editorial — revising prose, fixing chemistry, adjusting figure descriptions, updating manifests — with occasional rebuilds of the artefacts.

License: **CC BY 4.0**. Anything added must remain compatible (see "License compatibility" below).

## Repository layout

Top level holds one `.docx` per chapter plus front/back matter:

- `Front_Matter_Preface_License.docx` — preface, license, chapter map, "how to use" sections, accessibility statement, data-source provenance. Includes 'A Note from the Author' (Heading 2, signed by A. Elangovan PhD) immediately before the License section — added 2026-04-29.
- `Chapter_01_…docx` … `Chapter_10_…docx` — the ten chapters. Filenames are stable; do not rename.
- `Formula_and_Constant_Reference_Sheet.docx`, `Periodic_Table_Reference_Page.docx`, `Index.docx` — reference back matter.
- `Images/` — does **not** contain images. It contains one manifest per chapter (`Images/Chapter_NN/ManifestForChapter_NN.docx`) plus `Image_Sourcing_Guide_for_Instructors.docx` at the root of `Images/`. Manifests tell instructors where to source openly-licensed figures; chapters ship with text descriptions in place of pictures.
- `.~lock.<filename>#` — a LibreOffice/Word lock file. If you see one, the user has that document open; warn before writing. A lock file may persist for a file that no longer exists in the repo (e.g. an exported PDF that was moved away) — that's harmless and can be ignored.

## Lean-remote policy (set 2026-04-29)

Only what GitHub Pages CI needs is tracked in the public remote: the `.docx` chapter sources, `build_html.py`, the workflow file, and the `HTML_Files/` snapshot for in-repo review. Everything else under `.firecrawl/` — every `rewrite_*.py`, `a11y_*.py`, `insert_*.py`, `audit_*.py`, `build_canvas.py`, `build_imscc.py`, the OpenStax markdown scrapes, the per-section JSON briefs — exists locally on the author's machine but is gitignored. `HTML_Files_Canvas/` and `CHEM_139_OER.imscc` are likewise local-only.

When this CLAUDE.md references a script that isn't tracked, it's documenting a precedent that lives on the author's disk. Check `ls .firecrawl/` before invoking; on a fresh clone you'll only find `build_html.py`.

## Working directories (editorial workshop, not part of the published book)

These directories hold scaffolding for editing the chapters; their contents are not shipped to students:

- **`Briefs/`** — one `Brief_Figure_X.Y.md` per figure that needs designer reconstruction. Each brief lifts the FIGURE DESCRIPTION block (alt text, description, caption) out of its chapter into a standalone Markdown file a graphic designer can work from. When you create or edit a FIGURE DESCRIPTION block in a chapter, mirror it here if a brief already exists for that figure number.
- **`.firecrawl/`** — local automation scratch space (gitignored except for `build_html.py`; see "Lean-remote policy" above). On the author's machine it contains `python-docx` scripts that have been run against these chapters (`a11y_fix.py`, `a11y_pass.py`, `a11y_sublists.py`, `insert_practice.py`, `insert_ch1_images.py`, `insert_author_note.py`, `move_practice_above_mixed.py`, `additional_problems.py`, `build_periodic_table.py`, …), Firecrawl-scraped OpenStax source material (`os-N-N.md`, `cat-*.md`, `file-*.md`), per-section JSON briefs (`s-N-N.json`), and a `backups/` directory. Before writing a new automation script, check here — there is probably a precedent that already handles styles, numbering, and the chapter template correctly.
- **Root-level reference PDFs** (e.g. `acs-periodic-table-poster_download.pdf`) — downloaded source material for figure sourcing. Not authored content.

## Build pipeline

`build_html.py` (in `.firecrawl/`) is the only build script tracked in the public remote. It depends on `python-docx`, `mammoth`, and `beautifulsoup4`.

| Command | Output | Use |
|---|---|---|
| `python .firecrawl/build_html.py` | `HTML_Files/` | Standalone preview — open `HTML_Files/index.html` in any browser. JS toggles for "Show solution / Hide solution"; MathJax for factor-label math with `\cancel{}` on cancelled units; shaded FIGURE DESCRIPTION boxes; `<details class="instructor-notes">` collapsing the per-chapter Instructor Notes section behind a "Show Instructor Notes" pill. |

**Local-only build scripts (not in the remote, present on the author's machine):**

- `build_canvas.py [--image-map image_map.json]` → `HTML_Files_Canvas/`. One file per chapter, pasteable into a Canvas Page's `</>` editor. Inlines CSS, swaps the JS toggle for a CSS-only `<details>` equivalent, strips `<script>` tags. The `--image-map` flag rewrites every `<img src="…">` against a flat `{relative_path: canvas_url}` JSON. See `CANVAS_DEPLOYMENT.md` → *Images*.
- `build_imscc.py` → `CHEM_139_OER.imscc`. IMS Common Cartridge for one-shot import (Settings → Import Course Content → Common Cartridge). Preferred deployment path; see `CANVAS_DEPLOYMENT.md`.

If you're working in a fresh clone of the public remote, only `build_html.py` will be present. If you need the Canvas or IMSCC artefact, ask the author rather than reconstructing the script.

After any non-trivial editorial change, rebuild **all three** artefacts so they stay in sync. The IMSCC bundle is what gets imported to Canvas; the loose Canvas HTML is the fallback for one-off page edits; the standalone HTML is for local preview.

### CI: GitHub Pages auto-publish

`.github/workflows/pages.yml` runs `build_html.py` on every push to `main` and on manual dispatch, then deploys the result to <https://aelangovan-pcd.github.io/CHEM-139-OER-Text-2026/>. The deployed site is regenerated from the `.docx` sources each run; the committed `HTML_Files/` is just a convenience snapshot for in-repo review and is not the source of truth for what students see. Only `build_html.py` runs in CI — Canvas (`build_canvas.py`) and IMSCC (`build_imscc.py`) builds are still local-only because they're tied to a specific Canvas course's import workflow.

## Reading and editing `.docx` from Claude Code

`.docx` is a ZIP. To read text without Word:

```bash
unzip -p "Chapter_01_Science_and_Measurement.docx" word/document.xml \
  | sed -E 's/<[^>]+>/ /g; s/  +/ /g'
```

Use this for inspection, search, quoting passages, and fact-checking. **Do not** attempt to surgically edit `word/document.xml` and re-zip — Word's XML is brittle (numbering, styles, relationships in `word/_rels/`, content types) and a hand-edit will usually corrupt the file. For real edits:

1. Quote the existing passage to the user, propose the change in plain text, and let the user apply it in Word; **or**
2. Regenerate the affected `.docx` with `python-docx`. Several precedents live in `.firecrawl/` — read those before writing a new script so you preserve the chapter template (styles, numbering, FIGURE DESCRIPTION shading, etc.). Always write to a backup first.

When in doubt, ask before writing to a `.docx`. Never write to a file while its `.~lock.…#` sibling exists.

**Gotcha — Worked Examples live inside Word tables.** Many Worked Example boxes in the chapter prose are implemented as single-cell shaded tables, not flowing paragraphs. `doc.paragraphs` walks only top-level paragraphs and silently skips them. Any script that scans or rewrites Worked Examples must recurse into `doc.tables` → `cell.paragraphs` (and into nested tables, if any). The Solution paragraphs that live in the body prose between Practice Problems are *not* in tables — only the boxed Worked Examples are.

## Chapter document structure (load-bearing conventions)

Every chapter follows the **same template**, and instructor/student instructions in the front matter promise this consistency. Preserve it when editing or regenerating:

1. Heading 1 chapter title → `Chapter N: <Title>` plus the standard subtitle line `CHEM 139 — General Chemistry Prep · Open Educational Resource (2026 ed.)` and the CC BY 4.0 license line.
2. **Chapter Opener** — a real-world scenario hooking the topic.
3. **Chapter Learning Outcomes** — bulleted list, "After completing this chapter, you should be able to: …".
4. **Sectional prose** organized into Parts (e.g. Part A, Part B) with numbered subsections (`1.1`, `1.2`, …). Worked examples are embedded inline in the prose.
5. **NOTE:** callouts for etymology / historical context.
6. **FIGURE DESCRIPTION blocks** — shaded boxes labeled `Figure X.Y — <title>` containing alt-text, reconstruction description, and caption. These are intentional and accessibility-critical (see below). Numbered `Figure 1.1`, `1.2`, etc.
7. **Concepts to Remember** summary, **Key Terms** glossary, **Practice Problems with full solutions**, **Multi-concept problems**, and a **10-question multiple-choice practice test with answer key**.
8. **Instructor Notes** section at the end (common student difficulties, in-class activities, lab connections). In the docx, this is a normal Heading 2 section; in the rendered HTML, `build_html.py` wraps it in `<details class="instructor-notes">` so it's hidden behind a "Show Instructor Notes" pill by default.

Suggested pacing baked into the front matter: 10-week course = 2 weeks on Ch 1, 1 week each on Ch 2–10.

## Figures: text-first, not image-first (do not "fix" this)

Figures live in the chapters as `FIGURE DESCRIPTION` blocks rather than embedded raster images. This is a **deliberate accessibility choice** under WCAG 2.2 — the descriptions double as screen-reader alt-text and as reconstruction notes for graphic designers. Do not propose replacing them with images as a cleanup task.

When a figure is added or revised, the corresponding entry in `Images/Chapter_NN/ManifestForChapter_NN.docx` must also be updated. The total count is tracked in `Images/Image_Sourcing_Guide_for_Instructors.docx` ("Total figures across the textbook: 19" as of this edition — Ch1:2, Ch2:2, Ch3:2, Ch4:2, Ch5:4, Ch6:1, Ch7:1, Ch8:1, Ch9:1, Ch10:3). Keep these in sync.

## License compatibility (matters when sourcing or quoting)

The book is **CC BY 4.0**. Anything pulled in must be compatible:

- **CC BY 4.0** and **CC0 / public domain** — fine, attribute as a courtesy.
- **CC BY-SA 4.0** — viral; embedding it can force the surrounding section (or whole work) to relicense as CC BY-SA. Flag to the user before suggesting.
- **CC BY-NC** — prohibits commercial use. Avoid unless the user confirms their institution permits it.
- **CC BY-ND** — never use. Cropping or recaptioning is itself a derivative.

Default approved sources for figures and data: OpenStax Chemistry 2e (CC BY 4.0), Wikimedia Commons (verify per file), NIST Chemistry WebBook (public domain), LibreTexts (verify per page — usually CC BY-NC-SA), NASA / USGS / FDA (public domain). Attribution lines go directly under the figure in italics, 9–10 pt; the `Image_Sourcing_Guide_for_Instructors.docx` shows the canonical formats.

## Numerical-data standards

When adding or correcting numerical content, match what the front matter promises:

- **Atomic masses** → IUPAC 2021 standard atomic weights.
- **Physical constants** → CODATA 2018.
- **Authoritative sources** → NIST, IUPAC, BIPM, CODATA, USGS, CRC Handbook.

If a number disagrees with these references, treat the references as authoritative and flag the discrepancy.

## Editorial conventions to preserve

- **Audience**: assumes high-school algebra; **no prior chemistry**. When rewriting, do not introduce unstated prerequisites.
- **Voice**: second person to the student; concrete, scenario-led openers; worked examples before practice.
- **Key terms** are bolded at first use in prose and re-defined in the chapter glossary — keep both copies in sync if you rename a term.
- **No color-only information**: anything conveyed by color must also be conveyed by label, pattern, or position (WCAG 2.2).
- **Math** is rendered in plain text where possible, for accessibility. Don't switch to images of equations.
- **Cross-references** between chapters (e.g. "see Section 5.3") are by section number; if you renumber, grep all chapters for stale references.
- **Multiple-choice practice tests carry two answer keys** — the terse line (`Answer Key: 1-B 2-C 3-A …`) at the top, and an "Answer Key with Worked Rationales" sub-section directly underneath that explains each correct answer in one sentence (math questions get a one-line factor-label calculation; conceptual ones get a "why this answer" sentence). When you edit MC questions, update **both**. The rationales were added by `.firecrawl/rewrite_mc_keys.py`, which is idempotent and safe to re-run.

## Dimensional-analysis (factor-label) Solutions format

Numerical Solutions and Worked Examples render the factor-label calculation in a specific dual-format ("Option C") so the docx, HTML, and Canvas/IMSCC builds stay aligned:

- **In `.docx`** — plain-text equation with **Word strikethrough on cancelled units** (`run.font.strike = True`). No symbol fonts, no special characters.
- **In built HTML / Canvas / IMSCC** — the same equation rendered with MathJax, with `\cancel{}` around cancelled units. `build_html.py` performs the docx → MathJax conversion.
- **Followed by an italic explanatory paragraph** that names which units cancel and why the answer carries the sig figs it does.

When rewriting Solutions to this format, prefer the per-chapter `rewrite_*` scripts in `.firecrawl/` (e.g. `rewrite_solutions_ch02.py`, `rewrite_ch08.py`, `rewrite_examples_ch09.py`) over hand-editing — they preserve the strikethrough runs that hand edits in Word commonly drop. The sweep is essentially complete across all 10 chapters as of commit `3a814da` (Apr 2026), including Worked Examples in Ch 8 and Ch 9; see `git log -- '*.docx'` for chapter-by-chapter history.

## Scripts you might reach for

Beyond the rewrite scripts noted above, two general-purpose helpers in `.firecrawl/` are worth knowing about before writing a new one:

| Script | What it does |
|---|---|
| `rewrite_engine_examples.py` | Worked-Example analogue of `rewrite_engine.py`. Anchors on "Step N — …" string matches inside boxed examples (which live in single-cell tables) rather than walking Solution paragraphs in document order. Use this when rewriting math chains inside Worked Example boxes. |
| `audit_problem_solution_pairs.py` | Content-QA scanner. Flags problems whose displayed solution doesn't echo any decimal number from the stem — surfaces mis-paired Problem/Solution rows. Low-recall, high-precision (skips purely conceptual stems). Re-run after large rewrites or content reshuffles. |
| `rewrite_mc_keys.py` | Appends the "Answer Key with Worked Rationales" sub-section after each chapter's terse MC answer key line. Idempotent. |
| `rename_course_title.py` | Run-level title rename across the .docx files (used to swap "Introduction to Chemical Principles" → "General Chemistry Prep"); a precedent for any future title-style rename that lives inside a single Word run. |
