# Variable-Problem Pilot — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add interactive, re-randomizable practice problems to Chapter 1's HTML build so students can attempt the same problem repeatedly with fresh sampled values, while leaving the canonical static build, the Word source files, and the Canvas/IMSCC pipeline untouched.

**Architecture:** A new parallel build script (`build_interactive.py`) postprocesses `HTML_Files/Chapter_01.html` (the existing static output), wraps selected problems with variant metadata, and copies a hand-written ES-module engine (`engine.js`) into the output directory. The engine boots in the browser, samples parameter values within author-declared ranges with four guardrails, recomputes the answer with sig-fig-correct arithmetic, re-renders the LaTeX solution chain, and re-typesets via MathJax 3's partial-typeset API. Output is a parallel directory `HTML_Files_Interactive/` deployed to a subdirectory of the existing GitHub Pages site.

**Tech Stack:**
- **Engine (browser + Node test runtime):** Vanilla ES-module JavaScript, no dependencies, ~30 KB target. Tested with Node 24's built-in `node:test` runner.
- **Build script (Python):** `build_interactive.py` using `PyYAML`, `beautifulsoup4` (already a project dependency for `build_html.py`). Tested with built-in `unittest`.
- **Browser:** MathJax 3 with the `cancel` extension (already configured by `build_html.py`).
- **CI:** GitHub Actions workflow extension to `.github/workflows/pages.yml`.
- **Source spec:** `docs/superpowers/specs/2026-05-05-variable-problems-pilot-design.md` (committed `d16c517`).

**Repo conventions:** Per `CLAUDE.md`, no `Co-Authored-By: Claude` trailer on commits.

---

## Decided Open Questions

These were flagged "to settle in implementation plan" in the spec (§11). Locking in here:

| # | Question | Decision |
|---|---|---|
| 1 | Anchor matching strategy | YAML spec entries declare a `match_text` field — a unique substring of the problem stem. Build script locates the matching `<div class="problem-stem">` by text content, adds a `data-variant-spec="<id>"` attribute, and wraps with the engine's bootstrap hook. **No changes to `build_html.py`.** |
| 2 | Tracking decisions | Track `.firecrawl/build_interactive.py`, `.firecrawl/interactive_engine/`, `.firecrawl/interactive_specs/`, and `HTML_Files_Interactive/` (the latter analogous to the tracked `HTML_Files/` snapshot). |
| 3 | Sig-fig parsing/formatting | Hand-roll. Zero dependencies. Engine bundle stays under 30 KB. |
| 4 | CI workflow extension | Add steps to the existing `build` job in `pages.yml` (single deploy artefact). |
| 5 | MathJax partial typeset | Confirmed available; engine awaits `MathJax.startup.promise` then calls `MathJax.typesetPromise([containerEl])`. |
| 6 | Specific source problems | Selected during Phase E by reading `Chapter_01.docx`'s "Practice Problems by Topic" / "Additional Practice Problems by Topic" sections. |

---

## File Structure

**New files (all tracked):**

```
.firecrawl/
    build_interactive.py                            # CLI build script
    test_build_interactive.py                       # Python unittest tests
    interactive_engine/
        engine.js                                   # ES module — pure functions + bootstrap
        engine.css                                  # button + fade-transition styles
        engine.test.js                              # node:test unit tests for pure functions
        package.json                                # declares "type": "module" so Node treats .js as ESM
    interactive_specs/
        chapter_01.yaml                             # author-written spec (6 problems)
        chapter_01_problems/                        # escape-hatch JS modules (likely empty for pilot)

HTML_Files_Interactive/                             # build output (committed)
    Chapter_01.html
    assets/
        engine.js                                   # copied verbatim from .firecrawl/interactive_engine/
        engine.css

docs/superpowers/
    specs/2026-05-05-variable-problems-pilot-design.md   # ALREADY EXISTS (commit d16c517)
    plans/2026-05-05-variable-problems-pilot.md          # THIS FILE

.github/workflows/pages.yml                         # extended (single new step)
```

**Files NOT modified by this plan:**

- Any `.docx` chapter source.
- `.firecrawl/build_html.py`.
- `HTML_Files/*.html` (canonical static output — verified byte-identical after the pilot).
- `build_canvas.py`, `build_imscc.py` (not present on this workspace anyway).
- All other top-level files.

---

## Engine API (defined upfront for cross-task consistency)

These names and signatures appear across multiple tasks — defined once here so later tasks reference them consistently.

**Pure functions (exported from `engine.js`):**

```js
export function countSigFigs(numericString) → { count: number, ruleExplanation: string }
export function formatWithSigFigs(value, n) → string
export function decimalToSciNotation(value, sigFigs) → { coefficient: string, exponent: number, latex: string }
export function sciNotationToDecimal({ coefficient, exponent }) → string
export function addPreservingDecimalPlaces(values) → { rawSum: string, finalSum: string, limitingDecimalPlaces: number, limitingValue: string }
export function multiplyPreservingSigFigs(values) → { rawProduct: string, finalProduct: string, limitingSigFigs: number, limitingValue: string }
export function evaluateLinearFunction({ slope, intercept, x }) → { y: string, latex: string }
```

**Sampling functions (exported):**

```js
export function sampleValue(spec, rng) → string                         // single uniform sample, formatted to declared precision
export function generateVariant(problemSpec, rng) → object              // full variant with guardrail retries; throws on cap
```

**Bootstrap (called automatically on DOMContentLoaded if `document` is defined):**

```js
export function bootstrap() → void                                      // finds [data-variant-spec], wires buttons, initial render
```

**Internal helpers (not exported, but defined for clarity):**

```js
function renderQuestion(spec, params) → string                          // HTML string for problem stem
function renderSolution(spec, params) → { latex: string, explanation: string }
function renderLatexForOperation(operation, computed) → string          // delegates per operation type
```

---

## Spec File Schema (YAML)

`chapter_01.yaml` follows this schema. Build script enforces it.

```yaml
problems:
  - id: <slug>                       # required: human-readable, used in console messages
    match_text: <substring>          # required: unique substring of problem-stem text in HTML
    question: <template>             # required: prose with {var} placeholders
    variables:
      <name>:                        # one entry per variable
        # exactly one of:
        range: [<low>, <high>]
        decimal_places: <int>        # OR sig_figs: <int>
        # OR for sig-fig-counting questions:
        generator: random_decimal_with_features
        sig_figs: [<int>, ...]       # rotates among these
        patterns: [<pattern>, ...]   # rotates among these
        # OR for scientific notation:
        coefficient: { range: [<low>, <high>], sig_figs: <int> }
        exponent: { range: [<int>, <int>] }
    answer:
      operation: <op>                # one of: subtract, add, multiply, count_sig_figs, to_sci_notation, sci_notation_arithmetic, linear_function
      unit: <string>                 # optional, appended to rendered answer
    constraints:                     # optional
      result_range: [<low>, <high>]
      result_must_be_positive: <bool>
      avoid_round: [<value>, ...]
    explanation_template: <template> # required: solution paragraph with {token} substitutions
    custom_js: <filename>            # optional escape hatch — overrides everything above
```

---

# Tasks

## Phase A — Setup and scaffolding

### Task A1: Create directory structure and Node module config

**Files:**
- Create: `.firecrawl/interactive_engine/package.json`
- Create: `.firecrawl/interactive_engine/engine.js` (empty placeholder)
- Create: `.firecrawl/interactive_engine/engine.test.js` (empty placeholder)
- Create: `.firecrawl/interactive_engine/engine.css` (empty placeholder)
- Create: `.firecrawl/interactive_specs/chapter_01.yaml` (placeholder with empty `problems: []`)
- Create: `.firecrawl/interactive_specs/chapter_01_problems/.gitkeep`

- [ ] **Step 1: Create `.firecrawl/interactive_engine/package.json`**

```json
{
  "name": "interactive-engine",
  "version": "0.1.0",
  "type": "module",
  "private": true,
  "description": "Hand-rolled ES-module engine for variable-problem pilot. No runtime deps.",
  "scripts": {
    "test": "node --test engine.test.js"
  }
}
```

- [ ] **Step 2: Create empty placeholder files**

```bash
touch .firecrawl/interactive_engine/engine.js
touch .firecrawl/interactive_engine/engine.test.js
touch .firecrawl/interactive_engine/engine.css
mkdir -p .firecrawl/interactive_specs/chapter_01_problems
touch .firecrawl/interactive_specs/chapter_01_problems/.gitkeep
```

- [ ] **Step 3: Create `.firecrawl/interactive_specs/chapter_01.yaml` with an empty problem list**

```yaml
# Variable-problem specs for Chapter 1.
# Schema reference: docs/superpowers/plans/2026-05-05-variable-problems-pilot.md
problems: []
```

- [ ] **Step 4: Verify Node and Python tooling**

Run: `node --version` (expect `v20+` or `v24+`).
Run: `python --version` (expect `3.11+`).
Run: `python -c "import yaml, bs4"` (expect no error). If `yaml` import fails, run `pip install pyyaml`.

- [ ] **Step 5: Commit**

```bash
git add .firecrawl/interactive_engine/ .firecrawl/interactive_specs/
git commit -m "Scaffold interactive engine + spec dirs for Ch 1 pilot"
```

---

## Phase B — Engine pure functions (TDD)

Each function in this phase follows the same TDD cycle: write failing test → confirm fail → implement → confirm pass → commit. No DOM, no MathJax — these are pure deterministic functions.

### Task B1: `countSigFigs(numericString)` — counts sig figs and explains rules

**Files:**
- Modify: `.firecrawl/interactive_engine/engine.test.js`
- Modify: `.firecrawl/interactive_engine/engine.js`

**Sig-fig rules implemented:**
- Rule 1: All non-zero digits are significant.
- Rule 2: Captive zeros (between non-zero digits) are significant.
- Rule 3: Leading zeros are NOT significant.
- Rule 4a: Trailing zeros after a decimal point ARE significant.
- Rule 4b: Trailing zeros without a decimal point are AMBIGUOUS (return as ambiguous case).
- Rule 5: Scientific notation — all digits in the coefficient count.

- [ ] **Step 1: Write failing tests**

Add to `.firecrawl/interactive_engine/engine.test.js`:

```js
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { countSigFigs } from './engine.js';

test('countSigFigs: simple integer', () => {
  const r = countSigFigs('305.20');
  assert.equal(r.count, 5);
  assert.match(r.ruleExplanation, /trailing zero/i);
});

test('countSigFigs: leading zeros excluded', () => {
  assert.equal(countSigFigs('0.0030').count, 2);
});

test('countSigFigs: captive zeros included', () => {
  assert.equal(countSigFigs('4002').count, 4);
});

test('countSigFigs: scientific notation', () => {
  assert.equal(countSigFigs('7.000e6').count, 4);
  assert.equal(countSigFigs('1.20e3').count, 3);
});

test('countSigFigs: ambiguous trailing zeros without decimal', () => {
  const r = countSigFigs('600');
  assert.equal(r.ambiguous, true);
  assert.match(r.ruleExplanation, /ambiguous/i);
});

test('countSigFigs: 100. with decimal point', () => {
  assert.equal(countSigFigs('100.').count, 3);
});

test('countSigFigs: 0.020080', () => {
  assert.equal(countSigFigs('0.020080').count, 5);
});
```

- [ ] **Step 2: Run tests, confirm they fail**

Run: `cd .firecrawl/interactive_engine && node --test engine.test.js`
Expected: All tests fail with `SyntaxError` (no export of `countSigFigs`) or `TypeError`.

- [ ] **Step 3: Implement `countSigFigs` in `engine.js`**

```js
// engine.js — variable-problem pilot engine
// ES module. Runs in modern browsers and Node 20+.

/**
 * Count significant figures in a numeric string.
 * Returns { count, ruleExplanation, ambiguous? }.
 */
export function countSigFigs(s) {
  const trimmed = String(s).trim();

  // Scientific notation: 7.000e6 — count digits in coefficient.
  const sciMatch = trimmed.match(/^([+-]?\d+(?:\.\d+)?)[eE]([+-]?\d+)$/);
  if (sciMatch) {
    const coeff = sciMatch[1].replace(/^[+-]/, '');
    const digits = coeff.replace('.', '');
    // Leading zeros in the coefficient still don't count
    const significant = digits.replace(/^0+/, '') || '0';
    return {
      count: significant.length,
      ruleExplanation: 'Scientific notation: all digits in the coefficient are significant.',
    };
  }

  const negStripped = trimmed.replace(/^[+-]/, '');
  const hasDecimal = negStripped.includes('.');

  if (!hasDecimal) {
    // No decimal point — trailing zeros ambiguous.
    const stripped = negStripped.replace(/^0+/, '');
    if (stripped === '') return { count: 1, ruleExplanation: 'Zero by itself is one sig fig.' };
    if (/0+$/.test(stripped)) {
      return {
        count: stripped.replace(/0+$/, '').length,
        ambiguous: true,
        ruleExplanation: 'Trailing zeros without a decimal point are ambiguous (1 to ' + stripped.length + ' sig figs). Express as scientific notation to disambiguate.',
      };
    }
    return { count: stripped.length, ruleExplanation: 'All digits are non-zero or captive zeros.' };
  }

  // Has decimal point.
  const [intPart, decPart] = negStripped.split('.');
  const intStripped = intPart.replace(/^0+/, '');
  if (intStripped === '') {
    // 0.xxx — leading zeros in decimal part don't count
    const decStripped = decPart.replace(/^0+/, '');
    return {
      count: decStripped.length,
      ruleExplanation: 'Leading zeros do not count; remaining digits (including trailing zeros after the decimal point) all count.',
    };
  }
  // Has integer part — all digits after the leading zeros count, including trailing.
  return {
    count: (intStripped + decPart).length,
    ruleExplanation: 'Captive zeros count; trailing zeros after the decimal point count.',
  };
}
```

- [ ] **Step 4: Run tests, confirm they pass**

Run: `cd .firecrawl/interactive_engine && node --test engine.test.js`
Expected: All 7 tests pass.

- [ ] **Step 5: Commit**

```bash
git add .firecrawl/interactive_engine/engine.js .firecrawl/interactive_engine/engine.test.js
git commit -m "Add countSigFigs() engine primitive with tests"
```

---

### Task B2: `formatWithSigFigs(value, n)` — round to N sig figs

**Files:**
- Modify: `.firecrawl/interactive_engine/engine.test.js`
- Modify: `.firecrawl/interactive_engine/engine.js`

- [ ] **Step 1: Write failing tests**

Append to `engine.test.js`:

```js
import { formatWithSigFigs } from './engine.js';

test('formatWithSigFigs: round to 3 sig figs', () => {
  assert.equal(formatWithSigFigs(12.3456, 3), '12.3');
  assert.equal(formatWithSigFigs(0.012345, 3), '0.0123');
  assert.equal(formatWithSigFigs(123456, 3), '123000');
});

test('formatWithSigFigs: preserves trailing zeros', () => {
  assert.equal(formatWithSigFigs(2.5, 3), '2.50');
  assert.equal(formatWithSigFigs(40.7, 4), '40.70');
});

test('formatWithSigFigs: handles negative', () => {
  assert.equal(formatWithSigFigs(-12.34, 3), '-12.3');
});

test('formatWithSigFigs: integer with N=2 from N=4', () => {
  assert.equal(formatWithSigFigs(1234, 2), '1200');
});
```

- [ ] **Step 2: Run, confirm fail**

Run: `node --test engine.test.js`
Expected: 4 new tests fail (`formatWithSigFigs is not a function`).

- [ ] **Step 3: Implement**

Append to `engine.js`:

```js
/**
 * Format a number to exactly N significant figures.
 * Preserves trailing zeros (e.g., formatWithSigFigs(2.5, 3) → "2.50").
 */
export function formatWithSigFigs(value, n) {
  if (value === 0) return n === 1 ? '0' : '0.' + '0'.repeat(n - 1);
  const sign = value < 0 ? '-' : '';
  const abs = Math.abs(value);
  const magnitude = Math.floor(Math.log10(abs));
  const factor = Math.pow(10, n - 1 - magnitude);
  const rounded = Math.round(abs * factor) / factor;
  // Determine decimals to keep
  const decimals = Math.max(0, n - 1 - magnitude);
  if (decimals === 0) {
    // Integer-style — may need trailing zeros via scaling
    return sign + Math.round(rounded).toString();
  }
  return sign + rounded.toFixed(decimals);
}
```

- [ ] **Step 4: Run, confirm pass**

Run: `node --test engine.test.js`
Expected: All tests pass (countSigFigs's 7 + formatWithSigFigs's 4 = 11).

- [ ] **Step 5: Commit**

```bash
git add .firecrawl/interactive_engine/engine.js .firecrawl/interactive_engine/engine.test.js
git commit -m "Add formatWithSigFigs() engine primitive with tests"
```

---

### Task B3: `decimalToSciNotation(value, sigFigs)`

**Files:**
- Modify: `.firecrawl/interactive_engine/engine.test.js`
- Modify: `.firecrawl/interactive_engine/engine.js`

- [ ] **Step 1: Write failing tests**

Append:

```js
import { decimalToSciNotation } from './engine.js';

test('decimalToSciNotation: positive small', () => {
  const r = decimalToSciNotation(0.00038, 2);
  assert.equal(r.coefficient, '3.8');
  assert.equal(r.exponent, -4);
  assert.equal(r.latex, '3.8 \\times 10^{-4}');
});

test('decimalToSciNotation: large with 3 sig figs', () => {
  const r = decimalToSciNotation(420000, 3);
  assert.equal(r.coefficient, '4.20');
  assert.equal(r.exponent, 5);
});

test('decimalToSciNotation: between 1 and 10', () => {
  const r = decimalToSciNotation(4.56, 3);
  assert.equal(r.coefficient, '4.56');
  assert.equal(r.exponent, 0);
});
```

- [ ] **Step 2: Run, confirm fail**

Run: `node --test engine.test.js`

- [ ] **Step 3: Implement**

```js
/**
 * Convert a decimal value to scientific notation form.
 */
export function decimalToSciNotation(value, sigFigs) {
  if (value === 0) return { coefficient: '0', exponent: 0, latex: '0' };
  const sign = value < 0 ? '-' : '';
  const abs = Math.abs(value);
  const exponent = Math.floor(Math.log10(abs));
  const coefficientNum = abs / Math.pow(10, exponent);
  const coefficient = formatWithSigFigs(coefficientNum, sigFigs);
  const latex = sign + coefficient + ' \\times 10^{' + exponent + '}';
  return { coefficient: sign + coefficient, exponent, latex };
}
```

- [ ] **Step 4: Run, confirm pass**

Run: `node --test engine.test.js`

- [ ] **Step 5: Commit**

```bash
git add .firecrawl/interactive_engine/engine.js .firecrawl/interactive_engine/engine.test.js
git commit -m "Add decimalToSciNotation() engine primitive with tests"
```

---

### Task B4: `sciNotationToDecimal({ coefficient, exponent })`

**Files:**
- Modify: `.firecrawl/interactive_engine/engine.test.js`
- Modify: `.firecrawl/interactive_engine/engine.js`

- [ ] **Step 1: Write failing tests**

Append:

```js
import { sciNotationToDecimal } from './engine.js';

test('sciNotationToDecimal: positive integer exponent', () => {
  assert.equal(sciNotationToDecimal({ coefficient: '9.20', exponent: 5 }), '920000');
});

test('sciNotationToDecimal: negative exponent', () => {
  assert.equal(sciNotationToDecimal({ coefficient: '4.56', exponent: -5 }), '0.0000456');
});

test('sciNotationToDecimal: small positive exponent preserves trailing zeros', () => {
  assert.equal(sciNotationToDecimal({ coefficient: '4.20', exponent: 2 }), '420');
});
```

- [ ] **Step 2: Run, confirm fail**

Run: `node --test engine.test.js`

- [ ] **Step 3: Implement**

```js
/**
 * Convert {coefficient, exponent} back to decimal form.
 * Preserves trailing-zero significance.
 */
export function sciNotationToDecimal({ coefficient, exponent }) {
  const sign = coefficient.startsWith('-') ? '-' : '';
  const absCoeff = coefficient.replace(/^[+-]/, '');
  const [intPart, decPart = ''] = absCoeff.split('.');
  const allDigits = intPart + decPart;
  const decimalPos = intPart.length + exponent;

  if (decimalPos >= allDigits.length) {
    // Pad with zeros on the right
    return sign + allDigits + '0'.repeat(decimalPos - allDigits.length);
  } else if (decimalPos <= 0) {
    // Pad with zeros on the left after "0."
    return sign + '0.' + '0'.repeat(-decimalPos) + allDigits;
  } else {
    return sign + allDigits.slice(0, decimalPos) + '.' + allDigits.slice(decimalPos);
  }
}
```

- [ ] **Step 4: Run, confirm pass**

Run: `node --test engine.test.js`

- [ ] **Step 5: Commit**

```bash
git add .firecrawl/interactive_engine/engine.js .firecrawl/interactive_engine/engine.test.js
git commit -m "Add sciNotationToDecimal() engine primitive with tests"
```

---

### Task B5: `addPreservingDecimalPlaces(values)`

**Files:**
- Modify: `.firecrawl/interactive_engine/engine.test.js`
- Modify: `.firecrawl/interactive_engine/engine.js`

Returns `{ rawSum, finalSum, limitingDecimalPlaces, limitingValue }` — applies the addition/subtraction sig-fig rule (round to least decimal places).

- [ ] **Step 1: Write failing tests**

Append:

```js
import { addPreservingDecimalPlaces } from './engine.js';

test('addPreservingDecimalPlaces: textbook example', () => {
  const r = addPreservingDecimalPlaces(['2.45', '12.1', '0.378']);
  assert.equal(r.rawSum, '14.928');
  assert.equal(r.finalSum, '14.9');
  assert.equal(r.limitingDecimalPlaces, 1);
  assert.equal(r.limitingValue, '12.1');
});

test('addPreservingDecimalPlaces: subtraction (negative)', () => {
  const r = addPreservingDecimalPlaces(['8.42', '-6.1']);
  assert.equal(r.finalSum, '2.3');
  assert.equal(r.limitingDecimalPlaces, 1);
  assert.equal(r.limitingValue, '-6.1');
});

test('addPreservingDecimalPlaces: integer + decimal', () => {
  const r = addPreservingDecimalPlaces(['100', '0.5']);
  // 100 has 0 decimal places (treating as exact-place)
  assert.equal(r.limitingDecimalPlaces, 0);
});
```

- [ ] **Step 2: Run, confirm fail**

Run: `node --test engine.test.js`

- [ ] **Step 3: Implement**

```js
/**
 * Add a list of numeric strings; round to least decimal places per sig-fig rule.
 */
export function addPreservingDecimalPlaces(values) {
  const decimalPlacesOf = (s) => {
    const stripped = s.replace(/^[+-]/, '');
    if (!stripped.includes('.')) return 0;
    return stripped.split('.')[1].length;
  };
  const places = values.map(decimalPlacesOf);
  const minPlaces = Math.min(...places);
  const limitingIdx = places.indexOf(minPlaces);
  const limitingValue = values[limitingIdx];
  const sumNum = values.reduce((acc, v) => acc + parseFloat(v), 0);
  const maxPlaces = Math.max(...places);
  const rawSum = sumNum.toFixed(maxPlaces);
  const finalSum = sumNum.toFixed(minPlaces);
  return { rawSum, finalSum, limitingDecimalPlaces: minPlaces, limitingValue };
}
```

- [ ] **Step 4: Run, confirm pass**

Run: `node --test engine.test.js`

- [ ] **Step 5: Commit**

```bash
git add .firecrawl/interactive_engine/engine.js .firecrawl/interactive_engine/engine.test.js
git commit -m "Add addPreservingDecimalPlaces() engine primitive with tests"
```

---

### Task B6: `multiplyPreservingSigFigs(values)`

**Files:**
- Modify: `.firecrawl/interactive_engine/engine.test.js`
- Modify: `.firecrawl/interactive_engine/engine.js`

- [ ] **Step 1: Write failing tests**

Append:

```js
import { multiplyPreservingSigFigs } from './engine.js';

test('multiplyPreservingSigFigs: textbook example', () => {
  const r = multiplyPreservingSigFigs(['7.20', '3.0']);
  // 7.20 × 3.0 = 21.6 → limited to 2 sig figs by 3.0 → 22? No — 7.20/3.0 in textbook is division
  // For multiply: 7.20 × 3.0 = 21.6; limit to 2 sig figs → 22
  assert.equal(r.limitingSigFigs, 2);
  assert.equal(r.limitingValue, '3.0');
  // Note: textbook example was 7.50 g ÷ 2.5 mL = 3.0 g/mL; we test * here
});

test('multiplyPreservingSigFigs: three-factor product', () => {
  const r = multiplyPreservingSigFigs(['3.75', '2.0', '4.50']);
  assert.equal(r.limitingSigFigs, 2);
  assert.equal(r.limitingValue, '2.0');
  assert.equal(r.finalProduct, '34');  // 33.75 → 34 with 2 sig figs
});
```

- [ ] **Step 2: Run, confirm fail**

Run: `node --test engine.test.js`

- [ ] **Step 3: Implement**

```js
/**
 * Multiply a list of numeric strings; round to fewest sig figs per sig-fig rule.
 */
export function multiplyPreservingSigFigs(values) {
  const sigFigsOf = (s) => countSigFigs(s).count;
  const sigs = values.map(sigFigsOf);
  const minSigs = Math.min(...sigs);
  const limitingIdx = sigs.indexOf(minSigs);
  const limitingValue = values[limitingIdx];
  const product = values.reduce((acc, v) => acc * parseFloat(v), 1);
  const rawProduct = product.toString();
  const finalProduct = formatWithSigFigs(product, minSigs);
  return { rawProduct, finalProduct, limitingSigFigs: minSigs, limitingValue };
}
```

- [ ] **Step 4: Run, confirm pass**

Run: `node --test engine.test.js`

- [ ] **Step 5: Commit**

```bash
git add .firecrawl/interactive_engine/engine.js .firecrawl/interactive_engine/engine.test.js
git commit -m "Add multiplyPreservingSigFigs() engine primitive with tests"
```

---

### Task B7: `evaluateLinearFunction({ slope, intercept, x })`

**Files:**
- Modify: `.firecrawl/interactive_engine/engine.test.js`
- Modify: `.firecrawl/interactive_engine/engine.js`

- [ ] **Step 1: Write failing tests**

Append:

```js
import { evaluateLinearFunction } from './engine.js';

test('evaluateLinearFunction: textbook example', () => {
  const r = evaluateLinearFunction({ slope: '0.025', intercept: '6.83', x: '50' });
  // 0.025 × 50 + 6.83 = 1.25 + 6.83 = 8.08
  assert.equal(r.y, '8.08');
  assert.match(r.latex, /0\.025/);
  assert.match(r.latex, /6\.83/);
});

test('evaluateLinearFunction: zero intercept', () => {
  const r = evaluateLinearFunction({ slope: '2.0', intercept: '0', x: '5.0' });
  assert.equal(r.y, '10');
});
```

- [ ] **Step 2: Run, confirm fail**

Run: `node --test engine.test.js`

- [ ] **Step 3: Implement**

```js
/**
 * Evaluate y = slope*x + intercept; sig-fig handling: limit by fewest sig figs across slope, intercept, x.
 */
export function evaluateLinearFunction({ slope, intercept, x }) {
  const product = parseFloat(slope) * parseFloat(x);
  const y = product + parseFloat(intercept);
  // Sig figs: addition rule on the product + intercept
  const productResult = multiplyPreservingSigFigs([slope, x]);
  const yResult = addPreservingDecimalPlaces([productResult.finalProduct, intercept]);
  const latex = slope + ' \\times ' + x + ' + ' + intercept + ' = ' + yResult.finalSum;
  return { y: yResult.finalSum, latex };
}
```

- [ ] **Step 4: Run, confirm pass**

Run: `node --test engine.test.js`

- [ ] **Step 5: Commit**

```bash
git add .firecrawl/interactive_engine/engine.js .firecrawl/interactive_engine/engine.test.js
git commit -m "Add evaluateLinearFunction() engine primitive with tests"
```

---

## Phase C — Engine sampling and rendering

### Task C1: Seedable RNG and `sampleValue(spec, rng)`

The engine needs a deterministic RNG for reproducible test runs (`--fuzz 1000` results should be reproducible) and for unit tests.

**Files:**
- Modify: `.firecrawl/interactive_engine/engine.test.js`
- Modify: `.firecrawl/interactive_engine/engine.js`

- [ ] **Step 1: Write failing tests**

Append:

```js
import { mulberry32, sampleValue } from './engine.js';

test('mulberry32: deterministic with seed', () => {
  const a = mulberry32(42);
  const b = mulberry32(42);
  for (let i = 0; i < 100; i++) {
    assert.equal(a(), b());
  }
});

test('sampleValue: range with decimal_places', () => {
  const rng = mulberry32(7);
  const v = sampleValue({ range: [1.0, 100.0], decimal_places: 2 }, rng);
  assert.match(v, /^\d+\.\d{2}$/);
  const num = parseFloat(v);
  assert.ok(num >= 1.0 && num <= 100.0);
});

test('sampleValue: range with sig_figs', () => {
  const rng = mulberry32(7);
  const v = sampleValue({ range: [10, 100], sig_figs: 3 }, rng);
  // Should have exactly 3 sig figs
  assert.match(v, /^\d{3}(?:\.\d+)?$/);
});
```

- [ ] **Step 2: Run, confirm fail**

Run: `node --test engine.test.js`

- [ ] **Step 3: Implement**

```js
/**
 * Tiny seedable RNG (mulberry32). Returns a function () → number in [0, 1).
 */
export function mulberry32(seed) {
  let a = seed | 0;
  return function () {
    a |= 0;
    a = (a + 0x6D2B79F5) | 0;
    let t = Math.imul(a ^ (a >>> 15), 1 | a);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

/**
 * Sample a single variable per its spec. Returns a numeric string formatted to declared precision.
 */
export function sampleValue(spec, rng) {
  if (spec.range) {
    const [low, high] = spec.range;
    const raw = low + rng() * (high - low);
    if (spec.decimal_places !== undefined) return raw.toFixed(spec.decimal_places);
    if (spec.sig_figs !== undefined) return formatWithSigFigs(raw, spec.sig_figs);
    return raw.toString();
  }
  throw new Error('sampleValue: unsupported spec shape: ' + JSON.stringify(spec));
}
```

- [ ] **Step 4: Run, confirm pass**

Run: `node --test engine.test.js`

- [ ] **Step 5: Commit**

```bash
git add .firecrawl/interactive_engine/engine.js .firecrawl/interactive_engine/engine.test.js
git commit -m "Add seedable RNG and sampleValue() to engine"
```

---

### Task C2: `generateVariant(problemSpec, rng)` with guardrails

Implements: parameter sampling for all `variables`, runs the declared `answer.operation` to get the result, applies guardrails (sig-fig validation, magnitude sanity, result-range check, no-degenerate-values), retries up to 50 times, throws if cap hit.

**Files:**
- Modify: `.firecrawl/interactive_engine/engine.test.js`
- Modify: `.firecrawl/interactive_engine/engine.js`

- [ ] **Step 1: Write failing tests**

Append:

```js
import { generateVariant } from './engine.js';

test('generateVariant: subtract operation', () => {
  const spec = {
    id: 'test.subtract',
    variables: {
      a: { range: [5.0, 50.0], decimal_places: 2 },
      b: { range: [1.0, 5.0], decimal_places: 1 },
    },
    answer: { operation: 'subtract', unit: 'm' },
    constraints: { result_must_be_positive: true },
  };
  const rng = mulberry32(123);
  const v = generateVariant(spec, rng);
  assert.ok('a' in v.params);
  assert.ok('b' in v.params);
  assert.ok(parseFloat(v.computed.finalSum) > 0);
});

test('generateVariant: throws on guardrail cap', () => {
  const impossibleSpec = {
    id: 'test.impossible',
    variables: {
      a: { range: [1.0, 1.0], decimal_places: 1 },
    },
    answer: { operation: 'subtract' },
    constraints: { result_range: [100, 200] },  // never satisfiable
  };
  const rng = mulberry32(123);
  assert.throws(() => generateVariant(impossibleSpec, rng), /guardrail/i);
});
```

- [ ] **Step 2: Run, confirm fail**

Run: `node --test engine.test.js`

- [ ] **Step 3: Implement**

```js
const MAX_RETRIES = 50;

/**
 * Sample a full variant for a problem spec, running the declared operation
 * and enforcing guardrails. Throws if cap hit; caller falls back to original.
 */
export function generateVariant(problemSpec, rng) {
  for (let i = 0; i < MAX_RETRIES; i++) {
    const params = {};
    for (const [name, varSpec] of Object.entries(problemSpec.variables || {})) {
      params[name] = sampleValue(varSpec, rng);
    }
    const computed = computeAnswer(problemSpec.answer, params);
    if (passesGuardrails(problemSpec.constraints || {}, params, computed)) {
      return { params, computed };
    }
  }
  throw new Error('Guardrail cap hit (' + MAX_RETRIES + ' retries) for spec: ' + problemSpec.id);
}

function computeAnswer(answerSpec, params) {
  const op = answerSpec.operation;
  const values = Object.values(params);
  switch (op) {
    case 'subtract': {
      const [a, b] = values;
      return addPreservingDecimalPlaces([a, '-' + b.replace(/^[+-]/, '')]);
    }
    case 'add':
      return addPreservingDecimalPlaces(values);
    case 'multiply':
      return multiplyPreservingSigFigs(values);
    case 'count_sig_figs':
      return countSigFigs(values[0]);
    case 'to_sci_notation':
      return decimalToSciNotation(parseFloat(values[0]), countSigFigs(values[0]).count);
    case 'sci_notation_arithmetic':
      return computeSciNotationArith(answerSpec, params);
    case 'linear_function':
      return evaluateLinearFunction(params);
    default:
      throw new Error('Unknown operation: ' + op);
  }
}

function computeSciNotationArith(answerSpec, params) {
  // For Ch 1 pilot: support multiply on (coeff, exp) pairs
  const a = parseFloat(params.a_coefficient) * Math.pow(10, parseInt(params.a_exponent, 10));
  const b = parseFloat(params.b_coefficient) * Math.pow(10, parseInt(params.b_exponent, 10));
  const product = a * b;
  const sigFigs = Math.min(
    countSigFigs(params.a_coefficient).count,
    countSigFigs(params.b_coefficient).count
  );
  return decimalToSciNotation(product, sigFigs);
}

function passesGuardrails(constraints, params, computed) {
  // result_must_be_positive
  if (constraints.result_must_be_positive) {
    const final = parseFloat(computed.finalSum ?? computed.finalProduct ?? computed.y ?? '0');
    if (final <= 0) return false;
  }
  // result_range
  if (constraints.result_range) {
    const [low, high] = constraints.result_range;
    const final = parseFloat(computed.finalSum ?? computed.finalProduct ?? computed.y ?? '0');
    if (final < low || final > high) return false;
  }
  // avoid_round
  if (constraints.avoid_round) {
    for (const value of Object.values(params)) {
      if (constraints.avoid_round.includes(parseFloat(value))) return false;
    }
  }
  return true;
}
```

- [ ] **Step 4: Run, confirm pass**

Run: `node --test engine.test.js`

- [ ] **Step 5: Commit**

```bash
git add .firecrawl/interactive_engine/engine.js .firecrawl/interactive_engine/engine.test.js
git commit -m "Add generateVariant() with guardrail retry loop"
```

---

### Task C3: LaTeX rendering helpers and explanation-template substitution

**Files:**
- Modify: `.firecrawl/interactive_engine/engine.test.js`
- Modify: `.firecrawl/interactive_engine/engine.js`

- [ ] **Step 1: Write failing tests**

Append:

```js
import { renderLatexForOperation, substituteTemplate } from './engine.js';

test('renderLatexForOperation: subtract', () => {
  const latex = renderLatexForOperation('subtract',
    { params: { a: '8.42', b: '6.1' }, computed: { finalSum: '2.3' } },
    { unit: 'm' }
  );
  assert.match(latex, /8\.42/);
  assert.match(latex, /6\.1/);
  assert.match(latex, /2\.3/);
  assert.match(latex, /\\,\\text\{m\}/);
});

test('substituteTemplate: fills tokens', () => {
  const out = substituteTemplate(
    'Sum is {finalSum}; limited by {limitingValue} ({limitingDecimalPlaces} dp).',
    { finalSum: '14.9', limitingValue: '12.1', limitingDecimalPlaces: 1 }
  );
  assert.equal(out, 'Sum is 14.9; limited by 12.1 (1 dp).');
});
```

- [ ] **Step 2: Run, confirm fail**

Run: `node --test engine.test.js`

- [ ] **Step 3: Implement**

```js
/**
 * Substitute {token} placeholders in a string with values from a map.
 */
export function substituteTemplate(template, tokens) {
  return template.replace(/\{(\w+)\}/g, (_, key) => {
    if (key in tokens) return String(tokens[key]);
    return '{' + key + '}';
  });
}

/**
 * Render LaTeX for a given operation type. Returns a LaTeX string for MathJax.
 */
export function renderLatexForOperation(op, variant, answerSpec) {
  const u = answerSpec.unit ? '\\,\\text{' + answerSpec.unit + '}' : '';
  const p = variant.params;
  const c = variant.computed;
  switch (op) {
    case 'subtract':
      return p.a + u + ' - ' + p.b + u + ' = ' + c.finalSum + u;
    case 'add':
      return Object.values(p).join(u + ' + ') + u + ' = ' + c.finalSum + u;
    case 'multiply':
      return Object.values(p).join(u + ' \\times ') + u + ' = ' + c.finalProduct + u;
    case 'count_sig_figs':
      return p[Object.keys(p)[0]];
    case 'to_sci_notation':
      return p[Object.keys(p)[0]] + ' = ' + c.latex;
    case 'sci_notation_arithmetic': {
      const aLatex = p.a_coefficient + ' \\times 10^{' + p.a_exponent + '}';
      const bLatex = p.b_coefficient + ' \\times 10^{' + p.b_exponent + '}';
      return '(' + aLatex + ')(' + bLatex + ') = ' + c.latex;
    }
    case 'linear_function':
      return c.latex + u;
    default:
      throw new Error('renderLatexForOperation: unknown op ' + op);
  }
}
```

- [ ] **Step 4: Run, confirm pass**

Run: `node --test engine.test.js`

- [ ] **Step 5: Commit**

```bash
git add .firecrawl/interactive_engine/engine.js .firecrawl/interactive_engine/engine.test.js
git commit -m "Add LaTeX rendering and template substitution"
```

---

## Phase D — Engine bootstrap and DOM wiring

These tasks involve DOM and MathJax. No TDD — manual smoke test only. Each task ends with a stage commit.

### Task D1: Bootstrap function and button injection

**Files:**
- Modify: `.firecrawl/interactive_engine/engine.js`
- Modify: `.firecrawl/interactive_engine/engine.css`

- [ ] **Step 1: Add `bootstrap()`, `cycleVariant()`, and supporting helpers to `engine.js`**

Append to `engine.js`:

```js
// ---- Browser bootstrap (runs only when DOM is available) ----

const VARIANT_BUTTON_LABEL = 'Try a different version';

/**
 * Find all problems flagged with [data-variant-spec], wire up buttons, render initial variants.
 */
export function bootstrap() {
  const specsEl = document.getElementById('variant-specs');
  if (!specsEl) {
    console.warn('[interactive-engine] No #variant-specs JSON found on page; nothing to do.');
    return;
  }
  let specs;
  try {
    specs = JSON.parse(specsEl.textContent).problems || [];
  } catch (e) {
    console.error('[interactive-engine] Could not parse #variant-specs JSON:', e);
    return;
  }
  // ARIA-live region for variant-change announcements
  ensureAriaLiveRegion();
  for (const spec of specs) {
    const stem = document.querySelector('[data-variant-spec="' + spec.id + '"]');
    if (!stem) {
      console.warn('[interactive-engine] No DOM node for spec ' + spec.id);
      continue;
    }
    wireProblem(stem, spec);
  }
}

function ensureAriaLiveRegion() {
  if (document.getElementById('variant-aria-live')) return;
  const r = document.createElement('div');
  r.id = 'variant-aria-live';
  r.setAttribute('aria-live', 'polite');
  r.setAttribute('aria-atomic', 'true');
  r.style.position = 'absolute';
  r.style.left = '-9999px';
  r.style.width = '1px';
  r.style.height = '1px';
  r.style.overflow = 'hidden';
  document.body.appendChild(r);
}

function announce(msg) {
  const r = document.getElementById('variant-aria-live');
  if (r) r.textContent = msg;
}

function wireProblem(stemEl, spec) {
  const solutionEl = stemEl.nextElementSibling;
  if (!solutionEl || !solutionEl.classList.contains('solution')) {
    console.warn('[interactive-engine] No sibling .solution for spec ' + spec.id);
    return;
  }
  // Insert button between stem and solution
  const btn = document.createElement('button');
  btn.type = 'button';
  btn.className = 'try-variant';
  btn.textContent = VARIANT_BUTTON_LABEL;
  btn.setAttribute('aria-label', VARIANT_BUTTON_LABEL + ' for this problem');
  stemEl.insertAdjacentElement('afterend', btn);

  // Capture original prose for fallback
  const originalStemHTML = stemEl.innerHTML;
  const originalSolutionHTML = solutionEl.innerHTML;

  const state = { rng: mulberry32(Date.now() & 0xffffffff), spec, stemEl, solutionEl, originalStemHTML, originalSolutionHTML };
  cycleVariant(state, /*announceChange=*/ false);
  btn.addEventListener('click', () => cycleVariant(state, /*announceChange=*/ true));
}

function cycleVariant(state, announceChange) {
  let variant;
  try {
    variant = generateVariant(state.spec, state.rng);
  } catch (e) {
    console.warn('[interactive-engine] Falling back to original values for ' + state.spec.id, e);
    state.stemEl.innerHTML = state.originalStemHTML;
    state.solutionEl.innerHTML = state.originalSolutionHTML;
    return;
  }
  // Render question with parameter substitution
  const questionHTML = substituteTemplate(state.spec.question, variant.params);
  state.stemEl.innerHTML = questionHTML;

  // Render solution
  const op = state.spec.answer.operation;
  const latex = renderLatexForOperation(op, variant, state.spec.answer);
  const explanationTokens = { ...variant.params, ...flattenComputed(variant.computed) };
  const explanation = state.spec.explanation_template
    ? substituteTemplate(state.spec.explanation_template, explanationTokens)
    : '';
  state.solutionEl.innerHTML = '<div class="math-chain">\\[' + latex + '\\]</div><p><em>' + explanation + '</em></p>';

  // Close pill if open
  const details = state.solutionEl.closest('details');
  if (details && details.open) details.open = false;

  // MathJax retypeset (if loaded)
  if (typeof MathJax !== 'undefined' && MathJax.startup) {
    MathJax.startup.promise.then(() => {
      return MathJax.typesetPromise([state.solutionEl, state.stemEl]);
    }).catch((e) => console.error('[interactive-engine] MathJax typeset error:', e));
  }

  if (announceChange) announce('Problem updated with new values.');
}

function flattenComputed(computed) {
  // Spread computed result fields as tokens; rename ambiguous keys for templates.
  const out = {};
  for (const [k, v] of Object.entries(computed)) {
    out[k] = v;
  }
  return out;
}

// Auto-bootstrap when running in a browser
if (typeof document !== 'undefined') {
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', bootstrap);
  } else {
    bootstrap();
  }
}
```

- [ ] **Step 2: Add CSS**

Write `.firecrawl/interactive_engine/engine.css`:

```css
/* Variable-problem pilot — engine styles. */

button.try-variant {
  display: inline-block;
  margin: 0.5em 0;
  padding: 0.35em 0.9em;
  font: inherit;
  font-size: 0.95em;
  background: #e8f0fe;
  border: 1px solid #4a72c4;
  border-radius: 4px;
  color: #1a3a78;
  cursor: pointer;
}

button.try-variant:hover {
  background: #d2e1fc;
}

button.try-variant:focus {
  outline: 2px solid #1a3a78;
  outline-offset: 2px;
}

[data-variant-spec] {
  transition: opacity 0.15s ease-in-out;
}

[data-variant-spec].fading {
  opacity: 0.4;
}
```

- [ ] **Step 3: Run engine tests to confirm nothing regressed**

Run: `cd .firecrawl/interactive_engine && node --test engine.test.js`
Expected: All previous tests still pass (the bootstrap branch is gated by `typeof document`, so Node tests don't trigger it).

- [ ] **Step 4: Commit**

```bash
git add .firecrawl/interactive_engine/engine.js .firecrawl/interactive_engine/engine.css
git commit -m "Add engine bootstrap, button wiring, and CSS"
```

---

## Phase E — Build script (`build_interactive.py`)

### Task E1: Build script skeleton with argparse

**Files:**
- Create: `.firecrawl/build_interactive.py`
- Create: `.firecrawl/test_build_interactive.py`

- [ ] **Step 1: Write failing test**

Create `.firecrawl/test_build_interactive.py`:

```python
"""Tests for build_interactive.py."""
import unittest
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / ".firecrawl" / "build_interactive.py"


class TestCli(unittest.TestCase):
    def test_help(self):
        r = subprocess.run(
            [sys.executable, str(SCRIPT), "--help"],
            capture_output=True, text=True, cwd=str(REPO)
        )
        self.assertEqual(r.returncode, 0)
        self.assertIn("--validate", r.stdout)
        self.assertIn("--show-samples", r.stdout)
        self.assertIn("--fuzz", r.stdout)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run, confirm fail**

Run: `python .firecrawl/test_build_interactive.py`
Expected: Failure (script doesn't exist).

- [ ] **Step 3: Create skeleton script**

Write `.firecrawl/build_interactive.py`:

```python
"""Build the interactive variant of HTML_Files/Chapter_01.html.

Reads `interactive_specs/chapter_01.yaml`, postprocesses
`HTML_Files/Chapter_01.html`, copies the engine assets, and writes
`HTML_Files_Interactive/Chapter_01.html`.

Does NOT read or write any .docx file. Does NOT modify HTML_Files/.
"""
from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

import yaml
from bs4 import BeautifulSoup

REPO = Path(__file__).resolve().parents[1]
SPEC_FILE = REPO / ".firecrawl" / "interactive_specs" / "chapter_01.yaml"
ENGINE_DIR = REPO / ".firecrawl" / "interactive_engine"
INPUT_HTML = REPO / "HTML_Files" / "Chapter_01.html"
OUTPUT_DIR = REPO / "HTML_Files_Interactive"
OUTPUT_HTML = OUTPUT_DIR / "Chapter_01.html"
ASSETS_DIR = OUTPUT_DIR / "assets"


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--validate", action="store_true",
                   help="parse and verify spec without writing output")
    p.add_argument("--show-samples", type=int, metavar="N",
                   help="print N sampled variants per problem (does not write output)")
    p.add_argument("--fuzz", type=int, metavar="N",
                   help="generate N variants per problem and assert all pass guardrails")
    args = p.parse_args()

    if args.validate:
        return cmd_validate()
    if args.show_samples is not None:
        return cmd_show_samples(args.show_samples)
    if args.fuzz is not None:
        return cmd_fuzz(args.fuzz)
    return cmd_build()


def cmd_build() -> int:
    raise NotImplementedError("cmd_build will be implemented in task E3")


def cmd_validate() -> int:
    raise NotImplementedError("cmd_validate will be implemented in task E5")


def cmd_show_samples(n: int) -> int:
    raise NotImplementedError("cmd_show_samples will be implemented in task E6")


def cmd_fuzz(n: int) -> int:
    raise NotImplementedError("cmd_fuzz will be implemented in task E7")


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 4: Run test, confirm pass**

Run: `python .firecrawl/test_build_interactive.py`
Expected: PASS (the help text contains the expected flags).

- [ ] **Step 5: Commit**

```bash
git add .firecrawl/build_interactive.py .firecrawl/test_build_interactive.py
git commit -m "Add build_interactive.py CLI skeleton"
```

---

### Task E2: YAML spec loading and schema validation

**Files:**
- Modify: `.firecrawl/build_interactive.py`
- Modify: `.firecrawl/test_build_interactive.py`

- [ ] **Step 1: Write failing tests**

Append to `test_build_interactive.py`:

```python
import tempfile
from pathlib import Path

# Add the script's directory to path so we can import it
sys.path.insert(0, str(REPO / ".firecrawl"))
from build_interactive import load_spec, ValidationError


class TestSpecLoading(unittest.TestCase):
    def write_spec(self, content: str) -> Path:
        f = tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False)
        f.write(content)
        f.close()
        self.addCleanup(lambda: Path(f.name).unlink())
        return Path(f.name)

    def test_loads_valid_spec(self):
        path = self.write_spec("""
problems:
  - id: "test.subtract"
    match_text: "Compute (8.42 m)"
    question: "Compute ({a} m) − ({b} m)"
    variables:
      a: { range: [5.0, 50.0], decimal_places: 2 }
      b: { range: [1.0, 5.0], decimal_places: 1 }
    answer:
      operation: subtract
    explanation_template: "Test."
""")
        spec = load_spec(path)
        self.assertEqual(len(spec["problems"]), 1)
        self.assertEqual(spec["problems"][0]["id"], "test.subtract")

    def test_rejects_missing_id(self):
        path = self.write_spec("""
problems:
  - match_text: "x"
    question: "x"
    answer: { operation: subtract }
    explanation_template: "x"
""")
        with self.assertRaises(ValidationError):
            load_spec(path)

    def test_rejects_unknown_operation(self):
        path = self.write_spec("""
problems:
  - id: "x"
    match_text: "x"
    question: "x"
    answer: { operation: bogus }
    explanation_template: "x"
""")
        with self.assertRaises(ValidationError):
            load_spec(path)
```

- [ ] **Step 2: Run, confirm fail**

Run: `python .firecrawl/test_build_interactive.py`
Expected: ImportError or fail (`load_spec` doesn't exist).

- [ ] **Step 3: Implement spec loading**

Add to `build_interactive.py` (near the top, after imports):

```python
SUPPORTED_OPERATIONS = {
    "subtract", "add", "multiply", "count_sig_figs",
    "to_sci_notation", "sci_notation_arithmetic", "linear_function",
}

REQUIRED_PROBLEM_FIELDS = {"id", "match_text", "question", "answer", "explanation_template"}


class ValidationError(Exception):
    pass


def load_spec(path: Path) -> dict:
    """Parse and validate the YAML spec. Raise ValidationError on schema violations."""
    try:
        with open(path) as f:
            raw = yaml.safe_load(f) or {}
    except yaml.YAMLError as e:
        raise ValidationError(f"YAML parse error in {path}: {e}")
    problems = raw.get("problems") or []
    if not isinstance(problems, list):
        raise ValidationError(f"`problems` must be a list, got {type(problems).__name__}")
    for i, prob in enumerate(problems):
        missing = REQUIRED_PROBLEM_FIELDS - set(prob.keys())
        # custom_js entries skip most schema checks
        if "custom_js" in prob:
            if "id" not in prob or "match_text" not in prob:
                raise ValidationError(f"problems[{i}]: custom_js entries still require id and match_text")
            continue
        if missing:
            raise ValidationError(f"problems[{i}] (id={prob.get('id', '?')}): missing fields: {sorted(missing)}")
        op = prob.get("answer", {}).get("operation")
        if op not in SUPPORTED_OPERATIONS:
            raise ValidationError(
                f"problems[{i}] (id={prob.get('id')}): unsupported operation '{op}'. "
                f"Supported: {sorted(SUPPORTED_OPERATIONS)}"
            )
    return raw
```

- [ ] **Step 4: Run, confirm pass**

Run: `python .firecrawl/test_build_interactive.py`
Expected: All tests pass.

- [ ] **Step 5: Commit**

```bash
git add .firecrawl/build_interactive.py .firecrawl/test_build_interactive.py
git commit -m "Add YAML spec loading with schema validation"
```

---

### Task E3: HTML postprocess — find problem, attach `data-variant-spec`

**Files:**
- Modify: `.firecrawl/build_interactive.py`
- Modify: `.firecrawl/test_build_interactive.py`

- [ ] **Step 1: Write failing tests**

Append to `test_build_interactive.py`:

```python
from build_interactive import attach_variant_attrs


class TestAttachVariantAttrs(unittest.TestCase):
    def test_attaches_attribute_to_matching_stem(self):
        html = '''
        <div class="problem-stem">How many feet are in 12.4 meters?</div>
        <div class="solution">40.7 ft</div>
        <div class="problem-stem">Other problem.</div>
        <div class="solution">x</div>
        '''
        spec = {"problems": [{
            "id": "test.feet",
            "match_text": "How many feet are in 12.4",
            "question": "x", "answer": {"operation": "subtract"},
            "explanation_template": "x", "variables": {},
        }]}
        result_html = attach_variant_attrs(html, spec)
        self.assertIn('data-variant-spec="test.feet"', result_html)
        self.assertIn('How many feet are in 12.4 meters?', result_html)

    def test_raises_when_match_text_not_found(self):
        html = '<div class="problem-stem">Hello</div><div class="solution">x</div>'
        spec = {"problems": [{
            "id": "missing", "match_text": "GoodbyeNotFound",
            "question": "x", "answer": {"operation": "subtract"},
            "explanation_template": "x", "variables": {},
        }]}
        with self.assertRaises(ValidationError):
            attach_variant_attrs(html, spec)

    def test_raises_when_match_text_ambiguous(self):
        html = ('<div class="problem-stem">Convert X</div><div class="solution">x</div>'
                '<div class="problem-stem">Convert X</div><div class="solution">y</div>')
        spec = {"problems": [{
            "id": "ambig", "match_text": "Convert X",
            "question": "x", "answer": {"operation": "subtract"},
            "explanation_template": "x", "variables": {},
        }]}
        with self.assertRaises(ValidationError):
            attach_variant_attrs(html, spec)
```

- [ ] **Step 2: Run, confirm fail**

Run: `python .firecrawl/test_build_interactive.py`

- [ ] **Step 3: Implement**

Add to `build_interactive.py`:

```python
def attach_variant_attrs(html: str, spec: dict) -> str:
    """For each spec problem, find the matching <div class="problem-stem"> by
    text substring and add a data-variant-spec attribute. Raise ValidationError
    if a match_text doesn't resolve to exactly one element.
    """
    soup = BeautifulSoup(html, "html.parser")
    stems = soup.find_all("div", class_="problem-stem")
    for prob in spec.get("problems", []):
        match_text = prob["match_text"]
        matches = [s for s in stems if match_text in s.get_text()]
        if not matches:
            raise ValidationError(
                f"match_text {match_text!r} for spec {prob['id']!r} not found in HTML"
            )
        if len(matches) > 1:
            raise ValidationError(
                f"match_text {match_text!r} for spec {prob['id']!r} matched "
                f"{len(matches)} problem-stem elements; make it unique"
            )
        matches[0]["data-variant-spec"] = prob["id"]
    return str(soup)
```

- [ ] **Step 4: Run, confirm pass**

Run: `python .firecrawl/test_build_interactive.py`

- [ ] **Step 5: Commit**

```bash
git add .firecrawl/build_interactive.py .firecrawl/test_build_interactive.py
git commit -m "Add attach_variant_attrs() problem-matching"
```

---

### Task E4: Inline spec JSON, asset copying, full `cmd_build`

**Files:**
- Modify: `.firecrawl/build_interactive.py`

- [ ] **Step 1: Implement `cmd_build` and `inline_spec_json`**

Add to `build_interactive.py` (replace the `NotImplementedError` body):

```python
def inline_spec_json(html: str, spec: dict) -> str:
    """Insert <script type="application/json" id="variant-specs"> and
    <link>/<script> for engine assets just before </head>."""
    soup = BeautifulSoup(html, "html.parser")
    head = soup.find("head")
    if head is None:
        raise ValidationError("HTML has no <head>")
    # Spec JSON
    json_tag = soup.new_tag("script", id="variant-specs", type="application/json")
    json_tag.string = json.dumps(spec, separators=(",", ":"))
    head.append(json_tag)
    # Engine CSS
    css_tag = soup.new_tag("link", rel="stylesheet", href="assets/engine.css")
    head.append(css_tag)
    # Engine JS (ES module)
    js_tag = soup.new_tag("script", type="module", src="assets/engine.js")
    head.append(js_tag)
    return str(soup)


def cmd_build() -> int:
    spec = load_spec(SPEC_FILE)
    if not INPUT_HTML.exists():
        print(f"ERROR: {INPUT_HTML} not found. Run build_html.py first.", file=sys.stderr)
        return 2
    html = INPUT_HTML.read_text(encoding="utf-8")
    html = attach_variant_attrs(html, spec)
    html = inline_spec_json(html, spec)
    OUTPUT_DIR.mkdir(exist_ok=True)
    ASSETS_DIR.mkdir(exist_ok=True)
    OUTPUT_HTML.write_text(html, encoding="utf-8")
    shutil.copy2(ENGINE_DIR / "engine.js", ASSETS_DIR / "engine.js")
    shutil.copy2(ENGINE_DIR / "engine.css", ASSETS_DIR / "engine.css")
    print(f"Wrote {OUTPUT_HTML} and assets.")
    return 0
```

- [ ] **Step 2: Smoke test the build**

Ensure `.firecrawl/interactive_specs/chapter_01.yaml` still has `problems: []` (from Task A1). Run:

```bash
python .firecrawl/build_interactive.py
```

Expected: `Wrote HTML_Files_Interactive/Chapter_01.html and assets.`

- [ ] **Step 3: Verify output structure**

Run: `ls HTML_Files_Interactive/ HTML_Files_Interactive/assets/`
Expected: `Chapter_01.html` in the top dir; `engine.js` and `engine.css` in `assets/`.

- [ ] **Step 4: Spot-check the output HTML**

Run: `grep -c "variant-specs" HTML_Files_Interactive/Chapter_01.html`
Expected: `1`.

- [ ] **Step 5: Commit**

```bash
git add .firecrawl/build_interactive.py HTML_Files_Interactive/
git commit -m "Add cmd_build: HTML postprocess and asset copy"
```

---

### Task E5: `--validate` flag

**Files:**
- Modify: `.firecrawl/build_interactive.py`
- Modify: `.firecrawl/test_build_interactive.py`

- [ ] **Step 1: Write failing test**

Append:

```python
class TestValidateFlag(unittest.TestCase):
    def test_validate_returns_zero_on_clean_spec(self):
        r = subprocess.run(
            [sys.executable, str(SCRIPT), "--validate"],
            capture_output=True, text=True, cwd=str(REPO)
        )
        self.assertEqual(r.returncode, 0, msg=r.stderr)
```

- [ ] **Step 2: Run, confirm fail**

Run: `python .firecrawl/test_build_interactive.py`
Expected: Failure (`cmd_validate` raises `NotImplementedError`).

- [ ] **Step 3: Implement**

Replace the `cmd_validate` body in `build_interactive.py`:

```python
def cmd_validate() -> int:
    try:
        spec = load_spec(SPEC_FILE)
    except ValidationError as e:
        print(f"VALIDATE FAIL: {e}", file=sys.stderr)
        return 1
    if not INPUT_HTML.exists():
        print(f"VALIDATE FAIL: {INPUT_HTML} not found.", file=sys.stderr)
        return 1
    html = INPUT_HTML.read_text(encoding="utf-8")
    try:
        attach_variant_attrs(html, spec)
    except ValidationError as e:
        print(f"VALIDATE FAIL: {e}", file=sys.stderr)
        return 1
    n = len(spec.get("problems", []))
    print(f"VALIDATE OK: {n} problems, all match_text resolve to unique HTML elements.")
    return 0
```

- [ ] **Step 4: Run, confirm pass**

Run: `python .firecrawl/test_build_interactive.py`

- [ ] **Step 5: Commit**

```bash
git add .firecrawl/build_interactive.py .firecrawl/test_build_interactive.py
git commit -m "Implement --validate flag"
```

---

### Task E6: `--show-samples N` flag (calls Node-side engine)

**Files:**
- Modify: `.firecrawl/build_interactive.py`

The simplest way to call the JS engine from Python: write a tiny Node driver script and `subprocess.run` it.

- [ ] **Step 1: Create `.firecrawl/interactive_engine/sample_driver.js`**

```js
// Driver: read spec JSON from argv[2], emit N variants per problem as JSON.
import { generateVariant, mulberry32 } from './engine.js';
import { readFileSync } from 'node:fs';

const [, , specPath, nStr] = process.argv;
const n = parseInt(nStr, 10);
const spec = JSON.parse(readFileSync(specPath, 'utf-8'));
const out = { samples: [] };
for (const prob of spec.problems || []) {
  const rng = mulberry32(parseInt(prob.id.replace(/\D/g, '') || '1', 10));
  const variants = [];
  let failures = 0;
  for (let i = 0; i < n; i++) {
    try {
      variants.push(generateVariant(prob, rng));
    } catch (e) {
      failures++;
      variants.push({ error: e.message });
    }
  }
  out.samples.push({ id: prob.id, variants, failures });
}
console.log(JSON.stringify(out));
```

- [ ] **Step 2: Implement `cmd_show_samples` in Python**

Replace the body in `build_interactive.py`:

```python
def cmd_show_samples(n: int) -> int:
    spec = load_spec(SPEC_FILE)
    import subprocess as sp
    spec_json = json.dumps(spec)
    spec_tmp = REPO / ".firecrawl" / "interactive_engine" / "_spec_for_driver.json"
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
        print(f"SHOW-SAMPLES FAIL: {r.stderr}", file=sys.stderr)
        return 1
    payload = json.loads(r.stdout)
    for prob in payload["samples"]:
        print(f"\n=== {prob['id']} (failures: {prob['failures']}/{n}) ===")
        for i, v in enumerate(prob["variants"]):
            if "error" in v:
                print(f"  [{i}] ERROR: {v['error']}")
            else:
                params = v.get("params", {})
                computed = v.get("computed", {})
                print(f"  [{i}] params={params}  →  computed={computed}")
    return 0
```

- [ ] **Step 3: Smoke test**

With the spec file still empty (`problems: []`), run:

```bash
python .firecrawl/build_interactive.py --show-samples 3
```

Expected: No output (zero problems iterated). `echo $?` returns 0.

- [ ] **Step 4: Commit**

```bash
git add .firecrawl/build_interactive.py .firecrawl/interactive_engine/sample_driver.js
git commit -m "Implement --show-samples flag with Node driver"
```

---

### Task E7: `--fuzz N` flag

**Files:**
- Modify: `.firecrawl/build_interactive.py`

Reuses the same Node driver from E6; differs in that it asserts zero failures and runs an additional check: every LaTeX string contains the expected `{token}` substitutions (i.e., no unfilled `{...}` placeholders leak through).

- [ ] **Step 1: Implement `cmd_fuzz`**

Replace the body in `build_interactive.py`:

```python
def cmd_fuzz(n: int) -> int:
    spec = load_spec(SPEC_FILE)
    import subprocess as sp
    import re
    spec_json = json.dumps(spec)
    spec_tmp = REPO / ".firecrawl" / "interactive_engine" / "_spec_for_driver.json"
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
        print(f"FUZZ FAIL: {r.stderr}", file=sys.stderr)
        return 1
    payload = json.loads(r.stdout)
    placeholder_re = re.compile(r"\{[a-zA-Z_]\w*\}")
    failed = False
    for prob in payload["samples"]:
        if prob["failures"] > 0:
            print(f"FUZZ FAIL: {prob['id']} had {prob['failures']}/{n} guardrail failures",
                  file=sys.stderr)
            failed = True
            continue
        # Spot-check: pick the first 5 variants, check no unfilled {token}s in the explanation.
        # We need the spec entry for the explanation_template.
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
                print(f"FUZZ FAIL: {prob['id']} variant {i} explanation has unfilled tokens: {leftover}",
                      file=sys.stderr)
                failed = True
        print(f"FUZZ OK: {prob['id']} {n}/{n} variants passed.")
    return 1 if failed else 0
```

- [ ] **Step 2: Smoke test (no problems → trivially passes)**

Run: `python .firecrawl/build_interactive.py --fuzz 100`
Expected: No errors, exit 0.

- [ ] **Step 3: Commit**

```bash
git add .firecrawl/build_interactive.py
git commit -m "Implement --fuzz flag with placeholder leak check"
```

---

## Phase F — Author the 6 Ch 1 problems and verify end-to-end

Each task in this phase: pick the source problem, write the YAML spec entry, run `--validate` and `--show-samples 10`, run `--fuzz 1000`, build, manually smoke-test in browser, commit.

### Task F1: Pilot Problem 1 — Counting sig figs

Source: any of the "How many sig figs in X?" problems in §1.11. Pick one with a stem that's textually unique in the chapter (e.g., "How many sig figs in 0.0030?").

**Files:**
- Modify: `.firecrawl/interactive_specs/chapter_01.yaml`

- [ ] **Step 1: Identify the source problem**

Run:

```bash
grep -nE 'How many sig figs in 0\.0030' HTML_Files/Chapter_01.html
```

Confirm it's present and unique. If not, pick a different stem and adjust `match_text` accordingly.

- [ ] **Step 2: Add the spec entry**

Replace the contents of `.firecrawl/interactive_specs/chapter_01.yaml` with:

```yaml
problems:
  - id: "1.11.counting"
    match_text: "How many sig figs in 0.0030?"
    question: "How many sig figs in {value}?"
    variables:
      value:
        generator: random_decimal_with_features
        sig_figs: [2, 3, 4, 5]
        patterns:
          - leading_zeros
          - captive_zero
          - trailing_zero_with_decimal
          - mixed
    answer:
      operation: count_sig_figs
    explanation_template: |
      {count} sig figs. {ruleExplanation}
```

(*Note:* `random_decimal_with_features` requires a small extension to `sampleValue`. See Step 3.)

- [ ] **Step 3: Extend `sampleValue` to handle the feature-based generator**

In `engine.js`, expand `sampleValue` to recognize `generator: 'random_decimal_with_features'`:

```js
export function sampleValue(spec, rng) {
  if (spec.generator === 'random_decimal_with_features') {
    const sigFigs = spec.sig_figs[Math.floor(rng() * spec.sig_figs.length)];
    const pattern = spec.patterns[Math.floor(rng() * spec.patterns.length)];
    return generateFeaturePattern(sigFigs, pattern, rng);
  }
  if (spec.range) {
    const [low, high] = spec.range;
    const raw = low + rng() * (high - low);
    if (spec.decimal_places !== undefined) return raw.toFixed(spec.decimal_places);
    if (spec.sig_figs !== undefined) return formatWithSigFigs(raw, spec.sig_figs);
    return raw.toString();
  }
  throw new Error('sampleValue: unsupported spec shape: ' + JSON.stringify(spec));
}

function generateFeaturePattern(sigFigs, pattern, rng) {
  const digits = () => Math.floor(rng() * 9) + 1;  // 1-9
  const captive = () => '0';
  switch (pattern) {
    case 'leading_zeros': {
      // "0.00<sig digits>"
      const leading = '0.' + '0'.repeat(2 + Math.floor(rng() * 3));
      let body = '';
      for (let i = 0; i < sigFigs; i++) body += i === 0 ? digits() : Math.floor(rng() * 10);
      return leading + body;
    }
    case 'captive_zero': {
      // "<d><0><d><d>..." with at least one captive zero
      let body = String(digits());
      for (let i = 1; i < sigFigs; i++) {
        body += (i === 1 || i === 2) ? captive() : digits();
      }
      // Add a decimal point partway through
      const dot = 1 + Math.floor(rng() * (sigFigs - 1));
      return body.slice(0, dot) + '.' + body.slice(dot);
    }
    case 'trailing_zero_with_decimal': {
      // "<digits>.<digits>0" where final 0 is significant
      let body = '';
      for (let i = 0; i < sigFigs - 1; i++) body += i === 0 ? digits() : Math.floor(rng() * 10);
      body += '0';
      // Insert a decimal point partway
      const dot = 1 + Math.floor(rng() * (body.length - 1));
      return body.slice(0, dot) + '.' + body.slice(dot);
    }
    case 'mixed':
    default: {
      // Random number with N sig figs and a decimal somewhere
      let body = String(digits());
      for (let i = 1; i < sigFigs; i++) body += Math.floor(rng() * 10);
      const dot = 1 + Math.floor(rng() * (sigFigs - 1));
      return body.slice(0, dot) + '.' + body.slice(dot);
    }
  }
}
```

- [ ] **Step 4: Run validate, samples, fuzz**

```bash
python .firecrawl/build_interactive.py --validate
python .firecrawl/build_interactive.py --show-samples 10
python .firecrawl/build_interactive.py --fuzz 1000
```

Expected: all three return exit 0; `--show-samples` produces a readable table.

- [ ] **Step 5: Build and smoke-test**

```bash
python .firecrawl/build_interactive.py
```

Open `HTML_Files_Interactive/Chapter_01.html` in a browser. Find the "How many sig figs in …?" problem. Click "Try a different version" 5×. Verify:
- The numeric value changes each time.
- The Solution pill, when opened, shows the correct sig-fig count + rule explanation.
- The browser console shows no errors.

- [ ] **Step 6: Commit**

```bash
git add .firecrawl/interactive_engine/engine.js .firecrawl/interactive_specs/chapter_01.yaml HTML_Files_Interactive/
git commit -m "Pilot problem 1: variable sig-fig counting (§1.11)"
```

---

### Task F2: Pilot Problem 2 — Sig-fig addition

Source: a §1.12 addition problem with three terms (e.g., "(2.45 g) + (12.1 g) + (0.378 g)").

**Files:**
- Modify: `.firecrawl/interactive_specs/chapter_01.yaml`

- [ ] **Step 1: Identify**

Run: `grep -n '(2\.45 g) + (12\.1 g)' HTML_Files/Chapter_01.html`. Confirm uniqueness.

- [ ] **Step 2: Append spec entry**

Add to `chapter_01.yaml`:

```yaml
  - id: "1.12.add"
    match_text: "(2.45 g) + (12.1 g) + (0.378 g)"
    question: "({a} g) + ({b} g) + ({c} g) = ?"
    variables:
      a: { range: [1.0, 10.0], decimal_places: 2 }
      b: { range: [10.0, 50.0], decimal_places: 1 }
      c: { range: [0.1, 1.0], decimal_places: 3 }
    answer:
      operation: add
      unit: g
    explanation_template: |
      Sum = {rawSum}; round to {limitingDecimalPlaces} decimal place(s)
      ({limitingValue} has fewest decimal places) → {finalSum} g.
```

- [ ] **Step 3: Validate, sample, fuzz**

Run all three commands as in Task F1, Step 4.

- [ ] **Step 4: Build and smoke-test**

```bash
python .firecrawl/build_interactive.py
```

Open the HTML, find the addition problem, click button 5×, verify all three values change and the solution rounds correctly.

- [ ] **Step 5: Commit**

```bash
git add .firecrawl/interactive_specs/chapter_01.yaml HTML_Files_Interactive/
git commit -m "Pilot problem 2: variable sig-fig addition (§1.12)"
```

---

### Task F3: Pilot Problem 3 — Sig-fig multiplication

Source: a §1.12 multiplication problem with two or three factors (e.g., "(3.75 cm)(2.0 cm)(4.50 cm)").

- [ ] **Step 1: Identify**

Run: `grep -n '(3\.75 cm)(2\.0 cm)(4\.50 cm)' HTML_Files/Chapter_01.html`.

- [ ] **Step 2: Append spec entry**

```yaml
  - id: "1.12.multiply"
    match_text: "(3.75 cm)(2.0 cm)(4.50 cm)"
    question: "({a} cm)({b} cm)({c} cm) = ?"
    variables:
      a: { range: [1.0, 10.0], sig_figs: 3 }
      b: { range: [1.0, 5.0], sig_figs: 2 }
      c: { range: [1.0, 10.0], sig_figs: 3 }
    answer:
      operation: multiply
      unit: cm^3
    explanation_template: |
      Product = {rawProduct}; limit to {limitingSigFigs} sig figs
      ({limitingValue} is the limit) → {finalProduct} cm³.
```

- [ ] **Step 3: Validate, sample, fuzz, build, smoke-test**

(*See Task F1 for command list.*)

- [ ] **Step 4: Commit**

```bash
git add .firecrawl/interactive_specs/chapter_01.yaml HTML_Files_Interactive/
git commit -m "Pilot problem 3: variable sig-fig multiplication (§1.12)"
```

---

### Task F4: Pilot Problem 4 — Decimal → scientific notation

Source: a §1.13 conversion-to-sci-notation problem (e.g., "Express 0.000 045 6 in scientific notation").

- [ ] **Step 1: Identify**

Run: `grep -n 'Express 0\.000 045 6' HTML_Files/Chapter_01.html`.

- [ ] **Step 2: Append spec entry**

```yaml
  - id: "1.13.to_sci_notation"
    match_text: "Express 0.000 045 6 in scientific notation"
    question: "Express {value} in scientific notation."
    variables:
      value:
        range: [0.000001, 0.001]
        sig_figs: 3
    answer:
      operation: to_sci_notation
    explanation_template: |
      {value} = {coefficient} × 10^{exponent}.
```

- [ ] **Step 3: Validate, sample, fuzz, build, smoke-test**

- [ ] **Step 4: Commit**

```bash
git add .firecrawl/interactive_specs/chapter_01.yaml HTML_Files_Interactive/
git commit -m "Pilot problem 4: decimal → sci notation (§1.13)"
```

---

### Task F5: Pilot Problem 5 — Scientific notation arithmetic

Source: a §1.14 multiplication problem (e.g., "(2.4 × 10⁵) × (3.0 × 10²)").

- [ ] **Step 1: Identify**

Run: `grep -n '(2\.4 × 10⁵) × (3\.0 × 10²)' HTML_Files/Chapter_01.html`. (Note: the raw HTML may use UTF-8 superscripts; adjust grep accordingly.)

- [ ] **Step 2: Append spec entry**

```yaml
  - id: "1.14.sci_arith"
    match_text: "(2.4 × 10⁵) × (3.0 × 10²)"
    question: "({a_coefficient} × 10^{a_exponent}) × ({b_coefficient} × 10^{b_exponent}) = ?"
    variables:
      a_coefficient: { range: [1.0, 9.9], sig_figs: 2 }
      a_exponent: { range: [3, 6], decimal_places: 0 }
      b_coefficient: { range: [1.0, 9.9], sig_figs: 2 }
      b_exponent: { range: [-2, 4], decimal_places: 0 }
    answer:
      operation: sci_notation_arithmetic
    explanation_template: |
      Multiply coefficients ({a_coefficient} × {b_coefficient}); add exponents
      ({a_exponent} + {b_exponent}). Result: {coefficient} × 10^{exponent}
      (limited to fewest sig figs in coefficients).
```

- [ ] **Step 3: Validate, sample, fuzz, build, smoke-test**

When running `--show-samples 10`, **verify the exponents print as integers** (e.g. `5`, not `5.0`). `sampleValue` with `decimal_places: 0` calls `raw.toFixed(0)`, which produces an integer string. If you see decimal points in the exponent output, the bug is in `sampleValue` — exponents must be string-parsable as integers because `computeSciNotationArith` calls `parseInt(...)` on them.

- [ ] **Step 4: Commit**

```bash
git add .firecrawl/interactive_specs/chapter_01.yaml HTML_Files_Interactive/
git commit -m "Pilot problem 5: sci notation arithmetic (§1.14)"
```

---

### Task F6: Pilot Problem 6 — Linear extrapolation from a graph

Source: §1.16 problem "A best-fit line through gas-pressure-vs-temperature data has slope 0.025 atm/°C and y-intercept 6.83 atm. Predict the pressure at 50 °C."

- [ ] **Step 1: Identify**

Run: `grep -n 'best-fit line through gas-pressure' HTML_Files/Chapter_01.html`.

- [ ] **Step 2: Append spec entry**

```yaml
  - id: "1.16.linear"
    match_text: "best-fit line through gas-pressure-vs-temperature data has slope 0.025 atm/°C"
    question: |
      A best-fit line has slope {slope} atm/°C and y-intercept {intercept} atm.
      Predict the pressure at {x} °C.
    variables:
      slope: { range: [0.010, 0.050], sig_figs: 2 }
      intercept: { range: [5.00, 8.00], sig_figs: 3 }
      x: { range: [10, 100], sig_figs: 2 }
    answer:
      operation: linear_function
      unit: atm
    constraints:
      result_range: [4.0, 20.0]
    explanation_template: |
      P = m·T + b = {slope}·{x} + {intercept} = {y} atm.
```

- [ ] **Step 3: Validate, sample, fuzz, build, smoke-test**

- [ ] **Step 4: Commit**

```bash
git add .firecrawl/interactive_specs/chapter_01.yaml HTML_Files_Interactive/
git commit -m "Pilot problem 6: linear extrapolation (§1.16)"
```

---

## Phase G — CI integration and final regression check

### Task G1: Extend `.github/workflows/pages.yml`

**Files:**
- Modify: `.github/workflows/pages.yml`

The current workflow has one `build` job that runs `pip install python-docx mammoth beautifulsoup4`, then `python .firecrawl/build_html.py`, then uploads `HTML_Files/` as the Pages artifact. We add a single new step before the artifact upload that builds the interactive bundle and copies it under `HTML_Files/interactive/`. The Pages artifact then includes both.

The runner (`ubuntu-latest`) has Node 20+ pre-installed, so the engine's `--fuzz` step (which shells out to `node`) works without an extra `setup-node` action.

- [ ] **Step 1: Modify `.github/workflows/pages.yml` lines 43–47**

Replace this block:

```yaml
      - name: Install build dependencies
        run: pip install "python-docx>=1.1" "mammoth>=1.7" "beautifulsoup4>=4.12"

      - name: Build HTML preview from .docx sources
        run: python .firecrawl/build_html.py
```

with:

```yaml
      - name: Install build dependencies
        run: pip install "python-docx>=1.1" "mammoth>=1.7" "beautifulsoup4>=4.12" "pyyaml>=6.0"

      - name: Build HTML preview from .docx sources
        run: python .firecrawl/build_html.py

      - name: Build interactive Chapter 1
        run: |
          python .firecrawl/build_interactive.py --validate
          python .firecrawl/build_interactive.py --fuzz 1000
          python .firecrawl/build_interactive.py
          mkdir -p HTML_Files/interactive
          cp -r HTML_Files_Interactive/. HTML_Files/interactive/
```

(*Note `cp -r HTML_Files_Interactive/.` rather than `…/*` — the dot form copies the directory's contents including dotfiles and is shell-portable.*)

- [ ] **Step 2: Verify the workflow YAML is well-formed**

Run: `python -c "import yaml; yaml.safe_load(open('.github/workflows/pages.yml'))"`
Expected: No output, exit 0.

- [ ] **Step 3: Commit (do not push yet)**

```bash
git add .github/workflows/pages.yml
git commit -m "CI: build and deploy interactive Ch 1 to /interactive/"
```

- [ ] **Step 4: Hand off the push to the user**

Tell the user the plan is ready for deployment:
> "All commits are local. To deploy: `git push origin main`. Watch the Actions tab; on success, the interactive Ch 1 will be at https://aelangovan-pcd.github.io/CHEM-139-OER-Text-2026/interactive/Chapter_01.html"

---

### Task G2: Final regression check (acceptance criteria)

**Files:** None — verification only.

- [ ] **Step 1: Confirm no docx was modified**

Run: `git status -- '*.docx'`
Expected: Clean (no tracked .docx files modified).

- [ ] **Step 2: Confirm canonical HTML is byte-identical**

Run: `python .firecrawl/build_html.py` then `git diff --stat -- HTML_Files/`
Expected: Empty diff (or the only diff is `HTML_Files/interactive/`, which doesn't exist locally yet — depends on whether you copied from `HTML_Files_Interactive/`).

- [ ] **Step 3: Confirm Canvas/IMSCC scripts unaffected**

Run: `ls .firecrawl/build_canvas.py .firecrawl/build_imscc.py 2>/dev/null` — these don't exist on this workspace per CLAUDE.md, so the test is moot. Note in commit log that the absence is expected.

- [ ] **Step 4: Run the full test suites once more**

```bash
cd .firecrawl/interactive_engine && node --test engine.test.js
cd ../.. && python .firecrawl/test_build_interactive.py
python .firecrawl/build_interactive.py --fuzz 1000
```

Expected: All pass.

- [ ] **Step 5: Final commit (or note completion)**

If any documentation or CHANGELOG-style note is desired, add it now. Otherwise, mark the pilot complete.

```bash
git commit --allow-empty -m "Mark variable-problem pilot complete (Ch 1)"
```

---

## Self-Review Notes

Verified during plan-writing:

- Every task has explicit file paths.
- Every code-emitting step contains complete code.
- Function names referenced across tasks (`countSigFigs`, `formatWithSigFigs`, `decimalToSciNotation`, `sciNotationToDecimal`, `addPreservingDecimalPlaces`, `multiplyPreservingSigFigs`, `evaluateLinearFunction`, `mulberry32`, `sampleValue`, `generateVariant`, `substituteTemplate`, `renderLatexForOperation`, `bootstrap`) are consistent throughout.
- Spec coverage: every section of the design spec maps to one or more tasks (engine primitives → Phase B; sampling/guardrails → Phase C; DOM wiring → Phase D; build script → Phase E; the 6 pilot problems → Phase F; CI → Phase G).
- No "TBD" or "implement later" placeholders.
- `Co-Authored-By: Claude` trailer is **deliberately omitted** from every commit message per `CLAUDE.md`.
