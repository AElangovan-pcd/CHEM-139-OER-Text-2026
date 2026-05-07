# Variable-Problem Pilot — Phase 3b: Mass-Percent + Ch 9 Stoichiometry

**Date:** 2026-05-08
**Status:** Approved (brainstorming complete; ready for implementation plan)
**Owner:** A. Elangovan (textbook author)
**Predecessors:**
- `docs/superpowers/specs/2026-05-05-variable-problems-pilot-design.md` (Phase 1 — Ch 1)
- `docs/superpowers/specs/2026-05-06-variable-problems-phase2-design.md` (Phase 2 — Ch 2 + `factor_label`)
- `docs/superpowers/specs/2026-05-07-variable-problems-phase3a-design.md` (Phase 3a — Ch 8 mole conversions)

## 1. Goal

Phase 3b ships **8 new variable problems** across two chapters, addressing the two follow-ups pinned at the end of Phase 3a:

1. **Mass-percent problems** in Ch 8 §8.4 — "% N in NH₃" style. Two problems (one varies the compound, one varies the element).
2. **Ch 9 stoichiometry chains** — six problems exercising mole-to-mole, mole-to-mass, and mass-to-mass idioms across the §9.7–§9.9 sections, all on the existing `factor_label` engine.

Phase 3b introduces **one new engine operation** (`mass_percent`) and **one new variable generator** (`pick_one`). Both are minimal, well-scoped additions that follow the same architectural pattern as Phase 1's `to_sci_notation` and Phase 2's `factor_label`.

## 2. Scope

### In scope (Phase 3b)

- 2 new mass-percent problems in `.firecrawl/interactive_specs/chapter_08.yaml` (existing 6 untouched).
- 6 new stoichiometry problems in a new file `.firecrawl/interactive_specs/chapter_09.yaml`.
- New `mass_percent` engine operation in `.firecrawl/interactive_engine/engine.js`.
- New `pick_one` variable generator in `sampleValue`.
- Struct-unfolding logic in `generateVariant` (the only site that needs to know about struct-typed sample values).
- New tests in `engine.test.js`.
- `mass_percent` added to `SUPPORTED_OPERATIONS` in `build_interactive.py`.
- New build output: `HTML_Files/interactive/Chapter_09.html` (auto-discovered by `discover_chapters()`).

### Out of scope (deferred to Phase 3c+)

- **Percent yield** — same shape as `mass_percent` (`actual / theoretical × 100`); Phase 3b's `mass_percent` operation sets the precedent and Phase 3c can either reuse it or add a thin `percent_yield` alias.
- **Limiting reactant** — needs comparison logic between two products; doesn't fit any existing operation. Phase 4+ work.
- **Empirical / molecular formula problems** — multi-step ratios with branching; needs a new operation.
- **Combustion analysis** — multi-input mass balance; doesn't fit `factor_label`.
- **Engine-side molar-mass and unit-conversion table** — would let YAML reference `m("CaCO3")` instead of hand-listed values. Worth doing only after pain is felt across 30+ DA problems.

## 3. Numeric Precision Convention (textbook-wide)

**Rule (applies to all chapters and all engine operations):** when listing atomic masses or molar masses in YAML, use this precision:

| Element / molar mass | Decimal places | Example |
|---|---|---|
| < 100 g/mol | 2 | H = 1.01, O = 16.00, Ca = 40.08, NaCl = 58.44, H₂O = 18.02, Cu = 63.55 |
| > 100 g/mol | 1 | Pb = 207.2, U = 238.0, Hg = 200.6, Ca(NO₃)₂ = 164.1 |

**Rationale.** Reflects the textbook's atomic-mass-table precision convention. Heavier elements have less reliable trailing decimals and are conventionally shown to one decimal place in introductory chemistry tables.

**Where this applies:**
- `mass_percent` operation: the `decimal_places` field in the answer spec governs output rendering. 2 for light-element compounds, 1 for any-heavy compound.
- `factor_label` operation: the convention applies to authored numeric values (`num_value`, `den_value` for molar masses). Output `finalResult` continues to follow standard sig-fig propagation.
- Any future operation that handles molar masses inherits this convention.

**Phase 3a compliance check.** Verified — `chapter_08.yaml`'s existing 6 problems use `NaCl=58.44`, `H₂O=18.02`, `Cu=63.55` (all 2-decimal because all light-element compounds). No backport needed.

**Deliberate divergence from select textbook values.** Where the textbook source uses 3-decimal-place atomic masses for light elements (e.g., H = 1.008, Cl = 35.45 was already 2-decimal), Phase 3b YAML adopts the 2-decimal value (H = 1.01, H₂ = 2.02, H₂O = 18.02 — the last already matches). This is editorial uniformity, not a math error. The variant problems still teach correct mass conservation and the displayed answers stay within textbook tolerance.

## 4. Engine changes

### 4.1 New operation: `mass_percent`

**Compute function (engine.js):**

```js
function computeMassPercent(answerSpec, params) {
  const partial = parseFloat(params[answerSpec.partial_mass_param]);
  const total = parseFloat(params[answerSpec.total_mass_param]);
  const decimals = answerSpec.decimal_places ?? 2;
  const rawPercent = (partial / total) * 100;
  const finalPercent = rawPercent.toFixed(decimals);
  return {
    rawPercent: rawPercent.toString(),
    finalPercent,
    finalPercentLatex: finalPercent,
  };
}
```

Dispatched from `computeAnswer` via `case 'mass_percent': return computeMassPercent(answerSpec, params);`.

**LaTeX rendering (renderLatexForOperation adds case):**

```js
case 'mass_percent': {
  const partial = p[answerSpec.partial_mass_param];
  const total = p[answerSpec.total_mass_param];
  const elementLabel = p[answerSpec.element_label_param];
  const compoundLabel = p[answerSpec.compound_label_param];
  return '\\dfrac{' + partial + '\\,\\text{g ' + elementLabel + '}}'
       + '{' + total + '\\,\\text{g ' + compoundLabel + '}}'
       + ' \\times 100\\% = ' + c.finalPercent + '\\%';
}
```

**YAML interface:**

```yaml
answer:
  operation: mass_percent
  partial_mass_param: <variable name>     # variable holding partial mass (numeric)
  total_mass_param:   <variable name>     # variable holding total formula mass (numeric)
  element_label_param: <variable name>    # variable holding element symbol (e.g., "N")
  compound_label_param: <variable name>   # variable holding compound formula (e.g., "NH₃")
  decimal_places: 2                        # 2 for light-element compounds, 1 for heavy
```

**Result fields exposed as template tokens:** `finalPercent`, `finalPercentLatex`, `rawPercent`. Author may use `{finalPercent}` in `explanation_template`.

**Guardrails extended:** `passesGuardrails`'s existing `??` fallback chain (`finalSum ?? finalProduct ?? y ?? finalResult`) does not include `finalPercent`. Phase 3b adds `finalPercent` to the chain so `result_range` and `result_must_be_positive` work for mass-percent problems if a future spec uses them. Phase 3b's two mass-percent problems don't currently declare guardrails (mass percent is inherently bounded [0, 100]), but the chain extension is part of this PR for completeness.

```js
// Updated chain in passesGuardrails:
const final = parseFloat(
  computed.finalSum ?? computed.finalProduct ?? computed.y ??
  computed.finalResult ?? computed.finalPercent ?? '0'
);
```

### 4.2 New variable generator: `pick_one`

**Sampling (engine.js):**

```js
// In sampleValue, third branch:
if (spec.generator === 'pick_one') {
  if (!Array.isArray(spec.options) || spec.options.length === 0) {
    throw new Error('pick_one requires non-empty options array');
  }
  const idx = Math.floor(rng() * spec.options.length);
  return spec.options[idx];  // returns the option struct (object, not string)
}
```

**Struct unfolding (engine.js):**

```js
// In generateVariant, replace the existing param-population loop:
for (const [name, varSpec] of Object.entries(problemSpec.variables || {})) {
  const value = sampleValue(varSpec, rng);
  if (value !== null && typeof value === 'object') {
    // pick_one returned a struct → unfold into prefixed flat keys.
    for (const [k, v] of Object.entries(value)) {
      params[name + '_' + k] = String(v);
    }
  } else {
    params[name] = value;  // existing scalar path
  }
}
```

**YAML interface:**

```yaml
variables:
  compound:
    generator: pick_one
    options:
      - {formula: "NH₃",      element: "N", partial: 14.01, total: 17.03}
      - {formula: "NH₄NO₃",   element: "N", partial: 28.02, total: 80.04}
      - {formula: "Ca(NO₃)₂", element: "N", partial: 28.02, total: 164.10}
```

After sampling option 0, params dict contains:

```js
{
  compound_formula: "NH₃",
  compound_element: "N",
  compound_partial: "14.01",
  compound_total:   "17.03"
}
```

Templates and answer specs reference flat names (`{compound_formula}`, `partial_mass_param: compound_partial`, etc.).

### 4.3 Build pipeline changes

`SUPPORTED_OPERATIONS` in `build_interactive.py` adds `"mass_percent"`:

```python
SUPPORTED_OPERATIONS = {
    "subtract", "add", "multiply", "count_sig_figs",
    "to_sci_notation", "sci_notation_arithmetic", "linear_function",
    "factor_label", "mass_percent",
}
```

No other Python changes. `discover_chapters()` already iterates over every `chapter_NN.yaml`, so `chapter_09.yaml` is picked up automatically.

## 5. Problem manifest

### Ch 8 §8.4 — Mass-percent (2 problems, extending `chapter_08.yaml`)

| # | Variant strategy | Source stem | Match text |
|---|---|---|---|
| 1 | Compound varies, element fixed = N | Practice #3 in §8.4 area | "Mass percent of N in N₂O" |
| 2 | Element varies, compound fixed = CO₂ | Practice #7 in §8.4 area | "Mass percent of O in CO₂" |

**Problem 1 — compound varies (`8.4.mass_percent_compound_varies`):**

Variant set chooses from 6 N-containing compounds (N₂O, NO, NO₂, NH₃, NH₄NO₃, Ca(NO₃)₂). All compounds contain only light elements, so output is at 2 decimal places throughout.

**Problem 2 — element varies (`8.4.mass_percent_element_varies`):**

Variant chooses between asking for %C or %O within a single CO₂ compound. The two percentages should sum to 100% within rounding tolerance.

(Full YAML in §10 below.)

### Ch 9 §9.7–9.9 — Stoichiometry (6 problems, new file `chapter_09.yaml`)

| # | Idiom | Source stem (match_text) | Vary | Chain factors | Equation |
|---|---|---|---|---|---|
| 1 | mole-to-mole | "how many moles of H₂O from 5.0 mol H₂" | input mol | 1 (mole ratio, exact) | 2 H₂ + O₂ → 2 H₂O |
| 2 | mole-to-mole | "how many moles of NH₃ from 0.500 mol N₂" | input mol | 1 (mole ratio, exact) | N₂ + 3 H₂ → 2 NH₃ |
| 3 | mole-to-mass | "mass of CO₂ produced from 2.00 mol CaCO₃" | input mol | 2 (ratio + molar mass) | CaCO₃ → CaO + CO₂ |
| 4 | mole-to-mass | "Mass of CO₂ from 1.00 mol of C₃H₈" | input mol | 2 (ratio + molar mass) | C₃H₈ + 5 O₂ → 3 CO₂ + 4 H₂O |
| 5 | mass-to-mass | "mass of water from 8.00 g H₂" | input g | 3 (M + ratio + M) | 2 H₂ + O₂ → 2 H₂O |
| 6 | mass-to-mass | "mass of MgO from 12.0 g Mg" | input g | 3 (M + ratio + M) | 2 Mg + O₂ → 2 MgO |

All six use the existing `factor_label` operation with balanced-equation coefficients as `exact: true` mole-ratio factors. This generalizes Phase 3a problem 5's subscript-as-exact-factor idiom to balanced-equation context — same engine semantics, different source of the ratio (subscript → coefficient).

(Full YAML for representative problems in §10 below.)

## 6. Variant strategy summary

- **Mass-percent Problem 1** uses `pick_one` over 6 compound options. Each variant changes `compound_*` params (formula, element, partial mass, total mass).
- **Mass-percent Problem 2** uses `pick_one` over 2 element options. Each variant changes `element_*` params (symbol, formula, partial, total).
- **All 6 stoichiometry problems** use existing `range` generator on the input quantity (mol or grams). The balanced equation and molar masses stay fixed per problem.

## 7. Verification plan

### Pre-merge gates

| Check | Command | Pass criterion |
|---|---|---|
| Engine unit tests | `cd .firecrawl/interactive_engine && npm test` | 70/70 (60 existing + ~10 new) |
| Python tests | `python -m unittest test_build_interactive` | 14/14 (no Python regression) |
| Schema + match | `python .firecrawl/build_interactive.py --validate` | All 26 problems across 4 chapters validated |
| Fuzz | `python .firecrawl/build_interactive.py --fuzz 1000` | 26,000 / 26,000 variants pass |
| Eyeball | `--show-samples 5` per chapter | Generated questions read naturally |

### New test cases (engine.test.js, ~10 tests)

- `sampleValue: pick_one returns option struct`
- `sampleValue: pick_one with seeded rng is deterministic`
- `sampleValue: pick_one throws on empty options`
- `generateVariant: pick_one unfolds struct into prefixed params`
- `mass_percent: textbook example NH₃ → 82.27% at 2 decimals`
- `mass_percent: heavy-element compound at 1 decimal`
- `renderLatexForOperation: mass_percent emits proper formula form`
- `generateVariant: mass_percent + pick_one end-to-end (compound varies)`
- `generateVariant: mass_percent + pick_one end-to-end (element varies)`
- `factorLabelChain: balanced-equation mole ratio (3-factor mass-to-mass, regression check)`

### Acceptance criteria (must all pass before merge)

- [ ] 8/8 new Phase 3b problems pass `--fuzz 1000` (8,000 variants)
- [ ] Phase 1 + 2 + 3a problems still pass (no regression — 18,000 variants)
- [ ] Engine tests: 70/70 pass
- [ ] Python tests: 14/14 still pass
- [ ] `HTML_Files/Chapter_08.html` and all `.docx` files byte-identical to pre-PR `main`
- [ ] `HTML_Files/interactive/Chapter_09.html` is a new file
- [ ] `HTML_Files/interactive/assets/engine.js` byte-identical to `.firecrawl/interactive_engine/engine.js` (Phase 2 stale-asset rule)

## 8. Risks and mitigations

**Risk:** New `mass_percent` operation diverges from the engine's `sig_figs` precision idiom by using `decimal_places`. Future maintainers may be surprised.

**Mitigation:** This design doc explicitly justifies the divergence (§3, §4.1). Two precision idioms is the natural reflection of two precision conventions in chemistry pedagogy (sig figs for chains, decimals for percentages). The spec doc is canonical.

**Risk:** Struct unfolding in `generateVariant` is a one-way transform; if a future use case needs the original struct, we'd have to re-fetch from `spec.options` by index.

**Mitigation:** No current use case needs the struct. If one arises in Phase 3c+, the unfolding logic can also store a sentinel reference (e.g., `params[name + '_$index'] = idx`) for round-tripping. Not built now — YAGNI.

**Risk:** Atomic-mass divergence (H = 1.01 in YAML vs 1.008 in textbook) creates a small inconsistency between live page and PDF source.

**Mitigation:** Documented in §3 as deliberate editorial uniformity. The variants still produce mass-conserving answers within textbook tolerance. If feedback suggests this confuses students, two paths: (a) update the textbook to match (a docx edit), or (b) introduce a 3-decimal exception for hydrogen specifically. Defer the call until evidence comes in.

## 9. Branch and PR plan

- **Branch:** `pilot-variable-problems-phase3b` (matches Phase-N naming convention)
- **Commit structure (one commit per logical chunk):**
  1. Spec doc — this file. First commit on the branch.
  2. Engine changes — `engine.js` + `engine.test.js` + `build_interactive.py` SUPPORTED_OPERATIONS update.
  3. Ch 8 mass-percent — extension to `chapter_08.yaml` + rebuilt `HTML_Files/interactive/Chapter_08.html`.
  4. Ch 9 stoichiometry — new `chapter_09.yaml` + new `HTML_Files/interactive/Chapter_09.html`.
  5. Final asset sync — verify `HTML_Files/interactive/assets/engine.js` matches source.
- **PR title:** "Phase 3b: mass-percent + Ch 9 stoichiometry (8 new variant problems)"
- **PR body:** summarize the 8 problems, link this spec, list verification commands.
- **Merge strategy:** merge commit (matches PRs #4, #5, #6, #7).

## 10. Concrete YAML specs (representative, not exhaustive)

### Mass-percent Problem 1 (compound varies)

```yaml
- id: "8.4.mass_percent_compound_varies"
  match_text: "Mass percent of N in N₂O"
  question: "What is the mass percent of {compound_element} in {compound_formula}?"
  variables:
    compound:
      generator: pick_one
      options:
        - {formula: "N₂O",      element: "N", partial: 28.02, total: 44.02}
        - {formula: "NO",       element: "N", partial: 14.01, total: 30.01}
        - {formula: "NO₂",      element: "N", partial: 14.01, total: 46.01}
        - {formula: "NH₃",      element: "N", partial: 14.01, total: 17.03}
        - {formula: "NH₄NO₃",   element: "N", partial: 28.02, total: 80.04}
        - {formula: "Ca(NO₃)₂", element: "N", partial: 28.02, total: 164.10}
  answer:
    operation: mass_percent
    partial_mass_param: compound_partial
    total_mass_param: compound_total
    element_label_param: compound_element
    compound_label_param: compound_formula
    decimal_places: 2
  explanation_template: |
    Mass of {compound_element} per mole of {compound_formula} is {compound_partial} g;
    molar mass is {compound_total} g/mol.
    {finalPercent}% {compound_element} by mass.
```

### Mass-percent Problem 2 (element varies)

```yaml
- id: "8.4.mass_percent_element_varies"
  match_text: "Mass percent of O in CO₂"
  question: "What is the mass percent of {element_symbol} in {element_formula}?"
  variables:
    element:
      generator: pick_one
      options:
        - {symbol: "C", formula: "CO₂", partial: 12.01, total: 44.01}
        - {symbol: "O", formula: "CO₂", partial: 32.00, total: 44.01}
  answer:
    operation: mass_percent
    partial_mass_param: element_partial
    total_mass_param: element_total
    element_label_param: element_symbol
    compound_label_param: element_formula
    decimal_places: 2
  explanation_template: |
    {element_symbol} contributes {element_partial} g per mole of {element_formula}.
    {finalPercent}% {element_symbol} by mass.
```

### Stoichiometry Problem 5 (mass-to-mass, the hardest idiom)

```yaml
- id: "9.9.mass_to_mass_water"
  match_text: "mass of water from 8.00 g H₂"
  question: "For 2 H₂ + O₂ → 2 H₂O, what mass of water is produced from {mass_h2} g H₂? (M(H₂) = 2.02, M(H₂O) = 18.02.)"
  variables:
    mass_h2: { range: [1.0, 30.0], sig_figs: 3 }
  answer:
    operation: factor_label
    value_param: mass_h2
    input_unit: g H₂
    chain:
      - num_value: 1
        num_unit: mol H₂
        den_value: 2.02
        den_unit: g H₂
        sig_figs: 3
      - num_value: 2
        num_unit: mol H₂O
        den_value: 2
        den_unit: mol H₂
        exact: true
      - num_value: 18.02
        num_unit: g H₂O
        den_value: 1
        den_unit: mol H₂O
        sig_figs: 4
    target_unit: g H₂O
  explanation_template: |
    Three factors: molar mass of H₂, balanced-equation mole ratio (2:2 = 1:1), molar mass of H₂O.
    {limitingSigFigs} sig figs from "{mass_h2} g H₂" yield {finalResult} g H₂O.
```

The remaining 5 stoichiometry problems follow the same pattern:
- 2 mole-to-mole problems use a 1-factor chain (mole ratio, exact).
- 2 mole-to-mass problems use a 2-factor chain (mole ratio + product molar mass).
- 1 more mass-to-mass problem (Mg + O₂ → MgO) uses a 3-factor chain similar to the example above.

Full YAML for all 8 problems will be authored during implementation per the writing-plans output.

## 11. Open follow-ups (Phase 3c+)

- **Percent yield** — same shape as `mass_percent`. Either reuse `mass_percent` with semantically distinct param names, or add a thin `percent_yield` alias. Phase 3c.
- **Pre-commit asset-sync guard** (Phase 2 lesson, still open) — Python pre-commit check that `HTML_Files/interactive/assets/engine.js` matches `.firecrawl/interactive_engine/engine.js`. Tiny PR; can land as polish at any time.
- **NaN/Infinity check in fuzz harness** — defensive check in `cmd_fuzz` that rejects variants whose `computed.finalResult` (or `finalPercent`) is non-finite. Closes the PyYAML-bare-exponent bug class.
- **Empirical / molecular formula problems** — multi-step ratios with branching; needs a new operation. Phase 3c+.
- **Limiting reactant** — comparison logic between products. Phase 4+.
- **Engine-side molar-mass and unit-conversion table** — reduce YAML verbosity. Worth doing only after pain is felt across 30+ DA problems.
