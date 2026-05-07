# Variable-Problem Pilot — Phase 2 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add factor-label / dimensional-analysis capability to the variable-problem engine and ship a 6-problem pilot for Chapter 2.

**Architecture:** Extend Phase 1's `engine.js` with two new pure functions (`factorLabelChain`, `renderFactorLabelLatex`) and wire them into the existing `computeAnswer` and `renderLatexForOperation` dispatchers. Refactor `build_interactive.py` to auto-discover any `chapter_*.yaml` and build all chapters in one run. Author `chapter_02.yaml` with 6 dimensional-analysis problems covering metric, English↔metric, density, dosage, mass percent, and a real-world cost chain.

**Tech Stack:**
- **Engine:** Vanilla ES-module JavaScript (no deps), tested via Node 20+'s built-in `node:test` runner. Auto-bootstraps in browsers; `MathJax.typesetPromise` retypeset (defended against startup-promise race per Phase 1's `maybeTypeset` helper).
- **Build script (Python):** `build_interactive.py` using `PyYAML`, `beautifulsoup4`. Tests via built-in `unittest`.
- **Browser:** MathJax 3 with the `cancel` extension (already configured by `build_html.py`).
- **CI:** GitHub Actions extends the existing `pages.yml`. After this plan, the workflow's per-chapter commands automatically iterate over every discovered chapter spec without further changes.

**Predecessor:** `docs/superpowers/specs/2026-05-06-variable-problems-phase2-design.md` (committed 15c1c3b). Supersedes nothing — extends Phase 1.

**Repo conventions:** Per `CLAUDE.md`, no `Co-Authored-By: Claude` trailer on commits. YAML and JS use **snake_case** for spec field names (`num_value`, `den_unit`, `sig_figs`, `value_param`, `input_unit`, `target_unit`) consistent with Phase 1's `decimal_places`, `result_must_be_positive`, etc.

---

## Decided Open Questions

These were flagged "to settle in implementation plan" in the spec (§11). Locking in here:

| # | Question | Decision |
|---|---|---|
| 1 | Specific source problems in Ch 2 | All six chosen and verified to be unique substrings in `HTML_Files/Chapter_02.html` (see Phase C below). |
| 2 | RNG seeding helper for non-numeric problem IDs | Keep Phase 1's `parseInt(prob.id.replace(/\D/g, '') || '1', 10)`. For Ch 2 IDs like `2.4.metric_simple`, this yields `24`; sufficient for variant determinism. Hashing is a Phase 3+ refinement. |
| 3 | `renderLatexForOperation` signature | Already accepts `answerSpec`. The `factor_label` case extracts `value_param`, `input_unit`, `chain` from it. No signature change. |
| 4 | Test isolation — split engine.test.js? | Keep one file. Phase 2 adds ~10 tests; total stays under 50. Split if/when it crosses 80. |
| 5 | CI runtime | Each chapter's `--fuzz 1000` adds ~2s. Total CI run still under one minute. No concern. |

---

## File Structure

**Modified files (existing):**

```
.firecrawl/interactive_engine/engine.js            # +2 exports + 2 case branches
.firecrawl/interactive_engine/engine.test.js       # +~10 tests for factor-label primitives
.firecrawl/build_interactive.py                    # multi-chapter discovery + --chapter flag
.firecrawl/test_build_interactive.py               # +~3 tests for discovery
.github/workflows/pages.yml                        # no change (commands now auto-iterate)
```

**New files:**

```
.firecrawl/interactive_specs/chapter_02.yaml       # 6 pilot problems
HTML_Files/interactive/Chapter_02.html             # build output (committed)
HTML_Files/interactive/assets/                     # already exists from Ch 1; engine.js / engine.css are shared
```

**Files NOT changed:**

- Any `.docx` chapter source (verified byte-identical at the end).
- `.firecrawl/build_html.py`.
- `HTML_Files/Chapter_*.html` (canonical build output beyond the `interactive/` subdir).
- Phase 1's `chapter_01.yaml` and `HTML_Files/interactive/Chapter_01.html` (continue to ship unchanged; regression-checked at the end).
- All other top-level project files.

---

## Engine API (defined upfront for cross-task consistency)

The new exports added in Phase 2:

```js
/**
 * Apply a chain of conversion factors to a starting value.
 * Returns a result object with sig-fig propagation across exact and inexact factors.
 * Throws on chain cancellation mismatches.
 *
 * @param {string} value          - input value, kept as string to preserve sig figs
 * @param {number} valueSigFigs   - sig figs of the input value
 * @param {string} valueUnit      - unit of input value (must equal chain[0].den_unit)
 * @param {Array<object>} steps   - each step: { num_value, num_unit, den_value, den_unit, exact?, sig_figs? }
 * @returns {{rawResult: string, finalResult: string, finalUnit: string, limitingSigFigs: number, limitingSource: string}}
 */
export function factorLabelChain(value, valueSigFigs, valueUnit, steps) { ... }

/**
 * Render a factor-label chain as MathJax LaTeX with \cancel{} on cancelled units.
 * Matches the textbook's Option-C convention.
 *
 * @returns {string} LaTeX string ready for MathJax typesetting
 */
export function renderFactorLabelLatex(value, valueUnit, steps, finalResult, finalUnit) { ... }
```

**Internal flow** (already established by Phase 1; just adding new branches):

- `computeAnswer(answerSpec, params)` → switch case `'factor_label'` → calls `factorLabelChain`
- `renderLatexForOperation(op, variant, answerSpec)` → switch case `'factor_label'` → calls `renderFactorLabelLatex`
- `passesGuardrails(constraints, params, computed)` → already a `??` chain; extends to include `computed.finalResult`

---

## YAML Schema for `factor_label` Operation

```yaml
- id: "<slug>"
  match_text: "<unique substring of problem stem>"
  question: "<template with {var} placeholders>"
  variables:
    <name>:
      range: [<low>, <high>]
      sig_figs: <n>           # OR decimal_places: <n>
  answer:
    operation: factor_label
    value_param: <var-name>   # which variable supplies the input value
    input_unit: <unit>        # must equal chain[0].den_unit
    chain:
      - num_value: <number>
        num_unit: <unit>
        den_value: <number>
        den_unit: <unit>      # must equal input_unit (step 0) or previous step's num_unit
        exact: <bool>         # if true, factor doesn't constrain sig figs
        sig_figs: <int>       # required if not exact
    target_unit: <unit>       # must equal chain[-1].num_unit
  constraints:                # optional
    result_range: [<low>, <high>]
    result_must_be_positive: <bool>
    avoid_round: [<value>, ...]
  explanation_template: |
    <prose with {token} substitutions; tokens include input variables AND
    {finalResult}, {finalUnit}, {limitingSigFigs}>
```

---

# Tasks

## Phase A — Engine factor-label primitives

### Task A1: `factorLabelChain` core math + sig-fig propagation + chain validation

**Files:**
- Modify: `.firecrawl/interactive_engine/engine.test.js`
- Modify: `.firecrawl/interactive_engine/engine.js`

- [ ] **Step 1: Pre-flight check**

Run: `cd .firecrawl/interactive_engine && node --test engine.test.js`
Expected: 35/35 pass (Phase 1 baseline).

If not, STOP and report `BLOCKED`.

- [ ] **Step 2: Append failing tests** to `engine.test.js`:

```js
import { factorLabelChain } from './engine.js';

test('factorLabelChain: single-step exact metric', () => {
  // 0.025 g × (1000 mg / 1 g) = 25 mg; sig figs = 2 (limited by 0.025)
  const r = factorLabelChain('0.025', 2, 'g', [
    { num_value: 1000, num_unit: 'mg', den_value: 1, den_unit: 'g', exact: true },
  ]);
  assert.equal(r.finalResult, '25');
  assert.equal(r.finalUnit, 'mg');
  assert.equal(r.limitingSigFigs, 2);
});

test('factorLabelChain: two-step English-metric mixed exact/inexact', () => {
  // 5.00 lb × (453.59 g / 1 lb) × (1 kg / 1000 g) = 2.27 kg; sig figs = 3 (limited by 5.00)
  const r = factorLabelChain('5.00', 3, 'lb', [
    { num_value: 453.59, num_unit: 'g',  den_value: 1, den_unit: 'lb', sig_figs: 5 },
    { num_value: 1,      num_unit: 'kg', den_value: 1000, den_unit: 'g', exact: true },
  ]);
  assert.equal(r.finalResult, '2.27');
  assert.equal(r.finalUnit, 'kg');
  assert.equal(r.limitingSigFigs, 3);
  assert.equal(r.limitingSource, 'value');
});

test('factorLabelChain: limiting sig figs from a non-exact factor', () => {
  // 100. yd × (0.9144 m / 1 yd) where 0.9144 is exact; result limited by 100. (3 sig figs) → 91.4
  // To test inexact-factor limiting: invent a factor with 2 sig figs
  const r = factorLabelChain('100.', 3, 'yd', [
    { num_value: 0.91, num_unit: 'm', den_value: 1, den_unit: 'yd', sig_figs: 2 },
  ]);
  assert.equal(r.finalResult, '91');  // limited by the 2-sig-fig factor
  assert.equal(r.limitingSigFigs, 2);
  assert.equal(r.limitingSource, 'step[0]');
});

test('factorLabelChain: density chain (kg → g → mL via density)', () => {
  // 1.50 kg × (1000 g / 1 kg) × (1 mL / 13.546 g) = 110.74... → 111 mL (3 sig figs)
  const r = factorLabelChain('1.50', 3, 'kg', [
    { num_value: 1000, num_unit: 'g',  den_value: 1,      den_unit: 'kg', exact: true },
    { num_value: 1,    num_unit: 'mL', den_value: 13.546, den_unit: 'g',  sig_figs: 5 },
  ]);
  assert.equal(r.finalResult, '111');
  assert.equal(r.finalUnit, 'mL');
  assert.equal(r.limitingSigFigs, 3);
});

test('factorLabelChain: throws on cancellation mismatch at step 0', () => {
  assert.throws(
    () => factorLabelChain('5.00', 3, 'lb', [
      { num_value: 1, num_unit: 'kg', den_value: 1, den_unit: 'oz', exact: true },  // den should be lb
    ]),
    /cancellation mismatch at step 0/i,
  );
});

test('factorLabelChain: throws on cancellation mismatch at step 1', () => {
  assert.throws(
    () => factorLabelChain('5.00', 3, 'lb', [
      { num_value: 453.59, num_unit: 'g',  den_value: 1, den_unit: 'lb', sig_figs: 5 },
      { num_value: 1,      num_unit: 'kg', den_value: 1, den_unit: 'mg', exact: true },  // should be g
    ]),
    /cancellation mismatch at step 1/i,
  );
});

test('factorLabelChain: missing sig_figs on non-exact factor throws', () => {
  assert.throws(
    () => factorLabelChain('5.00', 3, 'lb', [
      { num_value: 453.59, num_unit: 'g', den_value: 1, den_unit: 'lb' },  // neither exact nor sig_figs
    ]),
    /must declare sig_figs or set exact: true/i,
  );
});

test('factorLabelChain: dosage equivalence (mg per kg)', () => {
  // 70.0 kg × (5.00 mg / 1 kg) = 350. mg
  const r = factorLabelChain('70.0', 3, 'kg', [
    { num_value: 5.00, num_unit: 'mg', den_value: 1, den_unit: 'kg', sig_figs: 3 },
  ]);
  assert.equal(r.finalResult, '350');  // 350. but rounds to 350 string from formatWithSigFigs
  assert.equal(r.finalUnit, 'mg');
  assert.equal(r.limitingSigFigs, 3);
});
```

- [ ] **Step 3: Run, confirm fail**

Run: `node --test engine.test.js`
Expected: 8 failures (`factorLabelChain` not exported).

- [ ] **Step 4: Append implementation** to `engine.js` (after the `evaluateLinearFunction` block, before the bootstrap section):

```js
/**
 * Apply a chain of conversion factors to a starting value.
 * Validates that each step's denominator unit cancels with the previous numerator
 * (or with valueUnit for step 0). Tracks sig-fig propagation across exact and
 * inexact factors. Throws on cancellation mismatch or missing sig_figs.
 */
export function factorLabelChain(value, valueSigFigs, valueUnit, steps) {
  // Validate cancellation chain and sig-fig declarations
  let prevNumUnit = valueUnit;
  for (let i = 0; i < steps.length; i++) {
    const s = steps[i];
    if (s.den_unit !== prevNumUnit) {
      throw new Error(
        'factorLabelChain: cancellation mismatch at step ' + i +
        ': expected den_unit "' + prevNumUnit + '", got "' + s.den_unit + '"'
      );
    }
    if (!s.exact && (s.sig_figs === undefined || s.sig_figs === null)) {
      throw new Error(
        'factorLabelChain: step ' + i + ' must declare sig_figs or set exact: true'
      );
    }
    prevNumUnit = s.num_unit;
  }

  // Compute raw result
  let result = parseFloat(value);
  for (const s of steps) {
    result = result * (s.num_value / s.den_value);
  }

  // Sig-fig propagation: input value + each non-exact factor's sig_figs
  let limitingSigFigs = valueSigFigs;
  let limitingSource = 'value';
  for (let i = 0; i < steps.length; i++) {
    const s = steps[i];
    if (!s.exact && s.sig_figs !== undefined && s.sig_figs < limitingSigFigs) {
      limitingSigFigs = s.sig_figs;
      limitingSource = 'step[' + i + ']';
    }
  }

  return {
    rawResult: result.toString(),
    finalResult: formatWithSigFigs(result, limitingSigFigs),
    finalUnit: prevNumUnit,
    limitingSigFigs,
    limitingSource,
  };
}
```

- [ ] **Step 5: Run, confirm pass**

Run: `node --test engine.test.js`
Expected: 43 tests pass (35 prior + 8 new).

- [ ] **Step 6: Commit**

```bash
git add .firecrawl/interactive_engine/engine.js .firecrawl/interactive_engine/engine.test.js
git commit -m "Add factorLabelChain() engine primitive with tests"
```

---

### Task A2: `renderFactorLabelLatex` — chain-as-LaTeX with `\cancel{}`

**Files:**
- Modify: `.firecrawl/interactive_engine/engine.test.js`
- Modify: `.firecrawl/interactive_engine/engine.js`

- [ ] **Step 1: Pre-flight check**

Run: `node --test engine.test.js` — expect 43/43 pass.

- [ ] **Step 2: Append failing tests**:

```js
import { renderFactorLabelLatex } from './engine.js';

test('renderFactorLabelLatex: single-step exact metric', () => {
  const latex = renderFactorLabelLatex(
    '0.025', 'g',
    [{ num_value: 1000, num_unit: 'mg', den_value: 1, den_unit: 'g', exact: true }],
    '25', 'mg'
  );
  // 0.025\,\cancel{\text{g}} \times \frac{1000\,\text{mg}}{1\,\cancel{\text{g}}} = 25\,\text{mg}
  assert.match(latex, /0\.025\\,\\cancel\{\\text\{g\}\}/);
  assert.match(latex, /\\frac\{1000\\,\\text\{mg\}\}\{1\\,\\cancel\{\\text\{g\}\}\}/);
  assert.match(latex, /=\s*25\\,\\text\{mg\}/);
});

test('renderFactorLabelLatex: two-step chain has both \\cancel{} segments', () => {
  const latex = renderFactorLabelLatex(
    '5.00', 'lb',
    [
      { num_value: 453.59, num_unit: 'g',  den_value: 1, den_unit: 'lb', sig_figs: 5 },
      { num_value: 1,      num_unit: 'kg', den_value: 1000, den_unit: 'g', exact: true },
    ],
    '2.27', 'kg'
  );
  assert.match(latex, /5\.00\\,\\cancel\{\\text\{lb\}\}/);
  assert.match(latex, /\\cancel\{\\text\{lb\}\}\}/);  // lb cancellation in step 0 denominator
  assert.match(latex, /\\cancel\{\\text\{g\}\}/);     // g cancellation in step 1 denominator
  assert.match(latex, /=\s*2\.27\\,\\text\{kg\}/);
});

test('renderFactorLabelLatex: unit names with spaces', () => {
  // mass-percent style: g alloy → g Ag
  const latex = renderFactorLabelLatex(
    '50.0', 'g alloy',
    [{ num_value: 35.0, num_unit: 'g Ag', den_value: 100, den_unit: 'g alloy', sig_figs: 3 }],
    '17.5', 'g Ag'
  );
  assert.match(latex, /\\cancel\{\\text\{g alloy\}\}/);  // works with spaces
  assert.match(latex, /\\text\{g Ag\}/);                 // numerator unit
  assert.match(latex, /=\s*17\.5\\,\\text\{g Ag\}/);
});

test('renderFactorLabelLatex: chain has explicit \\times separators between steps', () => {
  const latex = renderFactorLabelLatex(
    '5.00', 'lb',
    [
      { num_value: 453.59, num_unit: 'g',  den_value: 1, den_unit: 'lb', sig_figs: 5 },
      { num_value: 1,      num_unit: 'kg', den_value: 1000, den_unit: 'g', exact: true },
    ],
    '2.27', 'kg'
  );
  // Should be value\,\cancel{\text{...}} \times \frac{...}{...} \times \frac{...}{...} = result\,\text{...}
  const timesMatches = latex.match(/\\times/g) || [];
  assert.equal(timesMatches.length, 2);
});
```

- [ ] **Step 3: Run, confirm fail**

Run: `node --test engine.test.js`
Expected: 4 failures (`renderFactorLabelLatex` not exported).

- [ ] **Step 4: Append implementation** to `engine.js`:

```js
/**
 * Render a factor-label chain as MathJax LaTeX with \cancel{} on cancelled units.
 * Output format matches the textbook's Option-C convention exactly:
 *   value\,\cancel{\text{unit}} \times \frac{num\,\text{numUnit}}{den\,\cancel{\text{denUnit}}} ... = result\,\text{finalUnit}
 */
export function renderFactorLabelLatex(value, valueUnit, steps, finalResult, finalUnit) {
  let latex = value + '\\,\\cancel{\\text{' + valueUnit + '}}';
  for (const s of steps) {
    latex += ' \\times \\frac{' + s.num_value + '\\,\\text{' + s.num_unit + '}}'
           + '{' + s.den_value + '\\,\\cancel{\\text{' + s.den_unit + '}}}';
  }
  latex += ' = ' + finalResult + '\\,\\text{' + finalUnit + '}';
  return latex;
}
```

- [ ] **Step 5: Run, confirm pass**

Run: `node --test engine.test.js`
Expected: 47 tests pass (43 prior + 4 new).

- [ ] **Step 6: Commit**

```bash
git add .firecrawl/interactive_engine/engine.js .firecrawl/interactive_engine/engine.test.js
git commit -m "Add renderFactorLabelLatex() engine primitive with tests"
```

---

### Task A3: Integrate `factor_label` into `computeAnswer` + `renderLatexForOperation` + guardrails

**Files:**
- Modify: `.firecrawl/interactive_engine/engine.test.js`
- Modify: `.firecrawl/interactive_engine/engine.js`

- [ ] **Step 1: Pre-flight check**

Run: `node --test engine.test.js` — expect 47/47 pass.

- [ ] **Step 2: Append failing tests**:

```js
test('generateVariant: factor_label end-to-end', () => {
  const spec = {
    id: 'test.factor_label',
    variables: {
      mass: { range: [1.0, 10.0], decimal_places: 2 },
    },
    answer: {
      operation: 'factor_label',
      value_param: 'mass',
      input_unit: 'lb',
      chain: [
        { num_value: 453.59, num_unit: 'g',  den_value: 1, den_unit: 'lb', sig_figs: 5 },
        { num_value: 1,      num_unit: 'kg', den_value: 1000, den_unit: 'g', exact: true },
      ],
      target_unit: 'kg',
    },
  };
  const rng = mulberry32(42);
  const v = generateVariant(spec, rng);
  assert.ok('mass' in v.params);
  assert.ok(parseFloat(v.computed.finalResult) > 0);
  assert.equal(v.computed.finalUnit, 'kg');
});

test('renderLatexForOperation: factor_label dispatches correctly', () => {
  const variant = {
    params: { mass: '5.00' },
    computed: {
      rawResult: '2.26795',
      finalResult: '2.27',
      finalUnit: 'kg',
      limitingSigFigs: 3,
    },
  };
  const answerSpec = {
    operation: 'factor_label',
    value_param: 'mass',
    input_unit: 'lb',
    chain: [
      { num_value: 453.59, num_unit: 'g',  den_value: 1, den_unit: 'lb', sig_figs: 5 },
      { num_value: 1,      num_unit: 'kg', den_value: 1000, den_unit: 'g', exact: true },
    ],
  };
  const latex = renderLatexForOperation('factor_label', variant, answerSpec);
  assert.match(latex, /5\.00\\,\\cancel\{\\text\{lb\}\}/);
  assert.match(latex, /=\s*2\.27\\,\\text\{kg\}/);
});

test('passesGuardrails: result_range works with factor_label finalResult', () => {
  const spec = {
    id: 'test.factor_label_constrained',
    variables: {
      mass: { range: [1.0, 1.0], decimal_places: 1 },  // always 1.0
    },
    answer: {
      operation: 'factor_label',
      value_param: 'mass',
      input_unit: 'lb',
      chain: [
        { num_value: 1, num_unit: 'kg', den_value: 1, den_unit: 'lb', exact: true },
      ],
      target_unit: 'kg',
    },
    constraints: { result_range: [100, 200] },  // never satisfied (result is 1.0 kg)
  };
  const rng = mulberry32(42);
  assert.throws(() => generateVariant(spec, rng), /guardrail/i);
});
```

- [ ] **Step 3: Run, confirm fail**

Run: `node --test engine.test.js`
Expected: 3 failures (factor_label not handled in switch).

- [ ] **Step 4: Modify `computeAnswer`** in `engine.js`. Find the switch statement and add a case BEFORE `default:`:

```js
    case 'factor_label': {
      const value = params[answerSpec.value_param];
      const valueSigFigs = countSigFigs(value).count;
      return factorLabelChain(value, valueSigFigs, answerSpec.input_unit, answerSpec.chain);
    }
```

- [ ] **Step 5: Modify `renderLatexForOperation`** in `engine.js`. Find the switch statement and add a case BEFORE `default:`:

```js
    case 'factor_label':
      return renderFactorLabelLatex(
        p[answerSpec.value_param],
        answerSpec.input_unit,
        answerSpec.chain,
        c.finalResult,
        c.finalUnit
      );
```

- [ ] **Step 6: Modify `passesGuardrails`** in `engine.js`. Update the `??` chain to include `finalResult`:

Find this line (currently appears twice — once in `result_must_be_positive`, once in `result_range`):

```js
    const final = parseFloat(computed.finalSum ?? computed.finalProduct ?? computed.y ?? '0');
```

Replace **both occurrences** with:

```js
    const final = parseFloat(computed.finalSum ?? computed.finalProduct ?? computed.y ?? computed.finalResult ?? '0');
```

- [ ] **Step 7: Run, confirm pass**

Run: `node --test engine.test.js`
Expected: 50 tests pass (47 prior + 3 new).

- [ ] **Step 8: Commit**

```bash
git add .firecrawl/interactive_engine/engine.js .firecrawl/interactive_engine/engine.test.js
git commit -m "Wire factor_label op into computeAnswer + renderLatex + guardrails"
```

---

## Phase B — Multi-chapter build script

### Task B1: `discover_chapters()` helper with tests

**Files:**
- Modify: `.firecrawl/build_interactive.py`
- Modify: `.firecrawl/test_build_interactive.py`

- [ ] **Step 1: Pre-flight check**

Run: `python .firecrawl/test_build_interactive.py`
Expected: 8/8 pass.

- [ ] **Step 2: Append failing test** to `test_build_interactive.py`:

```python
from build_interactive import discover_chapters


class TestDiscoverChapters(unittest.TestCase):
    def test_finds_chapter_01_yaml(self):
        chapters = discover_chapters()
        ids = [c['number'] for c in chapters]
        self.assertIn('01', ids, msg=f'Expected 01 in {ids}')

    def test_each_entry_has_required_fields(self):
        chapters = discover_chapters()
        self.assertGreaterEqual(len(chapters), 1)
        for c in chapters:
            self.assertIn('number', c)
            self.assertIn('spec_path', c)
            self.assertIn('input_html', c)
            self.assertIn('output_html', c)

    def test_paths_resolve_to_real_files(self):
        chapters = discover_chapters()
        for c in chapters:
            self.assertTrue(c['spec_path'].exists(), msg=f"spec missing: {c['spec_path']}")
            # input_html must exist for the build to work; output_html may not exist yet
            self.assertTrue(c['input_html'].exists(), msg=f"input HTML missing: {c['input_html']}")
```

- [ ] **Step 3: Run, confirm fail**

Run: `python .firecrawl/test_build_interactive.py`
Expected: ImportError on `from build_interactive import discover_chapters`.

- [ ] **Step 4: Add to `build_interactive.py`** — insert AFTER the existing path constants and BEFORE the `def main()`:

```python
def discover_chapters() -> list[dict]:
    """Find every chapter_NN.yaml spec in interactive_specs/ and return
    a list of dicts with the chapter number and its associated paths.
    """
    spec_dir = REPO / ".firecrawl" / "interactive_specs"
    chapters = []
    for spec_path in sorted(spec_dir.glob("chapter_*.yaml")):
        # Extract NN from filename like "chapter_02.yaml"
        stem = spec_path.stem  # e.g., "chapter_02"
        if not stem.startswith("chapter_"):
            continue
        number = stem[len("chapter_"):]
        chapters.append({
            "number": number,
            "spec_path": spec_path,
            "input_html": REPO / "HTML_Files" / f"Chapter_{number}.html",
            "output_html": REPO / "HTML_Files" / "interactive" / f"Chapter_{number}.html",
        })
    return chapters
```

Also, **remove the now-redundant single-chapter constants** (`SPEC_FILE`, `INPUT_HTML`, `OUTPUT_HTML`). They will be replaced by per-chapter discovery in subsequent tasks. Keep `OUTPUT_DIR` and `ASSETS_DIR` (the latter is still chapter-agnostic).

After this edit, the path constants block should look like:

```python
REPO = Path(__file__).resolve().parents[1]
ENGINE_DIR = REPO / ".firecrawl" / "interactive_engine"
OUTPUT_DIR = REPO / "HTML_Files" / "interactive"
ASSETS_DIR = OUTPUT_DIR / "assets"
```

- [ ] **Step 5: Run, confirm pass**

Run: `python .firecrawl/test_build_interactive.py`
Expected: 11 tests pass (8 prior + 3 new).

But wait — removing `SPEC_FILE` / `INPUT_HTML` / `OUTPUT_HTML` will break the existing `cmd_build`, `cmd_validate`, etc. that reference them. The tests for those will fail.

Actually, the tests for cmd_build etc. don't reference these constants directly — they invoke the script. They'll break only if the existing single-chapter code paths remain that reference the deleted constants.

Resolution: keep the constants pointing at Ch 1 for now (`SPEC_FILE = REPO / ... "chapter_01.yaml"`, `INPUT_HTML = REPO / ... "Chapter_01.html"`, `OUTPUT_HTML = OUTPUT_DIR / "Chapter_01.html"`). They become DEAD CODE after Tasks B2–B4 refactor everything to use `discover_chapters()`. Removing them in Task B4 once nothing references them.

So this Step 4 should ADD `discover_chapters()` without touching the existing constants. Re-stating Step 4:

**Step 4 (corrected): Add to `build_interactive.py`** — insert AFTER the existing path constants and BEFORE the `def main()`:

```python
def discover_chapters() -> list[dict]:
    """Find every chapter_NN.yaml spec in interactive_specs/ and return
    a list of dicts with the chapter number and its associated paths.
    """
    spec_dir = REPO / ".firecrawl" / "interactive_specs"
    chapters = []
    for spec_path in sorted(spec_dir.glob("chapter_*.yaml")):
        stem = spec_path.stem  # e.g., "chapter_02"
        if not stem.startswith("chapter_"):
            continue
        number = stem[len("chapter_"):]
        chapters.append({
            "number": number,
            "spec_path": spec_path,
            "input_html": REPO / "HTML_Files" / f"Chapter_{number}.html",
            "output_html": REPO / "HTML_Files" / "interactive" / f"Chapter_{number}.html",
        })
    return chapters
```

Do NOT touch the existing `SPEC_FILE` / `INPUT_HTML` / `OUTPUT_HTML` constants in this task. They remain pointing at Ch 1 and are removed in Task B4.

- [ ] **Step 6: Commit**

```bash
git add .firecrawl/build_interactive.py .firecrawl/test_build_interactive.py
git commit -m "Add discover_chapters() helper for multi-chapter build"
```

---

### Task B2: Refactor `cmd_build` for multi-chapter

**Files:**
- Modify: `.firecrawl/build_interactive.py`

- [ ] **Step 1: Replace `cmd_build` body** with this multi-chapter version:

```python
def cmd_build(filter_chapter: str | None = None) -> int:
    chapters = discover_chapters()
    if filter_chapter:
        chapters = [c for c in chapters if c['number'] == filter_chapter]
        if not chapters:
            print(f"ERROR: no chapter '{filter_chapter}' found.", file=sys.stderr)
            return 2
    OUTPUT_DIR.mkdir(exist_ok=True)
    ASSETS_DIR.mkdir(exist_ok=True)
    # Copy engine assets once (shared across chapters)
    shutil.copy2(ENGINE_DIR / "engine.js", ASSETS_DIR / "engine.js")
    shutil.copy2(ENGINE_DIR / "engine.css", ASSETS_DIR / "engine.css")
    for c in chapters:
        spec = load_spec(c['spec_path'])
        if not c['input_html'].exists():
            print(f"ERROR: {c['input_html']} not found. Run build_html.py first.", file=sys.stderr)
            return 2
        html = c['input_html'].read_text(encoding="utf-8")
        html = attach_variant_attrs(html, spec)
        html = inline_spec_json(html, spec)
        c['output_html'].write_text(html, encoding="utf-8")
        print(f"Wrote {c['output_html']}")
    return 0
```

- [ ] **Step 2: Smoke test**

Run from the repo root:
```bash
python .firecrawl/build_interactive.py
```
Expected: prints `Wrote .../HTML_Files/interactive/Chapter_01.html` (with no Ch 2 spec yet, only Ch 1 builds).

Then:
```bash
ls HTML_Files/interactive/
ls HTML_Files/interactive/assets/
grep -c 'data-variant-spec=' HTML_Files/interactive/Chapter_01.html
```
Expected: `Chapter_01.html` exists; `assets/engine.js` and `assets/engine.css` exist; grep returns at least 1.

- [ ] **Step 3: Run unit tests**

Run: `python .firecrawl/test_build_interactive.py`
Expected: 11/11 pass.

- [ ] **Step 4: Commit**

```bash
git add .firecrawl/build_interactive.py
git commit -m "Refactor cmd_build for multi-chapter discovery"
```

---

### Task B3: Refactor `cmd_validate`, `cmd_show_samples`, `cmd_fuzz` for multi-chapter

**Files:**
- Modify: `.firecrawl/build_interactive.py`

- [ ] **Step 1: Replace `cmd_validate` body**:

```python
def cmd_validate(filter_chapter: str | None = None) -> int:
    chapters = discover_chapters()
    if filter_chapter:
        chapters = [c for c in chapters if c['number'] == filter_chapter]
        if not chapters:
            print(f"VALIDATE FAIL: no chapter '{filter_chapter}' found.", file=sys.stderr)
            return 1
    total_problems = 0
    for c in chapters:
        try:
            spec = load_spec(c['spec_path'])
        except ValidationError as e:
            print(f"VALIDATE FAIL: chapter {c['number']}: {e}", file=sys.stderr)
            return 1
        if not c['input_html'].exists():
            print(f"VALIDATE FAIL: {c['input_html']} not found.", file=sys.stderr)
            return 1
        html = c['input_html'].read_text(encoding="utf-8")
        try:
            attach_variant_attrs(html, spec)
        except ValidationError as e:
            print(f"VALIDATE FAIL: chapter {c['number']}: {e}", file=sys.stderr)
            return 1
        n = len(spec.get("problems", []))
        total_problems += n
        print(f"VALIDATE OK: chapter {c['number']}: {n} problems.")
    print(f"VALIDATE OK: {total_problems} problems across {len(chapters)} chapter(s).")
    return 0
```

- [ ] **Step 2: Replace `cmd_show_samples` body**:

```python
def cmd_show_samples(n: int, filter_chapter: str | None = None) -> int:
    chapters = discover_chapters()
    if filter_chapter:
        chapters = [c for c in chapters if c['number'] == filter_chapter]
    import subprocess as sp
    for c in chapters:
        spec = load_spec(c['spec_path'])
        spec_json = json.dumps(spec)
        spec_tmp = REPO / ".firecrawl" / "interactive_engine" / f"_spec_for_driver_{c['number']}.json"
        spec_tmp.write_text(spec_json, encoding="utf-8")
        try:
            r = sp.run(
                ["node", "sample_driver.js", str(spec_tmp.name), str(n)],
                capture_output=True, text=True,
                cwd=str(ENGINE_DIR), check=False,
            )
        finally:
            spec_tmp.unlink(missing_ok=True)
        if r.returncode != 0:
            print(f"SHOW-SAMPLES FAIL (chapter {c['number']}): {r.stderr}", file=sys.stderr)
            return 1
        payload = json.loads(r.stdout)
        for prob in payload["samples"]:
            print(f"\n=== chapter {c['number']} :: {prob['id']} (failures: {prob['failures']}/{n}) ===")
            for i, v in enumerate(prob["variants"]):
                if "error" in v:
                    print(f"  [{i}] ERROR: {v['error']}")
                else:
                    params = v.get("params", {})
                    computed = v.get("computed", {})
                    print(f"  [{i}] params={params}  ->  computed={computed}")
    return 0
```

- [ ] **Step 3: Replace `cmd_fuzz` body**:

```python
def cmd_fuzz(n: int, filter_chapter: str | None = None) -> int:
    chapters = discover_chapters()
    if filter_chapter:
        chapters = [c for c in chapters if c['number'] == filter_chapter]
    import subprocess as sp
    import re
    placeholder_re = re.compile(r"\{[a-zA-Z_]\w*\}")
    failed = False
    for c in chapters:
        spec = load_spec(c['spec_path'])
        spec_json = json.dumps(spec)
        spec_tmp = REPO / ".firecrawl" / "interactive_engine" / f"_spec_for_driver_{c['number']}.json"
        spec_tmp.write_text(spec_json, encoding="utf-8")
        try:
            r = sp.run(
                ["node", "sample_driver.js", str(spec_tmp.name), str(n)],
                capture_output=True, text=True,
                cwd=str(ENGINE_DIR), check=False,
            )
        finally:
            spec_tmp.unlink(missing_ok=True)
        if r.returncode != 0:
            print(f"FUZZ FAIL (chapter {c['number']}): {r.stderr}", file=sys.stderr)
            failed = True
            continue
        payload = json.loads(r.stdout)
        for prob in payload["samples"]:
            if prob["failures"] > 0:
                print(f"FUZZ FAIL: chapter {c['number']} :: {prob['id']} had {prob['failures']}/{n} guardrail failures",
                      file=sys.stderr)
                failed = True
                continue
            spec_entry = next(p for p in spec["problems"] if p["id"] == prob["id"])
            if "custom_js" in spec_entry:
                continue
            template = spec_entry["explanation_template"]
            for i, v in enumerate(prob["variants"][:5]):
                tokens = {**v["params"], **(v["computed"] if isinstance(v["computed"], dict) else {})}
                substituted = template
                for k, val in tokens.items():
                    substituted = substituted.replace("{" + k + "}", str(val))
                leftover = placeholder_re.findall(substituted)
                if leftover:
                    print(f"FUZZ FAIL: chapter {c['number']} :: {prob['id']} variant {i} has unfilled tokens: {leftover}",
                          file=sys.stderr)
                    failed = True
            print(f"FUZZ OK: chapter {c['number']} :: {prob['id']} {n}/{n} variants passed.")
    return 1 if failed else 0
```

- [ ] **Step 4: Smoke test all three commands**

```bash
python .firecrawl/build_interactive.py --validate
python .firecrawl/build_interactive.py --fuzz 1000
python .firecrawl/build_interactive.py
python .firecrawl/test_build_interactive.py
```

Expected:
- `--validate` → "VALIDATE OK: chapter 01: 6 problems." then "VALIDATE OK: 6 problems across 1 chapter(s)."
- `--fuzz 1000` → 6 lines of "FUZZ OK: chapter 01 :: <id> 1000/1000 variants passed."
- build → "Wrote .../HTML_Files/interactive/Chapter_01.html"
- unit tests → 11/11 pass.

- [ ] **Step 5: Commit**

```bash
git add .firecrawl/build_interactive.py
git commit -m "Refactor cmd_validate / cmd_show_samples / cmd_fuzz for multi-chapter"
```

---

### Task B4: Add `--chapter NN` CLI flag, remove dead constants

**Files:**
- Modify: `.firecrawl/build_interactive.py`

- [ ] **Step 1: Update `main()` to accept and forward `--chapter`**:

Replace the existing `main()` body with:

```python
def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--validate", action="store_true",
                   help="parse and verify all chapter specs without writing output")
    p.add_argument("--show-samples", type=int, metavar="N",
                   help="print N sampled variants per problem")
    p.add_argument("--fuzz", type=int, metavar="N",
                   help="generate N variants per problem and assert all pass guardrails")
    p.add_argument("--chapter", type=str, metavar="NN",
                   help="limit to a single chapter (e.g. '02'); default is all discovered")
    args = p.parse_args()

    if args.validate:
        return cmd_validate(args.chapter)
    if args.show_samples is not None:
        return cmd_show_samples(args.show_samples, args.chapter)
    if args.fuzz is not None:
        return cmd_fuzz(args.fuzz, args.chapter)
    return cmd_build(args.chapter)
```

- [ ] **Step 2: Remove the now-dead single-chapter constants**

Delete these three lines (they're no longer referenced by any cmd_*):

```python
SPEC_FILE = REPO / ".firecrawl" / "interactive_specs" / "chapter_01.yaml"
INPUT_HTML = REPO / "HTML_Files" / "Chapter_01.html"
OUTPUT_HTML = OUTPUT_DIR / "Chapter_01.html"
```

After this, the constants block reads just:

```python
REPO = Path(__file__).resolve().parents[1]
ENGINE_DIR = REPO / ".firecrawl" / "interactive_engine"
OUTPUT_DIR = REPO / "HTML_Files" / "interactive"
ASSETS_DIR = OUTPUT_DIR / "assets"
```

- [ ] **Step 3: Append a CLI test** to `test_build_interactive.py`:

```python
class TestChapterFlag(unittest.TestCase):
    def test_chapter_flag_in_help(self):
        r = subprocess.run(
            [sys.executable, str(SCRIPT), "--help"],
            capture_output=True, text=True, cwd=str(REPO)
        )
        self.assertEqual(r.returncode, 0)
        self.assertIn("--chapter", r.stdout)

    def test_validate_chapter_01_explicit(self):
        r = subprocess.run(
            [sys.executable, str(SCRIPT), "--validate", "--chapter", "01"],
            capture_output=True, text=True, cwd=str(REPO)
        )
        self.assertEqual(r.returncode, 0, msg=r.stderr)

    def test_validate_unknown_chapter_fails(self):
        r = subprocess.run(
            [sys.executable, str(SCRIPT), "--validate", "--chapter", "99"],
            capture_output=True, text=True, cwd=str(REPO)
        )
        self.assertNotEqual(r.returncode, 0)
```

- [ ] **Step 4: Run all tests + smoke**

```bash
python .firecrawl/test_build_interactive.py
python .firecrawl/build_interactive.py --validate
python .firecrawl/build_interactive.py --validate --chapter 01
python .firecrawl/build_interactive.py
```

Expected:
- 14 tests pass (11 prior + 3 new).
- All four `--validate` / build invocations succeed.

- [ ] **Step 5: Commit**

```bash
git add .firecrawl/build_interactive.py .firecrawl/test_build_interactive.py
git commit -m "Add --chapter CLI flag; remove dead single-chapter constants"
```

---

## Phase C — Author 6 Chapter 2 pilot problems

Each task in this phase: append a YAML entry to `chapter_02.yaml`, run `--validate`, run `--fuzz 1000`, build, manual smoke check, commit.

### Task C0: Create empty `chapter_02.yaml`

**Files:**
- Create: `.firecrawl/interactive_specs/chapter_02.yaml`

- [ ] **Step 1: Create the empty spec file** with this content:

```yaml
# Variable-problem specs for Chapter 2 (Unit Systems and Dimensional Analysis).
# Schema reference: docs/superpowers/specs/2026-05-06-variable-problems-phase2-design.md
problems: []
```

- [ ] **Step 2: Verify discovery picks it up**

```bash
python .firecrawl/build_interactive.py --validate
```
Expected: "VALIDATE OK: chapter 01: 6 problems." AND "VALIDATE OK: chapter 02: 0 problems." then "VALIDATE OK: 6 problems across 2 chapter(s)."

- [ ] **Step 3: Commit**

```bash
git add .firecrawl/interactive_specs/chapter_02.yaml
git commit -m "Add empty Chapter 2 interactive spec scaffold"
```

---

### Task C1: Pilot problem 1 — single-step metric (µg → mg)

**Files:**
- Modify: `.firecrawl/interactive_specs/chapter_02.yaml`

- [ ] **Step 1: Verify match_text in HTML**

Run: `grep -c 'A medication dosage is 250 µg' HTML_Files/Chapter_02.html`
Expected: `1`.

- [ ] **Step 2: Replace contents** of `.firecrawl/interactive_specs/chapter_02.yaml` with:

```yaml
# Variable-problem specs for Chapter 2 (Unit Systems and Dimensional Analysis).
# Schema reference: docs/superpowers/specs/2026-05-06-variable-problems-phase2-design.md
problems:
  - id: "2.4.metric_simple"
    match_text: "A medication dosage is 250 µg"
    question: "A medication dosage is {dose} µg. How many mg is this?"
    variables:
      dose: { range: [10, 990], decimal_places: 0 }
    answer:
      operation: factor_label
      value_param: dose
      input_unit: µg
      chain:
        - num_value: 1
          num_unit: mg
          den_value: 1000
          den_unit: µg
          exact: true
      target_unit: mg
    explanation_template: |
      "µg" cancels, leaving "mg". {limitingSigFigs} sig figs from "{dose} µg" yield \({finalResult}\,\text{mg}\).
```

- [ ] **Step 3: Validate, fuzz, build**

```bash
python .firecrawl/build_interactive.py --validate
python .firecrawl/build_interactive.py --fuzz 1000
python .firecrawl/build_interactive.py
```

Expected:
- `--validate` → "VALIDATE OK: chapter 02: 1 problems."
- `--fuzz` → "FUZZ OK: chapter 02 :: 2.4.metric_simple 1000/1000 variants passed."
- build → "Wrote .../Chapter_02.html"

- [ ] **Step 4: Verify HTML output**

```bash
grep -c 'data-variant-spec="2.4.metric_simple"' HTML_Files/interactive/Chapter_02.html
```
Expected: `1`.

- [ ] **Step 5: Commit**

```bash
git add .firecrawl/interactive_specs/chapter_02.yaml HTML_Files/interactive/Chapter_02.html
git commit -m "Pilot problem 1: variable µg → mg conversion (§2.4)"
```

---

### Task C2: Pilot problem 2 — two-step English-metric (lb → g → kg)

**Files:**
- Modify: `.firecrawl/interactive_specs/chapter_02.yaml`

- [ ] **Step 1: Verify match_text**

Run: `grep -c 'Convert 5.00 lb to kg' HTML_Files/Chapter_02.html`
Expected: `1`.

- [ ] **Step 2: Append spec entry** to `chapter_02.yaml` (as a sibling list item under `problems:`):

```yaml
  - id: "2.7.eng_metric_chain"
    match_text: "Convert 5.00 lb to kg"
    question: "Convert {mass} lb to kg."
    variables:
      mass: { range: [1.0, 20.0], sig_figs: 3 }
    answer:
      operation: factor_label
      value_param: mass
      input_unit: lb
      chain:
        - num_value: 453.59
          num_unit: g
          den_value: 1
          den_unit: lb
          sig_figs: 5
        - num_value: 1
          num_unit: kg
          den_value: 1000
          den_unit: g
          exact: true
      target_unit: kg
    explanation_template: |
      "lb" cancels in step 1; "g" cancels in step 2. {limitingSigFigs} sig figs
      from "{mass} lb" yield \({finalResult}\,\text{kg}\).
```

- [ ] **Step 3: Validate, fuzz, build, verify**

Same commands as Task C1 Step 3–4. Expected: 2 problems pass; second `data-variant-spec="2.7.eng_metric_chain"` appears.

- [ ] **Step 4: Commit**

```bash
git add .firecrawl/interactive_specs/chapter_02.yaml HTML_Files/interactive/Chapter_02.html
git commit -m "Pilot problem 2: variable lb → g → kg conversion (§2.7)"
```

---

### Task C3: Pilot problem 3 — density chain (kg → g → mL via mercury density)

**Files:**
- Modify: `.firecrawl/interactive_specs/chapter_02.yaml`

- [ ] **Step 1: Verify match_text**

Run: `grep -c 'volume of 1.50 kg of mercury' HTML_Files/Chapter_02.html`
Expected: `1`.

- [ ] **Step 2: Append spec entry**:

```yaml
  - id: "2.8.density_chain"
    match_text: "volume of 1.50 kg of mercury"
    question: "What is the volume of {mass} kg of mercury (d = 13.546 g/mL)?"
    variables:
      mass: { range: [0.50, 5.00], sig_figs: 3 }
    answer:
      operation: factor_label
      value_param: mass
      input_unit: kg
      chain:
        - num_value: 1000
          num_unit: g
          den_value: 1
          den_unit: kg
          exact: true
        - num_value: 1
          num_unit: mL
          den_value: 13.546
          den_unit: g
          sig_figs: 5
      target_unit: mL
    constraints:
      result_must_be_positive: true
    explanation_template: |
      "kg" cancels in step 1; "g" cancels in step 2 via density.
      {limitingSigFigs} sig figs from "{mass} kg" yield \({finalResult}\,\text{mL}\).
```

- [ ] **Step 3: Validate, fuzz, build, verify**

Same as before. Expected: 3 problems pass.

- [ ] **Step 4: Commit**

```bash
git add .firecrawl/interactive_specs/chapter_02.yaml HTML_Files/interactive/Chapter_02.html
git commit -m "Pilot problem 3: variable density chain — mass to volume (§2.8)"
```

---

### Task C4: Pilot problem 4 — dosage equivalence (kg → mg)

**Files:**
- Modify: `.firecrawl/interactive_specs/chapter_02.yaml`

- [ ] **Step 1: Verify match_text**

Run: `grep -c '5.00 mg per kg of body mass' HTML_Files/Chapter_02.html`
Expected: `1`.

- [ ] **Step 2: Append spec entry**:

```yaml
  - id: "2.9.dosage"
    match_text: "5.00 mg per kg of body mass"
    question: "A drug is dosed at {rate} mg per kg of body mass. What dose is needed for a {weight} kg adult?"
    variables:
      rate: { range: [2.0, 10.0], sig_figs: 3 }
      weight: { range: [40.0, 100.0], sig_figs: 3 }
    answer:
      operation: factor_label
      value_param: weight
      input_unit: kg
      chain:
        - num_value: 5.00            # placeholder; engine reads rate from chain via custom mechanism
          num_unit: mg
          den_value: 1
          den_unit: kg
          sig_figs: 3
      target_unit: mg
    explanation_template: |
      "kg" cancels via the dosage factor. {limitingSigFigs} sig figs yield \({finalResult}\,\text{mg}\).
```

**Note on this spec:** the dosage factor's `num_value` is currently hard-coded at `5.00` (not parametric on the `rate` variable). To make it parametric on `rate`, we'd need either (a) a YAML feature where chain values can reference variable names, or (b) two separate variables and a custom multiply path. Both add complexity; for the pilot, a simpler approach is to fix the rate at `5.00` (the textbook value) and only vary `weight`. So:

**Step 2 (revised): Append this simpler version**:

```yaml
  - id: "2.9.dosage"
    match_text: "5.00 mg per kg of body mass"
    question: "A drug is dosed at 5.00 mg per kg of body mass. What dose is needed for a {weight} kg adult?"
    variables:
      weight: { range: [40.0, 100.0], sig_figs: 3 }
    answer:
      operation: factor_label
      value_param: weight
      input_unit: kg
      chain:
        - num_value: 5.00
          num_unit: mg
          den_value: 1
          den_unit: kg
          sig_figs: 3
      target_unit: mg
    explanation_template: |
      "kg" cancels via the 5.00 mg/kg dosage factor. {limitingSigFigs} sig figs from
      "{weight} kg" yield \({finalResult}\,\text{mg}\).
```

(Only `weight` varies; `rate` stays at 5.00 mg/kg per the textbook problem.)

- [ ] **Step 3: Validate, fuzz, build, verify**

Same as before. Expected: 4 problems pass.

- [ ] **Step 4: Commit**

```bash
git add .firecrawl/interactive_specs/chapter_02.yaml HTML_Files/interactive/Chapter_02.html
git commit -m "Pilot problem 4: variable dosage equivalence (§2.9)"
```

---

### Task C5: Pilot problem 5 — mass percent (g alloy → g Ag)

**Files:**
- Modify: `.firecrawl/interactive_specs/chapter_02.yaml`

- [ ] **Step 1: Verify match_text**

Run: `grep -c 'alloy is 35.0% silver' HTML_Files/Chapter_02.html`
Expected: `1`.

- [ ] **Step 2: Append spec entry**:

```yaml
  - id: "2.9.alloy_mass_percent"
    match_text: "alloy is 35.0% silver"
    question: "An alloy is {pct}% silver. How much silver is in {mass} g of alloy?"
    variables:
      pct: { range: [10.0, 80.0], sig_figs: 3 }
      mass: { range: [10.0, 100.0], sig_figs: 3 }
    answer:
      operation: factor_label
      value_param: mass
      input_unit: g alloy
      chain:
        - num_value: 35.0          # static placeholder; see note below
          num_unit: g Ag
          den_value: 100
          den_unit: g alloy
          sig_figs: 3
      target_unit: g Ag
    constraints:
      avoid_round: [0, 100]
    explanation_template: |
      "g alloy" cancels via the {pct}% mass-percent factor. {limitingSigFigs} sig figs
      from "{mass} g alloy" yield \({finalResult}\,\text{g Ag}\).
```

**Note:** Same parametric-chain limitation as Task C4. For the pilot, fix the percentage at 35.0 (textbook value). Variable mass alone gives meaningful retry coverage:

**Step 2 (revised): Append this simpler version**:

```yaml
  - id: "2.9.alloy_mass_percent"
    match_text: "alloy is 35.0% silver"
    question: "An alloy is 35.0% silver. How much silver is in {mass} g of alloy?"
    variables:
      mass: { range: [10.0, 100.0], sig_figs: 3 }
    answer:
      operation: factor_label
      value_param: mass
      input_unit: g alloy
      chain:
        - num_value: 35.0
          num_unit: g Ag
          den_value: 100
          den_unit: g alloy
          sig_figs: 3
      target_unit: g Ag
    explanation_template: |
      "g alloy" cancels via the 35.0% mass-percent factor.
      {limitingSigFigs} sig figs from "{mass} g alloy" yield \({finalResult}\,\text{g Ag}\).
```

- [ ] **Step 3: Validate, fuzz, build, verify**

Same. Expected: 5 problems pass.

- [ ] **Step 4: Commit**

```bash
git add .firecrawl/interactive_specs/chapter_02.yaml HTML_Files/interactive/Chapter_02.html
git commit -m "Pilot problem 5: variable mass percent — alloy silver (§2.9)"
```

---

### Task C6: Pilot problem 6 — two-step cost chain (mi → gal → $)

**Files:**
- Modify: `.firecrawl/interactive_specs/chapter_02.yaml`

- [ ] **Step 1: Verify match_text**

Run: `grep -c 'car gets 32.0 mi/gal' HTML_Files/Chapter_02.html`
Expected: `1`.

- [ ] **Step 2: Append spec entry**:

```yaml
  - id: "2.9.cost_chain"
    match_text: "car gets 32.0 mi/gal"
    question: "A car gets 32.0 mi/gal and the gas is $3.99/gal. What does it cost to drive {distance} mi?"
    variables:
      distance: { range: [50, 500], sig_figs: 3 }
    answer:
      operation: factor_label
      value_param: distance
      input_unit: mi
      chain:
        - num_value: 1
          num_unit: gal
          den_value: 32.0
          den_unit: mi
          sig_figs: 3
        - num_value: 3.99
          num_unit: dollar
          den_value: 1
          den_unit: gal
          sig_figs: 3
      target_unit: dollar
    explanation_template: |
      "mi" cancels in step 1; "gal" cancels in step 2. {limitingSigFigs} sig figs
      from "{distance} mi" yield \(\${finalResult}\) (rendered as $).
```

**Note on the dollar-sign LaTeX:** `\$` is the canonical MathJax escape for a literal $. In the explanation template above, `\(\${finalResult}\)` produces an inline-math block with a literal `$` followed by the number. Browser display: `$43.6`.

The `target_unit` is `dollar` (the unit name in the chain math). The displayed answer uses the `$` symbol via the explanation template; the engine's auto-LaTeX rendering produces `\text{dollar}` which is acceptable for a single problem.

- [ ] **Step 3: Validate, fuzz, build, verify**

Same. Expected: 6 problems pass.

- [ ] **Step 4: Manual smoke test**

Open `HTML_Files/interactive/Chapter_02.html` in a browser via the local server (or visit Pages after deploy). Click "Try a different version" 3× on each of the 6 problems. Verify:
- Question stem updates with new value
- Pill closes on click
- Reopening the pill shows the recomputed factor-label chain with `\cancel{}` typeset by MathJax
- Browser console has no errors

- [ ] **Step 5: Commit**

```bash
git add .firecrawl/interactive_specs/chapter_02.yaml HTML_Files/interactive/Chapter_02.html
git commit -m "Pilot problem 6: variable two-step cost chain (§2.9)"
```

---

## Phase D — Final regression check

### Task D1: Verify acceptance criteria

**Files:** None — verification only.

- [ ] **Step 1: All tests pass**

```bash
cd .firecrawl/interactive_engine && node --test engine.test.js
cd ../.. && python .firecrawl/test_build_interactive.py
```
Expected: 50/50 engine tests; 14/14 Python tests.

- [ ] **Step 2: All chapters validate and fuzz**

```bash
python .firecrawl/build_interactive.py --validate
python .firecrawl/build_interactive.py --fuzz 1000
```
Expected:
- `--validate` ends with "VALIDATE OK: 12 problems across 2 chapter(s)."
- `--fuzz` produces 12 lines of "FUZZ OK: ..." (6 for chapter 01, 6 for chapter 02).

- [ ] **Step 3: HTML output present**

```bash
ls HTML_Files/interactive/Chapter_01.html HTML_Files/interactive/Chapter_02.html
ls HTML_Files/interactive/assets/engine.js HTML_Files/interactive/assets/engine.css
grep -c 'data-variant-spec=' HTML_Files/interactive/Chapter_02.html
```
Expected:
- Both chapters' HTML files exist; assets exist.
- grep returns 6 (or higher if attributes share lines — use `grep -o ... | wc -l` to confirm 6 distinct attrs).

- [ ] **Step 4: Canonical files byte-identical**

```bash
git diff main -- HTML_Files/Chapter_01.html HTML_Files/Chapter_02.html
git diff main -- '*.docx'
```
Expected: empty output (no canonical regression).

- [ ] **Step 5: Phase 1 Ch 1 still works**

Open `HTML_Files/interactive/Chapter_01.html` in the browser via the local server. Click each Phase 1 button; verify all six Ch 1 problems still cycle variants correctly with no console errors.

- [ ] **Step 6: Final commit (or note completion)**

If everything is green, no final commit is needed (Phase D is verification only). If any documentation update is helpful, add it; otherwise:

```bash
git commit --allow-empty -m "Mark Phase 2 (Ch 2 dimensional analysis) pilot complete"
```

---

## Self-Review Notes

Verified during plan-writing:

- **Spec coverage:** Every section of the design spec maps to one or more tasks:
  - Spec §3 (architecture additions) → Tasks A1–A3 (engine), B1–B4 (build script).
  - Spec §4 (engine primitives) → Tasks A1, A2.
  - Spec §5 (YAML schema) → applied per-problem in Tasks C1–C6.
  - Spec §6 (multi-chapter build) → Tasks B1–B4.
  - Spec §7 (six pilot problems) → Tasks C1–C6.
  - Spec §10 (acceptance criteria) → Task D1.
  - Spec §11 (open questions) → resolved in plan header.

- **Function-name consistency:** `factorLabelChain` and `renderFactorLabelLatex` referenced consistently across Tasks A1, A2, A3, and the explanation tokens (`finalResult`, `finalUnit`, `limitingSigFigs`) are used identically in tests, implementation, and YAML explanation templates.

- **YAML field consistency:** `num_value`, `num_unit`, `den_value`, `den_unit`, `exact`, `sig_figs`, `value_param`, `input_unit`, `target_unit` — all snake_case throughout, matching Phase 1's existing conventions.

- **Test counts:** Phase 1 ended with 35 engine + 8 Python = 43 tests. Phase 2 adds (8 + 4 + 3) = 15 engine and (3 + 3) = 6 Python = 21 new tests. Final: 50 engine + 14 Python = 64 tests. The plan asserts these counts at each task boundary.

- **Commit hygiene:** Every commit message is single-line ≤ 70 chars (one or two have a body). No `Co-Authored-By: Claude` trailer per CLAUDE.md.

- **No `TBD`/`TODO`/placeholder strings.** Every code block contains complete, runnable code.

- **One known parametric-chain limitation** (acknowledged inline in Tasks C4 and C5): the YAML spec's chain values are static literals, so problems whose conversion factor varies with another variable (e.g., dosage rate, alloy percentage) currently fix that factor. Two simpler workarounds applied in the pilot — vary only the input value, not the factor. A "parametric chain" YAML feature is recorded as Phase 3+ in the spec's open follow-ups.
