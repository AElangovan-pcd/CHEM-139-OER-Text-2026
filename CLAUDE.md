# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repo is

CHEM 139 — *Introduction to Chemical Principles*, an Open Educational Resource (OER) textbook for one-quarter / one-semester community-college introductory chemistry (2026 edition). It is **content, not code** — every source file is a Microsoft Word `.docx` document. There is no build system, test suite, package manager, lockfile, or CI. Tasks here are editorial: revising prose, fixing chemistry, adjusting figure descriptions, updating manifests.

License: **CC BY 4.0**. Anything added must remain compatible (see "License compatibility" below).

## Repository layout

Top level holds one `.docx` per chapter plus front/back matter:

- `Front_Matter_Preface_License.docx` — preface, license, chapter map, "how to use" sections, accessibility statement, data-source provenance.
- `Chapter_01_…docx` … `Chapter_10_…docx` — the ten chapters. Filenames are stable; do not rename.
- `Formula_and_Constant_Reference_Sheet.docx`, `Periodic_Table_Reference_Page.docx`, `Index.docx` — reference back matter.
- `Images/` — does **not** contain images. It contains one manifest per chapter (`Images/Chapter_NN/ManifestForChapter_NN.docx`) plus `Image_Sourcing_Guide_for_Instructors.docx` at the root of `Images/`. Manifests tell instructors where to source openly-licensed figures; chapters ship with text descriptions in place of pictures.
- `.~lock.<filename>#` — a LibreOffice/Word lock file. If you see one, the user has that document open; warn before writing. A lock file may persist for a file that no longer exists in the repo (e.g. an exported PDF that was moved away) — that's harmless and can be ignored.

## Working directories (editorial workshop, not part of the published book)

These directories hold scaffolding for editing the chapters; their contents are not shipped to students:

- **`Briefs/`** — one `Brief_Figure_X.Y.md` per figure that needs designer reconstruction. Each brief lifts the FIGURE DESCRIPTION block (alt text, description, caption) out of its chapter into a standalone Markdown file a graphic designer can work from. When you create or edit a FIGURE DESCRIPTION block in a chapter, mirror it here if a brief already exists for that figure number.
- **`.firecrawl/`** — automation scratch space. Contains `python-docx` scripts the user has actually run against these chapters (`a11y_fix.py`, `a11y_pass.py`, `a11y_sublists.py`, `insert_practice.py`, `insert_ch1_images.py`, `move_practice_above_mixed.py`, `additional_problems.py`, `build_periodic_table.py`, …), Firecrawl-scraped OpenStax source material (`os-N-N.md`, `cat-*.md`, `file-*.md`), per-section JSON briefs (`s-N-N.json`), and a `backups/` directory. Before writing a new automation script, check here — there is probably a precedent that already handles styles, numbering, and the chapter template correctly.
- **Root-level reference PDFs** (e.g. `acs-periodic-table-poster_download.pdf`) — downloaded source material for figure sourcing. Not authored content.

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

## Chapter document structure (load-bearing conventions)

Every chapter follows the **same template**, and instructor/student instructions in the front matter promise this consistency. Preserve it when editing or regenerating:

1. Heading 1 chapter title → `Chapter N: <Title>` plus the standard subtitle line `CHEM 139 — Introduction to Chemical Principles · Open Educational Resource (2026 ed.)` and the CC BY 4.0 license line.
2. **Chapter Opener** — a real-world scenario hooking the topic.
3. **Chapter Learning Outcomes** — bulleted list, "After completing this chapter, you should be able to: …".
4. **Sectional prose** organized into Parts (e.g. Part A, Part B) with numbered subsections (`1.1`, `1.2`, …). Worked examples are embedded inline in the prose.
5. **NOTE:** callouts for etymology / historical context.
6. **FIGURE DESCRIPTION blocks** — shaded boxes labeled `Figure X.Y — <title>` containing alt-text, reconstruction description, and caption. These are intentional and accessibility-critical (see below). Numbered `Figure 1.1`, `1.2`, etc.
7. **Concepts to Remember** summary, **Key Terms** glossary, **Practice Problems with full solutions**, **Multi-concept problems**, and a **10-question multiple-choice practice test with answer key**.
8. **Instructor Notes** section at the end (common student difficulties, in-class activities, lab connections).

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
