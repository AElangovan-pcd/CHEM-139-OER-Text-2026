# Variable-Problem Pilot — Phase 2: Chapter 2 (Dimensional Analysis)

**Date:** 2026-05-06
**Status:** Approved (brainstorming complete; ready for implementation plan)
**Owner:** A. Elangovan (textbook author)
**Predecessor:** `docs/superpowers/specs/2026-05-05-variable-problems-pilot-design.md` (Phase 1 — Chapter 1)

## 1. Goal

Extend the variable-problem engine to support **factor-label / dimensional-analysis problems** with proper `\cancel{}` chain rendering, then pilot the new capability on **Chapter 2** ("Unit Systems and Dimensional Analysis"). Same student-facing UX as Phase 1: question stem above the pill, "Try a different version" button between, click closes pill and forces re-attempt before peeking. The new value here is on the *engine* side: a chain-of-conversion-factors primitive that generates LaTeX with proper unit cancellation, sig-fig propagation across exact and inexact factors, and rendering that matches the textbook's Option-C convention (`5.00\,\cancel{\text{lb}} \times \frac{453.59\,\text{g}}{1\,\cancel{\text{lb}}} \times \frac{1\,\text{kg}}{1000\,\cancel{\text{g}}} = 2.27\,\text{kg}`).

## 2. Scope

### In scope (Phase 2)

- **Chapter 2 only** — 6 pilot problems covering the major dimensional-analysis categories (single-step metric, multi-step metric, English↔metric, density chain, equivalence/dosage factor, mass percent).
- **`factor_label` operation** added to the engine.
- **Multi-chapter build-script refactor** so `build_interactive.py` auto-discovers all `chapter_NN.yaml` specs (Ch 1 stays working unchanged).
- **CI workflow extension** to validate, fuzz, and build every chapter's specs.
- Same testing rigour as Phase 1: TDD on engine primitives, `--fuzz 1000` gate, regression check on canonical HTML/docx.

### Out of scope (deferred to Phase 3+)

- **Ch 8 mole conversions** (mass↔mole↔atoms via molar mass + Avogadro). Same engine; ~6–8 more problems. Easy increment after Phase 2.
- **Ch 9 stoichiometry chains** (mole-ratio conversion factors from balanced equations). ~8 problems.
- **Substance variation** — sampling which liquid (ethanol/acetone/water) for density problems. Needs a substance-properties table; bigger lift.
- **Engine-side unit-conversion table** for common metric/English factors (reduces YAML verbosity but adds maintenance). Per-problem chain in YAML is YAGNI for the pilot.
- **Stepped multi-line chain rendering** (only useful for >3-step chains; pilot has none).
- **Temperature conversions** (Ch 2 §2.11) — formula-based, not factor-label. Could reuse the existing `linear_function` operation but `T_F = T_C × 9/5 + 32` needs two ops. Defer until a clear need surfaces.

## 3. Architecture

The Phase 1 architecture stays intact. Phase 2 makes targeted additions:

| Component | Phase 1 state | Phase 2 change |
|---|---|---|
| `.firecrawl/interactive_engine/engine.js` | 7 pure-function primitives + sampling + DOM bootstrap | **Add 2 primitives:** `factorLabelChain`, `renderFactorLabelLatex`. **Add 1 case** to `computeAnswer` (`factor_label`) and to `renderLatexForOperation`. |
| `.firecrawl/interactive_engine/engine.test.js` | 35 tests | **Add ~10 tests** for the new primitives + chain validation |
| `.firecrawl/build_interactive.py` | Hardcoded to `chapter_01.yaml` and `Chapter_01.html` | **Refactor to multi-chapter:** auto-discover all `interactive_specs/chapter_*.yaml`, build each into `HTML_Files/interactive/Chapter_NN.html`. Add `--chapter NN` flag for single-chapter runs. |
| `.firecrawl/test_build_interactive.py` | 8 tests | **Add ~3 tests** for multi-chapter discovery |
| `.firecrawl/interactive_specs/` | `chapter_01.yaml` + `chapter_01_problems/` | **Add `chapter_02.yaml`** with 6 pilot problems |
| `HTML_Files/interactive/` | `Chapter_01.html` + assets | **Add `Chapter_02.html`** (build output) |
| `.github/workflows/pages.yml` | Builds Ch 1 only | **Extend** to build all chapters discovered by `build_interactive.py` |
| `Chapter_02_*.docx` (source) | Untouched | **Untouched** (read-only input, regression check at end) |

**Files NOT changed by this plan:**
- Any `.docx` chapter source.
- `.firecrawl/build_html.py`, `HTML_Files/Chapter_*.html` (canonical output beyond Ch 1's `interactive/` subdir).
- The Phase 1 Ch 1 pilot's spec/output (continues to ship unchanged).
- `build_canvas.py`, `build_imscc.py` (already excluded by CLAUDE.md policy).

## 4. New engine primitives

Two new exported functions in `engine.js`. Both are pure (no DOM), tested via `node:test`.

### `factorLabelChain(value, valueSigFigs, valueUnit, steps) → result`

Applies a chain of conversion factors to a starting value. Validates that each step's denominator unit cancels with the previous numerator (or with `valueUnit` for step 0). Tracks sig-fig propagation: only inexact factors with declared `sig_figs` constrain the final result.

**Input shape:**

```js
factorLabelChain(
  '5.00',                   // value (string for sig-fig preservation)
  3,                        // valueSigFigs
  'lb',                     // valueUnit
  [
    { numValue: 453.59, numUnit: 'g',  denValue: 1, denUnit: 'lb', sigFigs: 5 },
    { numValue: 1,      numUnit: 'kg', denValue: 1000, denUnit: 'g', exact: true },
  ]
)
```

**Output shape:**

```js
{
  rawResult: '2.26795',       // unrounded float as string
  finalResult: '2.27',         // sig-fig-rounded
  finalUnit: 'kg',
  limitingSigFigs: 3,          // min of valueSigFigs and any non-exact factor's sigFigs
  limitingSource: 'value',     // which input limited (e.g., 'value', 'step[0]', 'step[1]')
  validatedChain: [...],       // chain echoed back, with cancellation checks recorded
}
```

**Validation:** throws `Error('factorLabelChain: cancellation mismatch at step N: expected den_unit "X", got "Y"')` if the chain doesn't cancel cleanly. This catches author errors at variant-generation time (each click) and at build-time fuzz.

### `renderFactorLabelLatex(value, valueUnit, steps, finalResult, finalUnit) → string`

Renders a complete chain as MathJax LaTeX, with `\cancel{...}` on every cancelled unit and the final result.

**Output (for the example above):**

```latex
5.00\,\cancel{\text{lb}} \times \frac{453.59\,\text{g}}{1\,\cancel{\text{lb}}} \times \frac{1\,\text{kg}}{1000\,\cancel{\text{g}}} = 2.27\,\text{kg}
```

This matches the textbook's Option-C convention exactly. `build_html.py` already MathJax-typesets this style for static problems; the engine produces the same form for variant-generated solutions.

### Integration with existing engine

`computeAnswer` (in `cycleVariant`'s pipeline) gains a new switch case:

```js
case 'factor_label':
  return factorLabelChain(
    params[answerSpec.value_param],     // e.g., params.mass
    countSigFigs(params[answerSpec.value_param]).count,
    answerSpec.input_unit,
    answerSpec.chain
  );
```

`renderLatexForOperation` gains a corresponding case that calls `renderFactorLabelLatex(...)`.

## 5. YAML schema — `factor_label` operation

```yaml
- id: "2.7.lb_to_kg"
  match_text: "Convert 5.00 lb to kg"
  question: "Convert {mass} lb to kg."
  variables:
    mass:
      range: [1.0, 20.0]
      sig_figs: 3
  answer:
    operation: factor_label
    value_param: mass               # which variable supplies the input value
    input_unit: lb                   # unit of the input value (must match chain[0].den_unit)
    chain:
      - num_value: 453.59
        num_unit: g
        den_value: 1
        den_unit: lb
        sig_figs: 5                  # 4-5 sig figs — non-exact
      - num_value: 1
        num_unit: kg
        den_value: 1000
        den_unit: g
        exact: true                  # 1 kg = 1000 g (definition; doesn't constrain sig figs)
    target_unit: kg                  # must equal chain[-1].num_unit
  explanation_template: |
    "lb" cancels in step 1; "g" cancels in step 2.
    {limitingSigFigs} sig figs from "{mass} lb" yield \({finalResult}\,\text{kg}\).
```

### Field reference

| Field | Required | Purpose |
|---|---|---|
| `value_param` | yes | Names the variable whose value seeds the chain. |
| `input_unit` | yes | Unit attached to the input value; must equal `chain[0].den_unit`. |
| `chain[].num_value` | yes | Numerator number (the conversion factor's "to" side). |
| `chain[].num_unit` | yes | Numerator unit. |
| `chain[].den_value` | yes | Denominator number. |
| `chain[].den_unit` | yes | Denominator unit; must cancel against the previous step's `num_unit` (or `input_unit` for step 0). |
| `chain[].exact` | no, default `false` | If `true`, factor doesn't constrain sig figs. |
| `chain[].sig_figs` | required if not exact | Number of sig figs in the factor; used in propagation. |
| `target_unit` | yes | Final unit; must equal `chain[-1].num_unit`. Used for explanation rendering and validation. |

### Validation (build-time)

- `input_unit` must equal `chain[0].den_unit`.
- For each step `i > 0`: `chain[i].den_unit` must equal `chain[i-1].num_unit`.
- `target_unit` must equal `chain[-1].num_unit`.
- Each non-exact step must declare `sig_figs`.

Failure modes are loud: `--validate` prints the specific spec id and which constraint failed.

## 6. Build script multi-chapter refactor

Phase 1's `build_interactive.py` is hardcoded to `chapter_01.yaml` → `Chapter_01.html`. Phase 2 generalizes:

```python
SPEC_GLOB = REPO / ".firecrawl" / "interactive_specs" / "chapter_*.yaml"

def discover_chapters():
    """Return [(chapter_num, spec_path, input_html, output_html), ...] for every chapter_NN.yaml."""
    ...
```

### CLI

| Flag | Effect |
|---|---|
| (no flag) | Build all discovered chapters |
| `--chapter 02` | Build only Chapter 02 |
| `--validate` | Validate all discovered chapters; exit nonzero on first failure |
| `--show-samples N` | Show N samples per problem across all chapters (or scoped by `--chapter`) |
| `--fuzz N` | Fuzz all chapters' problems (or scoped) |

### Backwards compat

- `chapter_01.yaml` continues to work without changes (it's just one of the discovered files).
- `HTML_Files/interactive/Chapter_01.html` continues to be produced and shipped.
- The Phase 1 spec format (no `factor_label` operation, just `subtract`/`add`/etc.) keeps working.

### CI workflow update

`.github/workflows/pages.yml` currently runs single-chapter commands; updates to:

```yaml
      - name: Build interactive chapters
        run: |
          python .firecrawl/build_interactive.py --validate
          python .firecrawl/build_interactive.py --fuzz 1000
          python .firecrawl/build_interactive.py
```

(Same commands, but they now operate on all chapters automatically.)

## 7. Pilot problem list — Chapter 2

Six problems covering the major DA categories. Specific source problems will be selected during implementation by reading `Chapter_02.docx`'s practice-problem section; spec IDs below are placeholder slugs.

| # | Spec id (placeholder) | §  | Pattern | Operation |
|---|---|---|---|---|
| 1 | `2.4.metric_simple` | §2.4 | Single-step metric (e.g. "Convert {mass} mg to g") | `factor_label`, 1 step (exact factor) |
| 2 | `2.7.metric_chain` | §2.7 | Two-step metric (e.g. "Convert {length} km to cm" via m) | `factor_label`, 2 steps (both exact) |
| 3 | `2.7.eng_metric` | §2.7 | English↔metric (e.g. "Convert {mass} lb to kg" via g) | `factor_label`, 2 steps (one inexact lb→g, one exact g→kg) |
| 4 | `2.8.density_mass_to_vol` | §2.8 | Density chain (e.g. "Volume of {mass} kg of mercury", `d = 13.546 g/mL`) | `factor_label`, 2 steps (kg→g exact, g→mL inexact density) |
| 5 | `2.9.dosage` | §2.9 | Dosage equivalence (e.g. "Drug at 5.00 mg/kg, dose for {mass} kg patient") | `factor_label`, 1 step (inexact factor) |
| 6 | `2.9.alloy_mass_percent` | §2.9 | Mass percent (e.g. "Alloy is {pct}% silver, mass of Ag in {mass} g of alloy") | `factor_label`, 1 step (mass percent as conversion factor) |

**Why these six:**
- **#1** (single-step exact) builds the engine on the simplest case.
- **#2** (two-step, both exact) exercises chain rendering with multiple `\cancel{}` cancellations and zero sig-fig erosion.
- **#3** (two-step, mixed exact/inexact) exercises sig-fig propagation across factor types.
- **#4** (density chain) introduces a non-metric equivalence factor (`g/mL` density) and exercises units that aren't simple unit-prefix conversions.
- **#5** (dosage) tests the per-mass equivalence pattern used heavily in pharmacy / pre-health applications.
- **#6** (mass percent) tests percent-as-conversion-factor, which transfers directly to Ch 8 mole-percent and Ch 9 yield problems.

All six exercise the same engine primitives. After Phase 2, adding Ch 8 and Ch 9 problems is "more YAML; no engine work."

## 8. Resolved design decisions

| # | Decision | Resolution |
|---|---|---|
| 1 | Phase 2 scope | Chapter 2 only, 6 pilot problems |
| 2 | Conversion factor source | Per-problem in YAML (no engine-side units table for the pilot) |
| 3 | Chain step format | Structured `num_value` / `num_unit` / `den_value` / `den_unit` fields (matches textbook Option C) |
| 4 | Substance variation in problems | No — only vary numbers in this pilot |
| 5 | Multi-step chain rendering | Single equation line with `\cancel{}` per cancelled unit |
| 6 | Build-script multi-chapter handling | Auto-discover all `chapter_*.yaml` files; `--chapter NN` for scoped runs |
| 7 | Substance constants (densities, molar masses) | Hard-code per problem in YAML (built-in lookup table is Phase 3+) |

## 9. Open follow-ups (Phase 3+)

These are explicitly out of scope for this design but recorded so they don't get lost:

- **Ch 8 mole conversions** — same engine; new YAML specs for mass↔mole↔atoms problems. ~6–8 problems. Should be a 2–3 hour increment.
- **Ch 9 stoichiometry** — same engine; introduces balanced-equation mole ratios as conversion factors. ~8 problems. Possibly a 4–5 hour increment depending on how the textbook formats balanced equations.
- **Engine-side unit conversion table** — built-in lookup for common metric/English factors. Reduces YAML verbosity. Worth doing only after authoring 20+ DA problems makes the verbosity painful.
- **Substance variation** — sample which liquid for density problems, which metal for alloy problems. Needs a substance-properties table; ~4–6 hour feature.
- **Stepped chain rendering** — only useful for chains with 4+ steps. None of Phase 2's six problems hit that threshold.
- **Temperature problems (§2.11)** — formula-based (not factor-label). Either reuse `linear_function` with a small wrapper, or add an `evaluateFormula` primitive. Defer until pedagogical demand surfaces.
- **Substance-name variation in question stems** (e.g., randomly choose between "mercury" and "iron" with the appropriate density) — Phase 3 substance-variation feature.
- **Per-step sig-fig override in spec** — currently each non-exact step declares `sig_figs`. If author writes `sig_figs` on the input variable in `variables` block but not on the step, engine could infer. Punt on this complexity until needed.

## 10. Acceptance criteria

The Phase 2 pilot is complete when:

- All 6 pilot problems pass `--fuzz 1000` (6,000 variants total).
- Engine has 45+ tests (Phase 1's 35 + ~10 new for `factorLabelChain`, `renderFactorLabelLatex`, and chain validation), all passing.
- Build script has 11+ tests (Phase 1's 8 + ~3 new for multi-chapter discovery), all passing.
- `python .firecrawl/build_interactive.py --validate` reports OK for *both* Ch 1 and Ch 2.
- Live on Pages at `https://aelangovan-pcd.github.io/CHEM-139-OER-Text-2026/interactive/Chapter_02.html`.
- Live on Render (after manual redeploy) at `https://chem-139-oer-text-2026.onrender.com/interactive/Chapter_02.html`.
- Manual smoke test: each "Try a different version" button works; pill closes on click; MathJax typesets the chain with `\cancel{}` correctly; serial number prefix preserved across variants.
- Canonical `HTML_Files/Chapter_02.html` and all `.docx` files byte-identical to current `main`.
- Phase 1 Ch 1 pilot continues to work without regression — same `--fuzz 1000` passes for all 6 Ch 1 problems.
- Canvas/IMSCC build paths unaffected (already not present on this workspace).

## 11. Open questions to settle in the implementation plan

1. **Specific source problems in Ch 2** — confirm `match_text` strings against `HTML_Files/Chapter_02.html` (the build_html.py output) during Phase 2 implementation.
2. **Whether to extract `mulberry32`'s seed-from-id helper** that Phase 1's `sample_driver.js` uses (`parseInt(prob.id.replace(/\D/g, '') || '1', 10)`) — for Phase 2 problem IDs like `2.4.metric_simple`, this yields seed `24` (good), but multi-period IDs may produce surprising seeds. Worth a small helper that hashes the full id deterministically.
3. **Engine API stability** — should `renderLatexForOperation`'s signature accept `answerSpec` for `factor_label` (it already does for sci-notation arithmetic)? Yes, per the existing pattern.
4. **Test isolation** — should `factorLabelChain` and `renderFactorLabelLatex` go in their own `engine-factor-label.test.js` file or extend the existing `engine.test.js`? Keep `engine.test.js` for the pilot; split only if the file passes ~80 tests.
5. **CI runtime** — the existing Phase 1 `--fuzz 1000` step takes ~2s. Adding 6 more problems at ~0.3s each adds ~2s. Total CI run still well under a minute. No concern.
