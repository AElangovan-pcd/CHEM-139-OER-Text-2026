# Variable-Problem Pilot — Phase 3a: Chapter 8 Mole Conversions

**Date:** 2026-05-07
**Status:** Approved (brainstorming complete; ready for implementation plan)
**Owner:** A. Elangovan (textbook author)
**Predecessors:**
- `docs/superpowers/specs/2026-05-05-variable-problems-pilot-design.md` (Phase 1 — Ch 1)
- `docs/superpowers/specs/2026-05-06-variable-problems-phase2-design.md` (Phase 2 — Ch 2 + factor-label engine)

## 1. Goal

Apply Phase 2's factor-label engine to Chapter 8 (Mole Concept and Chemical Formulas), shipping a 6-problem pilot covering mass↔mole↔atoms conversions and mole-ratio-from-formula problems. Same student-facing UX as Ch 1 and Ch 2: question stem above the pill, "Try a different version" button between, click closes pill.

The defining characteristic of Phase 3a is **scope minimization**: it reuses Phase 2's engine, build script, CI workflow, and YAML schema entirely. The deliverable is one new YAML spec and one new build-output HTML file.

## 2. Scope

### In scope (Phase 3a)

- Chapter 8 only — 6 pilot problems
- One new file: `.firecrawl/interactive_specs/chapter_08.yaml`
- One new build output: `HTML_Files/interactive/Chapter_08.html`
- Reuses Phase 2's `factor_label` operation exclusively
- Reuses Phase 2's `discover_chapters()` multi-chapter build infrastructure
- Reuses CI workflow without modification (already iterates over discovered specs)

### Out of scope (deferred to Phase 3b+)

- **Mass-percent problems** ("% N in NH₃", "% O in CaCO₃"). These are ratios, not multiplicative chains. Phase 3b will be paired with Ch 9 stoichiometry and address one of two paths:
  - (a) New `mass_percent` operation in the engine (`partial_mass / total_mass × 100`)
  - (b) Creative `factor_label` chain reformulation
  User explicitly requested this be addressed in Phase 3b.
- **Empirical/molecular formula problems** (multi-step ratios over multiple elements). Don't fit `factor_label` naturally; likely a new operation. Phase 3c+ work.
- **Combustion analysis** (multi-input mass balance). Doesn't fit `factor_label` at all. Phase 4+ work.
- **Purity problems** (same shape as mass-percent). Pair with Phase 3b.
- **Substance variation** — sampling between H₂O, NH₃, CH₄ randomly for a "moles of H atoms" problem. Bigger feature; punt to a substance-variation phase.

## 3. Architecture

**No code changes.** Phase 3a is additive: drop a new YAML in `interactive_specs/`, the build script auto-discovers it, CI builds + deploys.

### What changes vs. what doesn't

| File | Change | Why |
|---|---|---|
| `.firecrawl/interactive_specs/chapter_08.yaml` | **NEW** | The 6 pilot problem specs |
| `HTML_Files/interactive/Chapter_08.html` | **NEW** | The build output |
| `.firecrawl/interactive_engine/engine.js` | unchanged | All 6 problems use existing `factor_label` op |
| `.firecrawl/build_interactive.py` | unchanged | `discover_chapters()` already finds `chapter_*.yaml` |
| `.github/workflows/pages.yml` | unchanged | Already iterates over all discovered chapters |
| `Chapter_08_*.docx` | untouched (read-only) | Regression-checked at the end |
| `HTML_Files/interactive/Chapter_01.html`, `Chapter_02.html` | unchanged | Engine source mtime doesn't change → cache-buster URL stays the same → these files don't get rewritten |
| `HTML_Files/interactive/assets/engine.js`, `engine.css` | unchanged | Engine source mtime unchanged; `shutil.copy2` preserves mtime |

### Implication of the stale-asset lesson from Phase 2

Phase 2 was bitten by a workflow gap: engine *source* updates were committed but the rebuilt `HTML_Files/interactive/assets/engine.js` *asset* wasn't re-staged. Render shipped the stale asset.

**Phase 3a is immune to that gap because the engine source doesn't change.** No new engine.js content, no new mtime, no asset re-stage needed. If the engine ever changes again in a future phase, the discipline rule from Phase 2's memory file applies: rebuild and stage `HTML_Files/interactive/assets/engine.js` together with the source change.

## 4. Pilot problem list — Chapter 8

| # | Spec ID (placeholder) | § | Pattern | Engine usage |
|---|---|---|---|---|
| 1 | `8.10.mass_to_mole` | §8.10 | Mass → mole (single-step inexact factor) | `factor_label` 1 step, molar mass with declared sig_figs |
| 2 | `8.10.mole_to_mass` | §8.10 | Mole → mass (single-step inverse molar mass) | `factor_label` 1 step (inverse direction) |
| 3 | `8.10.mole_to_molecules` | §8.10 | Mole → molecules (single-step Avogadro) | `factor_label` 1 step, factor `6.022e23` |
| 4 | `8.10.atoms_to_mass` | §8.10 | Atoms → mass (two-step: atoms → mol → g) | `factor_label` 2 steps; sci-notation input value |
| 5 | `8.9.mole_ratio_subscript` | §8.9 | Mole compound → mole element via subscript | `factor_label` 1 step, subscript as exact integer factor |
| 6 | `8.10.three_step_chain` | §8.10 | g compound → mol → mol element → atoms | `factor_label` 3 steps |

Source problems (verified to appear in `HTML_Files/Chapter_08.html`):

- #1: "How many moles in 25.0 g of NaCl?" (M = 58.44 g/mol)
- #2: "Mass, in grams, of 0.250 mol H₂O?" (M = 18.02 g/mol)
- #3: "Number of molecules in 0.100 mol CO₂?"
- #4: "Mass of 3.011 × 10²³ atoms of Cu?" (M = 63.55 g/mol)
- #5: "How many moles of H atoms in 0.50 mol C₆H₁₂O₆?"
- #6: "How many H atoms in 18.0 g H₂O?" (M = 18.02 g/mol)

Spec IDs are placeholder slugs to be confirmed when the implementation plan reads the rendered HTML. Match_text strings will be unique-substring matches per the Phase 1/2 precedent.

### Why these six

Maximum diversity of factor-label idioms:
- **Single-step inexact factors** (#1, #2): exercises sig-fig propagation when molar mass governs.
- **Avogadro's number as factor** (#3, #4, #6): the textbook's 4-sig-fig convention (`6.022 × 10²³`); engine handles `6.022e23` via `parseFloat`.
- **Two-step chain** (#4): atoms → mol → g, mixed exact (1 mol = 6.022e23 atoms via Avogadro is treated as inexact 4 sig figs) and inexact (molar mass).
- **Subscript-as-exact-factor** (#5): a *new idiom* for the engine. The "12" in "12 mol H / 1 mol C₆H₁₂O₆" is exact (chemical formula derives it from integer subscripts). Sets up Ch 9's "mole-ratio-from-balanced-equation" pattern for Phase 3b.
- **Three-step chain** (#6): longest chain so far; stress-tests `renderFactorLabelLatex`'s output with three `\times \frac{...}{...}` segments. Phase 2 topped out at two steps.

## 5. New engine behavior to verify

The engine doesn't change, but Phase 3a exercises code paths Phase 2 didn't hit. The implementation plan should include explicit verification of:

1. **Sci-notation input values** in the question variable. Example: `n_atoms = "3.011e23"`. The Phase 1 `countSigFigs` handles sci-notation; `parseFloat` handles the arithmetic. The rendered MathJax in the *question stem* uses the value as-is — i.e., `3.011e23` would render as plain text "3.011e23" rather than "3.011 × 10²³" with proper superscript. **Decision for Phase 3a**: question template wraps the input in MathJax inline-math (`\(...\)`) for the sci-notation problems (matching Phase 1's `1.13.to_sci_notation` precedent). Plan tasks will include a small string-massage if needed.

2. **Three-step chain rendering**. Confirm the resulting LaTeX has exactly three `\times \frac{...}{...}` segments and renders cleanly in MathJax with the `cancel` extension. Manual smoke test in browser is the gate.

3. **Avogadro's number as `num_value: 6.022e23`** — JS `Number.toString()` may render `6.022e+23` (with `+`) which is technically valid in MathJax `10^{...}` but might look odd. If it does, the YAML can use `num_value: 6.022e23` and the engine renders it as `6.022e+23` in the chain — acceptable for the pilot, polish in a future phase if needed.

## 6. Resolved decisions (from brainstorming)

| Decision | Resolution |
|---|---|
| Phase 3a chapter | Chapter 8 only |
| Problem count | 6 |
| Engine extension? | None — reuses Phase 2's `factor_label` exclusively |
| Mass-percent problems | **Deferred to Phase 3b** (paired with Ch 9 stoichiometry); user explicitly approved deferral and asked the choice (new `mass_percent` op vs. creative reformulation) be addressed there |
| Sci-notation input values | Engine already handles via `parseFloat`; verified by Phase 1 `countSigFigs` tests |
| Substance variation | No — only vary numeric input values per problem (substances stay at textbook values, matching Phase 2 precedent) |
| Molar mass declaration in YAML | Per-problem inline (e.g., `num_value: 58.44, sig_figs: 4`); built-in molar-mass table is a Phase 4+ optimization |

## 7. Open follow-ups (recorded for future phases)

- **Phase 3b: Ch 9 stoichiometry + mass-percent operation.** ~8 problems. Pair with the mass-percent design choice the user flagged.
- **Phase 3c+: Empirical/molecular formula problems.** Multi-step ratios; needs a new operation type.
- **Phase 4+: Combustion analysis.** Multi-input mass balance; doesn't fit factor_label.
- **Substance variation feature.** Random formula sampling (H₂O / NH₃ / CH₄) for "moles of H" style problems. Bigger feature.
- **Engine-side molar-mass and unit-conversion table.** Reduces YAML verbosity once 20+ problems are authored. Worth doing only after the pain is felt.
- **Pre-commit hook for stale-asset bug** (lesson from Phase 2). Python check that compares `HTML_Files/interactive/assets/engine.js` content against `.firecrawl/interactive_engine/engine.js`. Tiny PR; can land alongside Phase 3a or independently.

## 8. Acceptance criteria

Phase 3a is complete when:

- 6/6 Ch 8 problems pass `--fuzz 1000` (6,000 new variants).
- Phase 1 + Phase 2 problems still pass `--fuzz 1000` (no regression — 18,000 variants total across 3 chapters).
- All engine tests pass (50/50; no new ones expected).
- All Python build-script tests pass (14/14; no new ones expected).
- Live on Pages: `https://aelangovan-pcd.github.io/CHEM-139-OER-Text-2026/interactive/Chapter_08.html`.
- Live on Render after manual redeploy: `https://chem-139-oer-text-2026.onrender.com/interactive/Chapter_08.html`.
- Manual smoke test: each "Try a different version" button cycles correctly; pill closes on click; MathJax typesets the chain with `\cancel{}`; serial number prefix preserved.
- Canonical `HTML_Files/Chapter_08.html` and all `.docx` files byte-identical to current `main`.
- All 18 problems across 3 chapters validate together (`--validate` reports "VALIDATE OK: 18 problems across 3 chapter(s).").

## 9. Open questions to settle in the implementation plan

1. Confirm `match_text` strings against `HTML_Files/Chapter_08.html` (per Phase 1/2 precedent — values selected during plan writing).
2. Each problem's molar-mass value and sig-fig count to declare in YAML — pulled from each textbook problem's parenthetical molar mass.
3. Avogadro sig-fig declaration: textbook uses 4 sig figs (`6.022 × 10²³`); spec uses `sig_figs: 4`.
4. Whether question template wraps sci-notation input in `\(...\)` MathJax delimiters (#4, #6) — recommend yes for clean rendering.

## 10. Estimated effort

~2–3 hours total session work:
- Plan writing: ~15 min (small plan; mostly authoring tasks)
- Implementation (subagent-driven C0–C6 pattern): ~90–120 min for 6 problems
- Final regression + push + PR + Pages deploy + Render manual redeploy: ~15 min
