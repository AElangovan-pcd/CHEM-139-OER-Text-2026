# Variable-Problem Pilot — Phase 3a Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Author 6 Chapter 8 mole-conversion problems using Phase 2's existing factor-label engine, then ship them to Pages and Render.

**Architecture:** Drop a new `chapter_08.yaml` into `interactive_specs/`; the existing `discover_chapters()` build infrastructure picks it up automatically. **Zero engine changes.** Zero build-script changes. Zero CI changes. Each problem uses Phase 2's `factor_label` operation with appropriate molar-mass and Avogadro-number factors.

**Tech Stack:**
- **Engine:** Phase 2's `engine.js` (50 unit tests, factor-label primitives shipped)
- **Build script:** Phase 2's `build_interactive.py` with multi-chapter discovery and `--chapter` flag
- **YAML schema:** Phase 2's `factor_label` operation contract
- **CI:** Phase 2's `pages.yml` (already iterates over all discovered chapters)
- **Predecessor:** `docs/superpowers/specs/2026-05-07-variable-problems-phase3a-design.md` (committed `3808ffd`)

**Repo conventions:** No `Co-Authored-By: Claude` trailer (per `CLAUDE.md`). YAML uses snake_case (`num_value`, `den_unit`, `sig_figs`, `value_param`, `input_unit`, `target_unit`).

---

## Decided open questions (from spec §9)

| # | Question | Decision |
|---|---|---|
| 1 | Match_text strings | All 6 candidates verified unique in `HTML_Files/Chapter_08.html` (count check during plan-writing). Locked in below. |
| 2 | Molar mass values | Pulled directly from each textbook problem's parenthetical: NaCl 58.44, H₂O 18.02, Cu 63.55. Sig figs declared as 4 (textbook convention). |
| 3 | Avogadro sig figs | 4 (`6.022e23`); declared as `sig_figs: 4` per the textbook convention. |
| 4 | Sci-notation input rendering for #4 | **Known limitation, accepted for Phase 3a.** The engine's `formatWithSigFigs` returns JS-default sci-notation strings (e.g., `'5.7e+23'`) without preserving trailing zeros. Sampled values render in the question stem as `5.7e+23` rather than `5.7 × 10²³`. Pedagogically passable; documented as Phase 3b polish. **Do not attempt to fix in Phase 3a — engine changes are out of scope.** |
| 5 | YAML reference comments per problem | Yes — each entry includes a brief `# molar mass: X g/mol per textbook` comment near the chain step for future maintainers. |

---

## File Structure

**New files (all tracked, both committed per task):**

```
.firecrawl/interactive_specs/chapter_08.yaml      # 6 pilot problems
HTML_Files/interactive/Chapter_08.html            # build output
```

**Files NOT changed by this plan:**

- Any `.docx` chapter source.
- `.firecrawl/build_interactive.py` (multi-chapter discovery already finds new YAML).
- `.firecrawl/interactive_engine/engine.js` and `engine.test.js` (existing primitives suffice).
- `.firecrawl/interactive_engine/engine.css` (no styling change).
- `.firecrawl/test_build_interactive.py` (no test changes).
- `.github/workflows/pages.yml` (already iterates chapters).
- Phase 1 spec/output (`chapter_01.yaml`, `Chapter_01.html`).
- Phase 2 spec/output (`chapter_02.yaml`, `Chapter_02.html`).
- `HTML_Files/interactive/assets/engine.js` and `engine.css` — engine source mtime won't change in Phase 3a, so `shutil.copy2` preserves the existing asset mtime. **No stale-asset risk** (Phase 2's bug only bites when engine source changes without re-staging the asset).

---

## Engine API recap (no changes from Phase 2)

For reference while authoring YAML — the `factor_label` operation expects:

```yaml
answer:
  operation: factor_label
  value_param: <var-name>          # which variable supplies the input value
  input_unit: <unit>                # must equal chain[0].den_unit
  chain:
    - num_value: <number>           # numerator value (the "to" side)
      num_unit: <string>            # numerator unit
      den_value: <number>           # denominator value
      den_unit: <string>            # must equal previous step's num_unit (or input_unit for step 0)
      exact: true | false           # if true, factor doesn't constrain sig figs
      sig_figs: <int>               # required if not exact
  target_unit: <unit>               # must equal chain[-1].num_unit
```

Engine validates the chain at variant-generation time (every `--fuzz` and every browser click). Cancellation mismatches throw early; `--fuzz 1000` catches them at build time.

---

# Tasks

## Phase A — Author 6 Chapter 8 problems

### Task A0: Create empty `chapter_08.yaml` scaffold

**Files:**
- Create: `.firecrawl/interactive_specs/chapter_08.yaml`

- [ ] **Step 1: Pre-flight check**

Run via Bash:
```
cd .firecrawl/interactive_engine && node --test engine.test.js
cd ../.. && python .firecrawl/test_build_interactive.py
python .firecrawl/build_interactive.py --validate
```
Expected: 50/50 engine tests, 14/14 Python tests, "VALIDATE OK: 12 problems across 2 chapter(s)." (Phase 1 + Phase 2 baseline).

If any check fails, STOP and report `BLOCKED`.

- [ ] **Step 2: Create `.firecrawl/interactive_specs/chapter_08.yaml`** with this exact content:

```yaml
# Variable-problem specs for Chapter 8 (Mole Concept and Chemical Formulas).
# Schema reference: docs/superpowers/specs/2026-05-07-variable-problems-phase3a-design.md
problems: []
```

- [ ] **Step 3: Verify discovery picks it up**

Run: `python .firecrawl/build_interactive.py --validate`
Expected output ends with: `VALIDATE OK: 12 problems across 3 chapter(s).` (Ch 8's 0 problems contribute zero to the total but are counted as a chapter.)

- [ ] **Step 4: Commit**

```bash
git add .firecrawl/interactive_specs/chapter_08.yaml
git commit -m "Add empty Chapter 8 interactive spec scaffold"
```

---

### Task A1: Pilot problem 1 — mass to mole (NaCl)

**Files:**
- Modify: `.firecrawl/interactive_specs/chapter_08.yaml`
- Modify: `HTML_Files/interactive/Chapter_08.html` (rebuilt as side effect)

- [ ] **Step 1: Verify match_text**

Run: `grep -c 'How many moles in 25.0 g of NaCl' HTML_Files/Chapter_08.html`
Expected: `1`.

- [ ] **Step 2: Replace the contents** of `.firecrawl/interactive_specs/chapter_08.yaml` with:

```yaml
# Variable-problem specs for Chapter 8 (Mole Concept and Chemical Formulas).
# Schema reference: docs/superpowers/specs/2026-05-07-variable-problems-phase3a-design.md
problems:
  - id: "8.10.mass_to_mole"
    match_text: "How many moles in 25.0 g of NaCl"
    question: "How many moles are in {mass} g of NaCl? (M = 58.44 g/mol)"
    variables:
      mass: { range: [5.0, 100.0], sig_figs: 3 }
    answer:
      operation: factor_label
      value_param: mass
      input_unit: g
      chain:
        # molar mass of NaCl: 58.44 g/mol per textbook (4 sig figs)
        - num_value: 1
          num_unit: mol
          den_value: 58.44
          den_unit: g
          sig_figs: 4
      target_unit: mol
    explanation_template: |
      "g" cancels via the 1 mol / 58.44 g molar-mass factor.
      {limitingSigFigs} sig figs from "{mass} g" yield {finalResult} mol.
```

- [ ] **Step 3: Validate, fuzz, build**

```bash
python .firecrawl/build_interactive.py --validate
python .firecrawl/build_interactive.py --fuzz 1000
python .firecrawl/build_interactive.py
```

Expected:
- `--validate` ends with "VALIDATE OK: 13 problems across 3 chapter(s)."
- `--fuzz` reports "FUZZ OK: chapter 08 :: 8.10.mass_to_mole 1000/1000 variants passed." (along with all 12 prior).
- build prints "Wrote .../HTML_Files/interactive/Chapter_08.html".

- [ ] **Step 4: Verify HTML output**

```bash
grep -c 'data-variant-spec="8.10.mass_to_mole"' HTML_Files/interactive/Chapter_08.html
```
Expected: `1`.

- [ ] **Step 5: Commit**

```bash
git add .firecrawl/interactive_specs/chapter_08.yaml HTML_Files/interactive/Chapter_08.html
git commit -m "P3a problem 1: variable g → mol via molar mass (§8.10)"
```

---

### Task A2: Pilot problem 2 — mole to mass (H₂O)

- [ ] **Step 1: Verify match_text**

Run: `grep -c 'Mass, in grams, of 0.250 mol H' HTML_Files/Chapter_08.html`
Expected: `1`.

- [ ] **Step 2: Append** to `chapter_08.yaml` (as a sibling list item under `problems:`):

```yaml
  - id: "8.10.mole_to_mass"
    match_text: "Mass, in grams, of 0.250 mol H"
    question: "What is the mass, in grams, of {moles} mol H₂O? (M = 18.02 g/mol)"
    variables:
      moles: { range: [0.05, 5.00], sig_figs: 3 }
    answer:
      operation: factor_label
      value_param: moles
      input_unit: mol
      chain:
        # molar mass of H₂O: 18.02 g/mol per textbook (4 sig figs)
        - num_value: 18.02
          num_unit: g
          den_value: 1
          den_unit: mol
          sig_figs: 4
      target_unit: g
    explanation_template: |
      "mol" cancels via the 18.02 g / 1 mol molar-mass factor.
      {limitingSigFigs} sig figs from "{moles} mol" yield {finalResult} g.
```

- [ ] **Step 3: Validate, fuzz, build, verify**

Same commands as Task A1, Step 3. Expected: 14 problems validate; "FUZZ OK: chapter 08 :: 8.10.mole_to_mass 1000/1000".

- [ ] **Step 4: Commit**

```bash
git add .firecrawl/interactive_specs/chapter_08.yaml HTML_Files/interactive/Chapter_08.html
git commit -m "P3a problem 2: variable mol → g via molar mass (§8.10)"
```

---

### Task A3: Pilot problem 3 — mole to molecules (Avogadro)

- [ ] **Step 1: Verify match_text**

Run: `grep -c 'Number of molecules in 0.100 mol CO' HTML_Files/Chapter_08.html`
Expected: `1`.

- [ ] **Step 2: Append**:

```yaml
  - id: "8.10.mole_to_molecules"
    match_text: "Number of molecules in 0.100 mol CO"
    question: "How many molecules are in {moles} mol CO₂?"
    variables:
      moles: { range: [0.01, 1.00], sig_figs: 3 }
    answer:
      operation: factor_label
      value_param: moles
      input_unit: mol
      chain:
        # Avogadro's number: 6.022 × 10²³ molecules / 1 mol (4 sig figs)
        - num_value: 6.022e23
          num_unit: molecules
          den_value: 1
          den_unit: mol
          sig_figs: 4
      target_unit: molecules
    explanation_template: |
      "mol" cancels via Avogadro's number (6.022 × 10²³ molecules per mole).
      {limitingSigFigs} sig figs from "{moles} mol" yield {finalResult} molecules.
```

- [ ] **Step 3: Validate, fuzz, build, verify**

Expected: 15 problems validate; "FUZZ OK: chapter 08 :: 8.10.mole_to_molecules 1000/1000".

- [ ] **Step 4: Commit**

```bash
git add .firecrawl/interactive_specs/chapter_08.yaml HTML_Files/interactive/Chapter_08.html
git commit -m "P3a problem 3: variable mol → molecules via Avogadro (§8.10)"
```

---

### Task A4: Pilot problem 4 — atoms to mass (two-step, sci-notation input)

**Note on display quirk** (per spec §5 and Decided Open Question #4): the sampled `n_atoms` value renders in the question stem as JS-default sci-notation (e.g., `'5.7e+23'`) instead of `'5.7 × 10²³'`. `formatWithSigFigs` may also lose trailing zeros (e.g., `5.70e23` → `'5.7e+23'`, dropping the third sig fig from display). This is acceptable for Phase 3a; pedagogically passable. Do NOT attempt to fix; engine changes are out of scope. Phase 3b polish item.

- [ ] **Step 1: Verify match_text**

Run: `grep -c 'Mass of 3.011' HTML_Files/Chapter_08.html`
Expected: `1`.

- [ ] **Step 2: Append**:

```yaml
  - id: "8.10.atoms_to_mass"
    match_text: "Mass of 3.011"
    question: "What is the mass of {n_atoms} atoms of Cu? (M = 63.55 g/mol)"
    variables:
      n_atoms: { range: [1.0e22, 9.99e23], sig_figs: 3 }
    answer:
      operation: factor_label
      value_param: n_atoms
      input_unit: atoms
      chain:
        # Avogadro's number (4 sig figs)
        - num_value: 1
          num_unit: mol
          den_value: 6.022e23
          den_unit: atoms
          sig_figs: 4
        # molar mass of Cu: 63.55 g/mol (4 sig figs)
        - num_value: 63.55
          num_unit: g
          den_value: 1
          den_unit: mol
          sig_figs: 4
      target_unit: g
    explanation_template: |
      "atoms" cancels via Avogadro; "mol" cancels via Cu molar mass.
      {limitingSigFigs} sig figs from "{n_atoms} atoms" yield {finalResult} g.
```

- [ ] **Step 3: Validate, fuzz, build, verify**

Expected: 16 problems validate; "FUZZ OK: chapter 08 :: 8.10.atoms_to_mass 1000/1000".

The fuzz check should pass even with sci-notation input — the placeholder-leak regex doesn't trigger on JS-formatted sci-notation strings (`5.7e+23` doesn't match `\{[a-zA-Z_]\w*\}`).

- [ ] **Step 4: Commit**

```bash
git add .firecrawl/interactive_specs/chapter_08.yaml HTML_Files/interactive/Chapter_08.html
git commit -m "P3a problem 4: variable atoms → mol → g (§8.10, sci-notation input)"
```

---

### Task A5: Pilot problem 5 — mole compound to mole element (subscript factor)

This problem introduces the **subscript-as-exact-factor** idiom new to Phase 3a. The "12" in "12 mol H / 1 mol C₆H₁₂O₆" comes from the chemical formula's subscript and is treated as exact (no sig-fig erosion).

- [ ] **Step 1: Verify match_text**

Run: `grep -c 'How many moles of H atoms in 0.50 mol C' HTML_Files/Chapter_08.html`
Expected: `1`.

- [ ] **Step 2: Append**:

```yaml
  - id: "8.9.mole_ratio_subscript"
    match_text: "How many moles of H atoms in 0.50 mol C"
    question: "How many moles of H atoms are in {moles} mol of glucose (C₆H₁₂O₆)?"
    variables:
      moles: { range: [0.05, 5.00], sig_figs: 2 }
    answer:
      operation: factor_label
      value_param: moles
      input_unit: mol C₆H₁₂O₆
      chain:
        # subscript-derived factor: glucose has 12 H atoms per molecule (exact integer)
        - num_value: 12
          num_unit: mol H
          den_value: 1
          den_unit: mol C₆H₁₂O₆
          exact: true
      target_unit: mol H
    explanation_template: |
      "mol C₆H₁₂O₆" cancels via the 12 mol H / 1 mol formula-unit subscript factor (exact).
      {limitingSigFigs} sig figs from "{moles} mol C₆H₁₂O₆" yield {finalResult} mol H.
```

- [ ] **Step 3: Validate, fuzz, build, verify**

Expected: 17 problems validate; "FUZZ OK: chapter 08 :: 8.9.mole_ratio_subscript 1000/1000".

- [ ] **Step 4: Commit**

```bash
git add .firecrawl/interactive_specs/chapter_08.yaml HTML_Files/interactive/Chapter_08.html
git commit -m "P3a problem 5: variable mol compound → mol element via subscript (§8.9)"
```

---

### Task A6: Pilot problem 6 — three-step chain (g compound → mol → mol element → atoms)

This is the longest chain so far (Phase 2 topped out at two steps). Stress-tests `renderFactorLabelLatex`'s output with three `\times \frac{...}{...}` segments.

- [ ] **Step 1: Verify match_text**

Run: `grep -c 'How many H atoms in 18.0 g H' HTML_Files/Chapter_08.html`
Expected: `1`.

- [ ] **Step 2: Append**:

```yaml
  - id: "8.10.three_step_chain"
    match_text: "How many H atoms in 18.0 g H"
    question: "How many H atoms are in {mass} g of H₂O? (M = 18.02 g/mol)"
    variables:
      mass: { range: [1.0, 100.0], sig_figs: 3 }
    answer:
      operation: factor_label
      value_param: mass
      input_unit: g H₂O
      chain:
        # molar mass of H₂O: 18.02 g/mol (4 sig figs)
        - num_value: 1
          num_unit: mol H₂O
          den_value: 18.02
          den_unit: g H₂O
          sig_figs: 4
        # subscript factor: 2 H atoms per H₂O molecule (exact)
        - num_value: 2
          num_unit: mol H
          den_value: 1
          den_unit: mol H₂O
          exact: true
        # Avogadro's number (4 sig figs)
        - num_value: 6.022e23
          num_unit: atoms
          den_value: 1
          den_unit: mol H
          sig_figs: 4
      target_unit: atoms
    explanation_template: |
      "g H₂O" cancels via molar mass; "mol H₂O" via subscript; "mol H" via Avogadro.
      {limitingSigFigs} sig figs from "{mass} g H₂O" yield {finalResult} atoms.
```

- [ ] **Step 3: Validate, fuzz, build, verify**

Expected: 18 problems validate (across 3 chapters); "FUZZ OK: chapter 08 :: 8.10.three_step_chain 1000/1000".

- [ ] **Step 4: Manual smoke check (no commands — visual inspection)**

Open `HTML_Files/interactive/Chapter_08.html` in a browser via the local server (or after Pages deploy). Click "Try a different version" 3× on each of the 6 Ch 8 problems. Verify:
- Question stem updates with new value
- Pill closes on click
- Reopening pill shows the recomputed factor-label chain with `\cancel{}` on every cancelled unit
- For #4 and #6: the sci-notation values render as `5.7e+23` (acceptable Phase 3a quirk)
- For #6 specifically: the chain has THREE `\times \frac{...}{...}` segments rendered cleanly
- Browser console has no errors

- [ ] **Step 5: Commit**

```bash
git add .firecrawl/interactive_specs/chapter_08.yaml HTML_Files/interactive/Chapter_08.html
git commit -m "P3a problem 6: variable g → mol → mol → atoms three-step chain (§8.10)"
```

---

## Phase B — Final regression check

### Task B1: Verify acceptance criteria across all three chapters

**Files:** None — verification only.

- [ ] **Step 1: All tests pass**

```bash
cd .firecrawl/interactive_engine && node --test engine.test.js
cd ../.. && python .firecrawl/test_build_interactive.py
```
Expected: 50/50 engine tests; 14/14 Python tests.

- [ ] **Step 2: All chapters validate and fuzz across the full 18-problem set**

```bash
python .firecrawl/build_interactive.py --validate
python .firecrawl/build_interactive.py --fuzz 1000
```
Expected:
- `--validate` ends with "VALIDATE OK: 18 problems across 3 chapter(s)."
- `--fuzz` produces 18 lines of "FUZZ OK: ..." (6 chapter 01 + 6 chapter 02 + 6 chapter 08), all 1000/1000.

- [ ] **Step 3: HTML output present for all three chapters**

```bash
ls HTML_Files/interactive/Chapter_01.html HTML_Files/interactive/Chapter_02.html HTML_Files/interactive/Chapter_08.html
ls HTML_Files/interactive/assets/engine.js HTML_Files/interactive/assets/engine.css
grep -oE 'data-variant-spec="[^"]+"' HTML_Files/interactive/Chapter_08.html | wc -l
```
Expected:
- All three chapter HTML files exist; both assets exist.
- Last grep returns 6 (six `data-variant-spec` attributes in Chapter_08.html).

- [ ] **Step 4: Confirm no canonical regression**

```bash
git diff main -- HTML_Files/Chapter_01.html HTML_Files/Chapter_02.html HTML_Files/Chapter_08.html
git diff main -- '*.docx'
```
Expected: empty output (no canonical regression beyond what's expected).

(Note: `git diff main -- HTML_Files/interactive/Chapter_01.html` and `Chapter_02.html` may show changes if cache-buster mtimes drifted; that's acceptable. The check above only looks at the canonical `HTML_Files/Chapter_*.html` outside the `interactive/` subdir.)

- [ ] **Step 5: Engine asset is up-to-date**

Phase 3a doesn't change the engine source, so `HTML_Files/interactive/assets/engine.js` should still match `.firecrawl/interactive_engine/engine.js` byte-for-byte:

```bash
diff .firecrawl/interactive_engine/engine.js HTML_Files/interactive/assets/engine.js
```
Expected: no output (identical content).

If different, the asset has drifted — run `python .firecrawl/build_interactive.py` to refresh, then commit any updates with message "Refresh interactive engine.js asset for Phase 3a deploy" (similar to the Phase 2 commit `2c56942`).

- [ ] **Step 6: Phase 1 + Phase 2 problems still work (manual smoke test)**

Open `HTML_Files/interactive/Chapter_01.html` and `Chapter_02.html` in a browser via the local server. Click "Try a different version" on at least one problem in each chapter. Verify no console errors and the variant cycling still works.

- [ ] **Step 7: (Optional) Final empty commit to mark phase complete**

If desired:

```bash
git commit --allow-empty -m "Mark Phase 3a (Ch 8 mole conversions) pilot complete"
```

---

## Self-Review Notes

Verified during plan-writing:

**Spec coverage:**
- Spec §1 (goal): single-chapter pilot reusing Phase 2 engine → covered by Phase A authoring tasks.
- Spec §2 (scope): in-scope items each map to a task; out-of-scope items (mass-percent, empirical formulas, etc.) are explicitly absent from the plan.
- Spec §3 (architecture: no engine changes): no Phase A or B task touches the engine. Files-NOT-changed list is the contract.
- Spec §4 (6 pilot problems): tasks A1-A6 each implement one of the six.
- Spec §5 (sci-notation rendering quirk): explicitly noted in Task A4's prose; accepted for Phase 3a.
- Spec §6 (resolved decisions): all seven decisions reflected in the YAML and task instructions (molar mass values, Avogadro sig figs, no substance variation, etc.).
- Spec §7 (Phase 3b+ follow-ups): outside this plan; will be addressed in subsequent phases.
- Spec §8 (acceptance criteria): all eight bullets exercised in Task B1 plus per-task validate/fuzz/build cycles.
- Spec §9 (open questions): all four resolved in this plan's "Decided open questions" table at the top.

**Function-name and field-name consistency:**
- All 6 problems use `factor_label` operation (Phase 2 contract).
- All chain steps use `num_value`, `num_unit`, `den_value`, `den_unit`, `exact`, `sig_figs` (snake_case, matching Phase 1 + 2 conventions).
- All `value_param`, `input_unit`, `target_unit` fields are populated.
- Each problem's `input_unit` matches its `chain[0].den_unit`; subsequent steps' `den_unit` matches the previous step's `num_unit`. Verified by hand for each of the 6.

**Commit hygiene:**
- Every commit message is single-line ≤ 70 characters.
- No `Co-Authored-By: Claude` trailer (per `CLAUDE.md`).
- Per-task staging is exactly two paths (`chapter_08.yaml` + `Chapter_08.html`) — no `git add -A` or `git add .`.

**No `TBD`/`TODO`/placeholder strings.** Every code block in every task contains complete, runnable code.

**Known limitations explicitly documented:**
- Task A4: sci-notation input rendering quirk (e.g., `5.7e+23` literal in the question stem). Pedagogically acceptable for Phase 3a; recorded as Phase 3b polish.
- Task A6: same quirk for the sci-notation OUTPUT (e.g., `1.2e+24` atoms). Same handling — accept, document.

**Estimated execution time:** ~2–3 hours
- 7 tasks (A0 + A1-A6 + B1)
- Each authoring task ~15-20 min (verify match_text, append YAML, validate, fuzz 1000, build, verify, commit)
- Final regression ~10 min
- No subagent fix loops expected (engine is settled, YAML is mechanical)
