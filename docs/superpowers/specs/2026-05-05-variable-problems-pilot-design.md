# Variable-Problem Pilot — Chapter 1

**Date:** 2026-05-05
**Status:** Approved (brainstorming complete; ready for implementation plan)
**Owner:** A. Elangovan (textbook author); implementation-plan to follow.

## 1. Goal

Add interactive, re-randomizable practice problems to the public HTML version of the textbook. A new **"Try a different version"** button next to selected Chapter 1 practice problems lets students attempt the same problem repeatedly with fresh sampled values; the existing **"Show solution"** pill always reveals the solution for the *current* sampled values. Pedagogical goal: support mastery-by-repetition on numerically-rich subtopics (sig figs, scientific notation) where students typically need many attempts.

The published static textbook is not changed. The interactive version is a parallel build deployed to GitHub Pages (with Render.com planned as the default publication target after the pilot).

## 2. Scope

### In scope (pilot)

- **Chapter 1 only** ("Science and Measurement").
- **6 practice problems**, one per major numerical subtopic in Ch 1 (see §8).
- **Live runtime randomization** — every click on the button re-samples values; the engine recomputes the answer and re-renders the solution paragraph.
- **Same repo, parallel build** — new code lives alongside `build_html.py`; canonical `HTML_Files/` is unchanged.

### Out of scope (pilot — explicit non-goals)

- All chapters other than Ch 1.
- Canvas/IMSCC integration.
- Persistent state (no localStorage of variant history).
- Quiz mode / answer checking.
- Variant-counter UI ("Variant 3 of ∞") or "Reset to original" link.
- Telemetry, analytics, or any data exfiltration.
- Browser automation tests (manual smoke test only).
- Author-facing GUI (YAML + console is the pilot UX).

### Phase 2 hints (deferred — do not build now)

- Expand to additional chapters with their own subtopic mix.
- Add factor-label / unit-conversion engine primitives (the `\cancel{}` chain renderer with a units lookup table) — needed for chapters with dimensional-analysis problems, **not** Ch 1.
- Render.com as the default publication URL.
- Optional follow-on: variant counter, reset-to-original link, persistent state, quiz mode.

## 3. Architecture

### File layout

```
.firecrawl/
    build_interactive.py                    # NEW build script (parallel to build_html.py)
    interactive_engine/
        engine.js                           # NEW tracked engine source
        engine.css                          # NEW tracked engine styles
    interactive_specs/
        chapter_01.yaml                     # NEW author-written spec
        chapter_01_problems/                # NEW escape-hatch JS modules (optional)
            problem_<slug>.js

HTML_Files_Interactive/                     # NEW build output — see §11 for tracking decision
    Chapter_01.html
    assets/
        engine.js                           # copied verbatim from .firecrawl/interactive_engine/
        engine.css

.github/workflows/pages.yml                 # extended to also run build_interactive.py
                                            # and copy HTML_Files_Interactive/ into /interactive/
```

The engine has no transpilation or minification step in the pilot — `engine.js` and `engine.css` are hand-written and copied verbatim into the build output. If the engine outgrows ~30 KB, a Phase 2 build step can be added.

### What changes vs. what doesn't

| Asset | Status |
|---|---|
| `Chapter_01.docx` (and all other `.docx`) | **Untouched** — read-only input, never written |
| `build_html.py` | **Untouched** |
| `HTML_Files/` (canonical static build output) | **Untouched** |
| `build_canvas.py`, `build_imscc.py`, IMSCC artefact | **Unaffected** (not present on this workspace anyway) |
| `.github/workflows/pages.yml` | **Extended** with one extra step + one extra copy |
| All other top-level files | **Untouched** |

### Five components

1. **Spec file** (YAML) — one entry per variable problem, identified by section-and-problem ID. Declares parameter ranges, the engine operation to apply, constraints, and an explanation-paragraph template.
2. **Build script** (`build_interactive.py`) — postprocesses `HTML_Files/Chapter_01.html` (does not read the docx). For each spec entry: locates the matching problem, replaces its markup with a variant-enabled block, copies the engine assets to `HTML_Files_Interactive/assets/`, writes the result. Idempotent.
3. **Runtime engine** (`interactive_engine.js`, ~30 KB target, no dependencies) — handles parameter sampling with guardrails, sig-fig arithmetic, scientific-notation conversion, linear-function evaluation, LaTeX rendering for each operation type, button wiring, and partial MathJax retypeset on variant change.
4. **Spec → runtime data path** — at build time, the YAML compiles to a JSON blob inlined into the page as `<script type="application/json" id="variant-specs">…</script>`. The engine reads it on page load.
5. **Escape-hatch loader** — a spec entry can set `custom_js: <filename>.js` instead of declaring parameters inline; the build script bundles that file's exports (`generateVariant`, `renderQuestion`, `renderSolution`) into the page and the engine wires the button to call them.

## 4. Authoring workflow (worked example)

The most important question for the author: *what do you write to make a problem variable?*

### Source problem (in `Chapter_01.docx`, untouched)

> **Practice Problem.** Compute (8.42 m) − (6.1 m) with correct sig figs.
>
> *Solution:* 2.32 → round to 1 decimal place → 2.3 m.

### Author writes in `chapter_01.yaml`

```yaml
problems:
  - id: "1.12.subtraction"             # matches problem in HTML by anchor or text
    question: "Compute ({a} m) − ({b} m) with correct sig figs."

    variables:
      a:
        range: [5.0, 50.0]
        decimal_places: 2              # exactly 2 decimal places after sampling
      b:
        range: [1.0, 5.0]
        decimal_places: 1

    answer:
      operation: subtract              # engine knows: apply addition/subtraction sig-fig rule
      unit: m

    constraints:
      result_must_be_positive: true    # resample if a − b ≤ 0

    explanation_template: |
      {a_value} − {b_value} = {raw_result}; round to {limiting_decimal_places}
      decimal place ({limiting_value} has fewest decimal places) → {final_result} m.
```

The engine handles: sampling values matching the declared decimal-place precision, computing the difference, applying the addition/subtraction sig-fig rule (round to the least decimal places), substituting `{a_value}`, `{b_value}`, `{raw_result}`, `{limiting_decimal_places}`, `{limiting_value}`, `{final_result}` into the explanation template, rendering the LaTeX, retyping it via MathJax.

### Spec format reference

| Field | Purpose | Example |
|---|---|---|
| `id` | Stable identifier matched against the HTML | `"1.12.subtraction"` |
| `question` | Prose template with `{var}` placeholders | `"How many sig figs in {value}?"` |
| `variables` | Generator declarations per variable | see worked example |
| `answer.operation` | What math the engine performs | `subtract`, `multiply`, `count_sig_figs`, `to_sci_notation`, `sci_notation_arithmetic`, `linear_function` |
| `answer.unit` | (optional) unit appended to the rendered answer | `m`, `g/mL` |
| `constraints` | Hard guardrails (resample on violation) | `result_range`, `result_must_be_positive`, `avoid_round`, custom predicates |
| `explanation_template` | Solution paragraph with `{token}` substitutions | see worked example |
| `custom_js` | Escape hatch — overrides everything above | `"problem_X.js"` |

### Variable generators

- **`range: [low, high]` + `decimal_places: N`** — uniform sample, formatted with exactly N decimal places.
- **`range: [low, high]` + `sig_figs: N`** — uniform sample, formatted with exactly N significant figures.
- **`generator: random_decimal_with_features` + `patterns: [...]`** — for sig-fig counting questions; rotates among declared structural patterns (`leading_zeros`, `captive_zero`, `trailing_zero_with_decimal`, `mixed`, `scientific_notation`).
- **`coefficient: …` + `exponent: …`** — for scientific-notation problems; samples a coefficient and an exponent independently.

### Escape-hatch contract

A problem with `custom_js: problem_<slug>.js` provides a JS module exporting:

```js
export function generateVariant() {
  // returns: { paramName: paramValue, ... }
}
export function renderQuestion(params) {
  // returns: string of HTML for the problem text
}
export function renderSolution(params) {
  // returns: { latex: "<full LaTeX>", explanation: "<text>" }
}
```

The engine wires the button to call `generateVariant()` → `renderQuestion()` → `renderSolution()` and replaces the relevant DOM in place. The escape hatch shares the same UX, the same Solution pill, and the same MathJax retypeset path as the main engine.

### Authoring effort estimate

Per problem: ~5–15 minutes to write, sample-test (`build_interactive.py --show-samples 50` dumps 50 variants for visual review), and tune ranges/constraints. For the 6-problem Ch 1 pilot: roughly half a day of authoring once the engine is built.

## 5. Runtime behavior

### On page load

1. Browser fetches `Chapter_01.html`. Inlined: the static prose (unchanged from the canonical build), the `<script type="application/json" id="variant-specs">` blob with compiled spec data, and `<script src="assets/interactive_engine.js" defer>`.
2. Engine boots. For each `<div class="variable-problem" data-spec-id="…">` on the page:
   - Reads the matching spec from the JSON blob.
   - Calls `generateVariant(spec)` with the four guardrails. If a sample fails, resample. **Cap at 50 retries**; on cap-hit the engine **falls back to the original textbook values** and logs a console warning.
   - Renders the question text via `{var}` substitution and swaps it into the DOM.
   - Pre-renders the solution LaTeX into a hidden `<div>` inside the closed Solution pill.
3. Engine awaits `MathJax.startup.promise`, then `MathJax.typesetPromise()` runs over the page once.

### On "Try a different version" click

1. Engine resamples the variant (same guardrails, same fallback).
2. Updates the question text in place with a light fade transition.
3. **Closes the Solution pill if it was open** so the student doesn't see numbers changing under their gaze.
4. Re-renders the solution LaTeX into the hidden div.
5. Calls `MathJax.typesetPromise([variantProblemEl])` to retypeset only that problem's container — keeps clicks snappy on pages with many MathJax expressions.

### Engine guardrails (defaults; per-problem overridable)

| Guardrail | Purpose |
|---|---|
| Sig-fig validation | Sampled value produces the declared sig-fig count |
| Magnitude sanity | Value falls within the declared range |
| Result-range check | If `constraints.result_range` declared, the *answer* must fall in it |
| No-degenerate-values | If `constraints.avoid_round` declared, sample must not equal those values |
| Retry cap | Max 50 resamples; on cap-hit, fall back to original textbook values |

### State model

Entirely client-side, in-memory, per page load. No localStorage, no cookies, no server. Refreshing the page yields a fresh sampled variant. If a student wants to redo "the same numbers," they keep the page open and click Show/Hide on the Solution pill.

### Accessibility

- The "Try a different version" button is a plain `<button>` with an `aria-label`, keyboard-focusable, labelled by the surrounding problem container.
- After a variant change, an `aria-live="polite"` region announces "Problem updated with new values" so screen-reader users know the question text changed.
- The Solution-pill behavior is unchanged, preserving the existing accessible-disclosure pattern.
- FIGURE DESCRIPTION blocks are unaffected — variable problems target practice problems, not figures.

## 6. Error handling

### Build time (`build_interactive.py` fails loudly)

| Failure | Behavior |
|---|---|
| YAML syntax error | Exit nonzero; print line number |
| Spec `id` not found in `HTML_Files/Chapter_01.html` | Exit; list nearby IDs ("did you mean 1.11.counting?") |
| Unknown `answer.operation` | Exit; print supported operations |
| Escape-hatch JS file missing or missing required exports | Exit; name the missing exports |
| `--show-samples 10` finds a problem where 10/10 samples violate guardrails | Exit; suggest widening ranges |
| One problem's spec is bad, others are fine | Skip that problem; warn (don't fail whole build) |

### Runtime (`interactive_engine.js` degrades gracefully)

| Failure | Behavior |
|---|---|
| Guardrail cap hit (50 resamples fail) | Fall back to original textbook values; console warning; page still works |
| MathJax not yet loaded at engine boot | Engine awaits `MathJax.startup.promise` before initial render |
| Spec JSON missing or malformed on page | Skip that problem (stays static); other problems unaffected |
| `MathJax.typesetPromise` rejects | Console error; leave previous typeset in place |

## 7. Testing

Three commands, no browser automation in the pilot:

| Command | Purpose | Speed | Run when |
|---|---|---|---|
| `build_interactive.py --validate` | Parse YAML, check every `id` resolves in HTML, check every operation known, generate 1 sample per problem to confirm constraints satisfiable | ~1 s | Every CI build |
| `build_interactive.py --show-samples 50` | Print a table of 50 sampled variants per problem | ~5 s | Author runs before shipping a chapter |
| `build_interactive.py --fuzz 1000` | Generate 1000 variants per problem; assert every one passes guardrails, every LaTeX string compiles via Node-side MathJax check, every `{token}` in the explanation template is filled | ~30 s | Before each release |

**Manual smoke test:** open `HTML_Files_Interactive/Chapter_01.html` in a browser, click "Try a different version" 10× per variable problem, open and close the Solution pill each time; check the browser console for warnings.

**Regression check:** confirm `HTML_Files/Chapter_01.html` (the canonical static build) renders byte-identically to before — proves the parallel build doesn't leak side-effects.

## 8. Pilot problem list

Six problems, one per major numerical subtopic in Ch 1. Specific source problems will be selected during implementation by reading `Chapter_01.docx`'s "Practice Problems by Topic" section and "Additional Practice Problems by Topic" section; spec IDs below are placeholder slugs.

| # | Spec ID (placeholder) | Subtopic (Ch 1 section) | Pattern | Engine operation |
|---|---|---|---|---|
| 1 | `1.11.counting` | Counting Sig Figs (1.11) | "How many sig figs in {value}?" — variable rotates among structural patterns (leading zeros, captive zero, trailing zero with decimal, scientific notation) | `count_sig_figs` |
| 2 | `1.12.add` | Sig Fig Arithmetic — Addition (1.12) | "Compute {a} + {b} + {c} with correct sig figs" — variables sampled with mixed decimal-place counts | `add` |
| 3 | `1.12.multiply` | Sig Fig Arithmetic — Multiplication (1.12) | "Compute ({a}) × ({b}) with correct sig figs" — variables sampled with mixed sig-fig counts | `multiply` |
| 4 | `1.13.to_sci_notation` | Scientific Notation Conversion (1.13) | "Express {decimal} in scientific notation" — variable orders of magnitude including very small and very large | `to_sci_notation` |
| 5 | `1.14.sci_arith` | Sci Notation Arithmetic (1.14) | "Compute ({a} × 10^{x}) × ({b} × 10^{y}) with correct sig figs" — coefficients and exponents both sampled | `sci_notation_arithmetic` |
| 6 | `1.16.linear` | Graphs in Chemistry (1.16) | "A best-fit line has slope {m} {units} and y-intercept {b}. Predict the y-value at x = {x_query}." | `linear_function` |

**Note on Ch 1 specifically:** the pilot does not exercise the engine's potential factor-label / unit-conversion machinery (with `\cancel{}` strikethrough). Ch 1's practice problems are sig-fig and scientific-notation focused; factor-label problems live in later chapters. Building the unit-conversion primitives is **Phase 2** work — adding them to the pilot now would be YAGNI.

## 9. Engine primitives needed for the pilot

The Ch 1 pilot needs these engine functions (all in vanilla JS, no external libs):

- `countSigFigs(numericString) → { count: number, ruleExplanation: string }`
- `formatWithSigFigs(value, n) → string`
- `decimalToSciNotation(value, sigFigs) → { coefficient: string, exponent: number, latex: string }`
- `sciNotationToDecimal({ coefficient, exponent }) → string`
- `addPreservingDecimalPlaces(values: string[]) → { rawSum, finalSum, limitingDecimalPlaces, limitingValue }`
- `multiplyPreservingSigFigs(values: string[]) → { rawProduct, finalProduct, limitingSigFigs, limitingValue }`
- `evaluateLinearFunction({ slope, intercept, x }) → { y, latex, explanation }`
- LaTeX rendering helpers per operation type (no `\cancel{}` strikethrough at this stage).

Phase 2 will add: `unitConvert(value, fromUnit, toUnit)`, `renderFactorLabelChain(steps)` (with `\cancel{}`), and a units lookup table.

## 10. Resolved decisions (from brainstorming)

| Decision | Resolution |
|---|---|
| Pilot scope | One chapter (Chapter 1) |
| Repo strategy | Same repo, parallel build |
| Variant generation model | Live runtime randomization with engine guardrails |
| Authoring surface | Constrained YAML spec + smart engine, with per-problem JS escape hatch |
| Student UX | Minimal — "Try a different version" button + existing Solution pill, no history/counter/quiz |
| Button label | "Try a different version" |
| Deploy target (pilot) | GitHub Pages subdirectory `/interactive/` |
| Deploy target (Phase 2 default) | Render.com |
| Pilot problem count | 6 — one per major numerical subtopic in Ch 1 |
| Engine fallback when guardrail cap is hit | Fall back to original textbook values |

## 11. Open questions to settle in the implementation plan

1. **Anchor matching strategy.** Exact `id` slugs and how they're attached to problems in `HTML_Files/Chapter_01.html` depend on what `mammoth` produces. The implementation plan should inspect the rendered HTML and pick: (a) inject IDs during the postprocess step using stable text-pattern matching, or (b) require `build_html.py` to add anchor IDs (a small, backward-compatible change to a tracked file).
2. **Tracking decisions.** Per the lean-remote policy in `CLAUDE.md`, only files needed by GitHub Pages CI are tracked. The plan should commit to:
   - `.firecrawl/build_interactive.py` — **track** (CI runs it).
   - `.firecrawl/interactive_engine/` (source) — **track** (build script reads it).
   - `.firecrawl/interactive_specs/` — **track** (build script reads it; also the editorial-rubric analogue of `.firecrawl/notes/`).
   - `HTML_Files_Interactive/` — by analogy with the tracked `HTML_Files/` snapshot, recommend **track**, so contributors can preview the interactive build without running Python locally. Pick one and lock it in.
3. **Sig-fig parsing/formatting.** Hand-roll a small parser, or pull a tiny dependency? Recommendation in the plan: hand-roll, to keep the engine bundle ≤ 30 KB.
4. **CI workflow extension.** Add a step to the existing `build` job in `pages.yml`, or split into a separate job? Recommendation: same job (single deploy artefact).
5. **MathJax partial typeset.** Confirm `MathJax.typesetPromise([el])` is callable on the static build's MathJax configuration; if not, the plan should include the (minor) configuration adjustment.
6. **Specific source problems.** During implementation planning, read Ch 1's "Practice Problems by Topic" and "Additional Practice Problems by Topic" sections and pick the specific 6 problems (one per subtopic in §8) whose source values will be the "fall-back originals."

## 12. Acceptance criteria

The pilot is complete when:

- All 6 pilot problems are variable-enabled with author-written YAML specs.
- `build_interactive.py --validate` passes.
- `build_interactive.py --fuzz 1000` passes for all 6 problems (no LaTeX-compile failures, no token-fill failures, no guardrail violations).
- The interactive page is deployed and reachable from GitHub Pages at `/interactive/Chapter_01.html`.
- Manual smoke test: each "Try a different version" button works 10× in a row, the Solution pill closes on click, the recomputed solution renders correctly with MathJax, no console errors.
- The canonical `HTML_Files/Chapter_01.html` is byte-identical to the pre-pilot build (regression check on the parallel-build separation).
- `Chapter_01.docx` is byte-identical to the pre-pilot file (proves the docx wasn't touched).
- `build_canvas.py` and the IMSCC build path are demonstrably unaffected (existing build commands run identically; `build_html.py` artefact unchanged).
