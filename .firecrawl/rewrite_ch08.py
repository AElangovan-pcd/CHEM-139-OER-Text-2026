"""Apply factor-label rewrites to Chapter 8 (Mole Concept) Solutions."""
from rewrite_engine import apply_rewrites

# Indices to LEAVE UNTOUCHED (0-based Solution paragraph order). These are
# pure atomic-mass additions, qualitative answers, or simple ratio listings
# where no unit cancellation is being demonstrated.
SKIP = {
    0,   # 22.99 + 35.45 = 58.44 (pure addition)
    1,   # 40.08 + 2(16.00 + 1.008) (pure addition)
    2,   # 6(12.01) + 12(1.008) + 6(16.00) (pure addition)
    10,  # Al₂(SO₄)₃ ratio 2:3:12 (no math)
    13,  # (NH₄)₂SO₄ atom counts (multiplications, no cancellation)
    17,  # multi-element ambiguous (qualitative ending)
    23,  # why combustion finds O by difference (qualitative)
    35,  # CaCO₃ formula mass (pure addition)
    36,  # (NH₄)₂SO₄ formula mass (pure addition)
    42,  # 1.000 mol CO₂ → molecules (trivial single conversion-factor;
         # leaving unchanged keeps response length down -- can revisit)
    49,  # CH empirical, M=78.11: complex multi-step, leave for hand pass
    57,  # CuSO₄·5H₂O molar mass (addition)
}

# Each entry: (anchor_text, consume_after, [math_lines_with_~~strike~~_markers], explanation)
# anchor_text is informational only; the engine applies in document order.

REWRITES = [
    # ---- Formula Mass and Mass Percent (PP3, PP4) ----
    # PP3: %N in NH₃   (idx 3)
    ("M(NH₃)=", 0, [
        "M(NH₃) = 14.01 + 3(1.008) = 17.03 g/mol",
        "% N = (14.01 ~~g~~ N / 17.03 ~~g~~ NH₃) × 100% = 82.27%",
    ],
        "\"g\" cancels in the mass ratio, leaving a dimensionless percentage. Four sig figs (limited by 14.01 and 17.03)."
    ),
    # PP4: %O in CaCO₃ (idx 4)
    ("M = 40.08", 0, [
        "M(CaCO₃) = 40.08 + 12.01 + 3(16.00) = 100.09 g/mol",
        "Mass of O in 1 formula unit = 3(16.00) = 48.00 g/mol",
        "% O = (48.00 ~~g~~ O / 100.09 ~~g~~ CaCO₃) × 100% = 47.96%",
    ],
        "\"g\" cancels in the mass ratio. Four sig figs throughout."
    ),

    # ---- Mole Concept Conversions ----
    # PP5: 25.0 g NaCl → mol (idx 5)
    ("25.0 / 58.44", 0, [
        "25.0 ~~g~~ NaCl × (1 mol / 58.44 ~~g~~) = 0.428 mol",
    ],
        "\"g\" cancels, leaving \"mol\". Three sig figs from \"25.0\"."
    ),
    # PP6: 0.250 mol H₂O → g (idx 6)
    ("0.250 × 18.02", 0, [
        "0.250 ~~mol~~ × (18.02 g / 1 ~~mol~~) = 4.51 g",
    ],
        "\"mol\" cancels, leaving \"g\". Three sig figs."
    ),
    # PP7: molecules in 0.100 mol CO₂ (idx 7)
    ("0.100 × 6.022", 0, [
        "0.100 ~~mol~~ × (6.022 × 10²³ molecules / 1 ~~mol~~) = 6.022 × 10²² molecules",
    ],
        "\"mol\" cancels. Three sig figs (limited by \"0.100\")."
    ),
    # PP8: 1.50 × 10²⁴ Ar → mol (idx 8)
    ("1.50 × 10²⁴", 0, [
        "1.50 × 10²⁴ ~~atoms~~ × (1 mol / 6.022 × 10²³ ~~atoms~~) = 2.49 mol",
    ],
        "\"atoms\" cancels, leaving \"mol\". Three sig figs."
    ),
    # PP9: 3.011 × 10²³ Cu atoms → mass (idx 9)
    ("n = 3.011", 0, [
        "n = 3.011 × 10²³ ~~atoms~~ × (1 mol / 6.022 × 10²³ ~~atoms~~) = 0.5000 mol",
        "m = 0.5000 ~~mol~~ × (63.55 g / 1 ~~mol~~) = 31.78 g → 31.8 g",
    ],
        "\"atoms\" cancels in step 1; \"mol\" cancels in step 2. Three sig figs (limited by \"63.55\" against 0.5000)."
    ),

    # ---- Mole Ratios from Formulas ----
    # PP11: H atoms in 0.50 mol C₆H₁₂O₆ (idx 11)
    ("0.50 × 12", 0, [
        "0.50 ~~mol C₆H₁₂O₆~~ × (12 mol H / 1 ~~mol C₆H₁₂O₆~~) = 6.0 mol H",
    ],
        "\"mol C₆H₁₂O₆\" cancels using the subscripts as the mole-ratio conversion factor. Two sig figs from \"0.50\"."
    ),
    # PP12: O atoms in 1.5 mol Mg(NO₃)₂ (idx 12)
    ("1.5 × 6", 0, [
        "1.5 ~~mol Mg(NO₃)₂~~ × (6 mol O / 1 ~~mol Mg(NO₃)₂~~) = 9.0 mol O",
    ],
        "\"mol Mg(NO₃)₂\" cancels. The 6 O atoms per formula unit come from 2 NO₃ groups × 3 O = 6. Two sig figs."
    ),
    # PP14: H atoms in 18.0 g H₂O (idx 14)
    ("n(H₂O) = 18.0", 0, [
        "n(H₂O) = 18.0 ~~g~~ × (1 mol / 18.02 ~~g~~) = 0.999 mol H₂O",
        "n(H) = 0.999 ~~mol H₂O~~ × (2 mol H / 1 ~~mol H₂O~~) = 1.998 mol H",
        "N(H) = 1.998 ~~mol~~ × (6.022 × 10²³ atoms / 1 ~~mol~~) = 1.20 × 10²⁴ atoms",
    ],
        "\"g\" cancels in step 1; \"mol H₂O\" cancels in step 2; \"mol\" cancels in step 3. Three sig figs (limited by \"18.0\")."
    ),

    # ---- Empirical and Molecular Formulas ----
    # PP15: 75.0% C, 25.0% H → CH₄ (idx 15)
    ("Per 100 g:", 0, [
        "n(C) = 75.0 ~~g C~~ × (1 mol C / 12.01 ~~g C~~) = 6.245 mol C",
        "n(H) = 25.0 ~~g H~~ × (1 mol H / 1.008 ~~g H~~) = 24.80 mol H",
        "Ratio H/C = 24.80 / 6.245 = 3.97 ≈ 4 → empirical formula CH₄",
    ],
        "\"g C\" and \"g H\" cancel in their respective conversions, leaving \"mol\". The integer ratio determines the empirical formula."
    ),
    # PP16: 27.3% C, 72.7% O → CO₂ (idx 16)
    ("27.3/12.01", 0, [
        "n(C) = 27.3 ~~g C~~ × (1 mol C / 12.01 ~~g C~~) = 2.273 mol C",
        "n(O) = 72.7 ~~g O~~ × (1 mol O / 16.00 ~~g O~~) = 4.544 mol O",
        "Ratio O/C = 4.544 / 2.273 = 2.00 → empirical formula CO₂",
    ],
        "\"g\" cancels in each conversion, leaving \"mol\". Three sig figs throughout."
    ),
    # PP18: CH₂O empirical, 180 g/mol → C₆H₁₂O₆ (idx 18)
    ("M(CH₂O) =", 0, [
        "M(CH₂O) = 12.01 + 2(1.008) + 16.00 = 30.03 g/mol",
        "n = (180 ~~g/mol~~) / (30.03 ~~g/mol~~) = 6 → multiply each subscript by 6",
        "Molecular formula: C₆H₁₂O₆ (glucose)",
    ],
        "\"g/mol\" cancels in the molar-mass ratio, giving a pure integer multiplier. The molecular formula is the empirical formula scaled up by n."
    ),
    # PP19: NO₂ empirical, M=92 → N₂O₄ (idx 19)
    ("M(NO₂) =", 0, [
        "M(NO₂) = 14.01 + 2(16.00) = 46.01 g/mol",
        "n = (92 ~~g/mol~~) / (46.01 ~~g/mol~~) = 2.00 → multiply subscripts by 2",
        "Molecular formula: N₂O₄ (dinitrogen tetroxide)",
    ],
        "\"g/mol\" cancels, leaving the integer multiplier."
    ),

    # ---- Combustion Analysis ----
    # PP20: 1.000 g hydrocarbon → 3.143 g CO₂ + 1.286 g H₂O → CH₂ (idx 20)
    ("g C = 3.143", 0, [
        "Mass C: 3.143 ~~g CO₂~~ × (12.01 g C / 44.01 ~~g CO₂~~) = 0.858 g C",
        "Mass H: 1.286 ~~g H₂O~~ × (2.016 g H / 18.02 ~~g H₂O~~) = 0.144 g H",
        "Sum = 0.858 + 0.144 = 1.002 g (≈ 1.000 g, consistent with C/H only)",
        "n(C) = 0.858 ~~g~~ × (1 mol / 12.01 ~~g~~) = 0.0714 mol",
        "n(H) = 0.144 ~~g~~ × (1 mol / 1.008 ~~g~~) = 0.143 mol",
        "Ratio H/C = 0.143 / 0.0714 = 2.00 → empirical formula CH₂",
    ],
        "\"g CO₂\" and \"g H₂O\" cancel in steps 1–2 (conversion factors built from molar masses); \"g\" cancels in steps 4–5. The ratio gives the empirical formula."
    ),
    # PP21: 0.500 g hydrocarbon → CH₂ (idx 21)
    ("C: 1.571", 0, [
        "Mass C: 1.571 ~~g CO₂~~ × (12.01 g C / 44.01 ~~g CO₂~~) = 0.4287 g C",
        "Mass H: 0.643 ~~g H₂O~~ × (2.016 g H / 18.02 ~~g H₂O~~) = 0.0719 g H",
        "n(C) = 0.4287 ~~g~~ × (1 mol / 12.01 ~~g~~) = 0.0357 mol",
        "n(H) = 0.0719 ~~g~~ × (1 mol / 1.008 ~~g~~) = 0.0714 mol",
        "Ratio H/C = 0.0714 / 0.0357 = 2.00 → empirical formula CH₂",
    ],
        "\"g CO₂\" and \"g H₂O\" cancel (mass-of-element / mass-of-product factors); \"g\" cancels in mole conversions."
    ),
    # PP22: 4.50 g C/H/O combustion → CH₂O (idx 22)
    ("C: 6.60", 0, [
        "Mass C: 6.60 ~~g CO₂~~ × (12.01 g C / 44.01 ~~g CO₂~~) = 1.802 g C",
        "Mass H: 2.70 ~~g H₂O~~ × (2.016 g H / 18.02 ~~g H₂O~~) = 0.302 g H",
        "Mass O = 4.50 − 1.802 − 0.302 = 2.396 g O (by difference)",
        "n(C) = 1.802 / 12.01 = 0.150 mol; n(H) = 0.302 / 1.008 = 0.300 mol; n(O) = 2.396 / 16.00 = 0.150 mol",
        "Ratio C : H : O = 0.150 : 0.300 : 0.150 = 1 : 2 : 1 → empirical formula CH₂O",
    ],
        "\"g CO₂\" and \"g H₂O\" cancel; oxygen is found by mass-balance (combustion can't measure O directly)."
    ),
    # PP24: 1.20 g C–H compound → 3.770 g CO₂ → %C (idx 24)
    ("g C = 3.770", 0, [
        "Mass C: 3.770 ~~g CO₂~~ × (12.01 g C / 44.01 ~~g CO₂~~) = 1.029 g C",
        "% C = (1.029 ~~g~~ C / 1.20 ~~g~~ sample) × 100% = 85.7%",
    ],
        "\"g CO₂\" cancels in step 1; \"g\" cancels in the percent ratio. Three sig figs."
    ),

    # ---- Purity ----
    # PP25: 4.50/5.00 g NaCl % (idx 25)
    ("4.50/5.00", 0, [
        "% purity = (4.50 ~~g~~ NaCl / 5.00 ~~g~~ sample) × 100% = 90.0%",
    ],
        "\"g\" cancels, leaving a dimensionless percentage."
    ),
    # PP26: 6.25/25.0 % Fe (idx 26)
    ("6.25/25.0", 0, [
        "% Fe = (6.25 ~~g~~ Fe / 25.0 ~~g~~ ore) × 100% = 25.0%",
    ],
        "\"g\" cancels. Three sig figs."
    ),
    # PP27: 196/200 mg drug % (idx 27)
    ("196/200", 0, [
        "% purity = (196 ~~mg~~ actual / 200 ~~mg~~ label) × 100% = 98.0%",
    ],
        "\"mg\" cancels."
    ),
    # PP28: 0.950 × 50.0 NaCl in 95% sample (idx 28)
    ("0.950 ×", 0, [
        "Mass NaCl = 50.0 ~~g~~ sample × (95.0 g NaCl / 100 ~~g~~ sample) = 47.5 g NaCl",
    ],
        "\"g sample\" cancels using the purity fraction as a conversion factor."
    ),
    # PP29: CaCO₃ % via CO₂ release (idx 29)
    ("n(CO₂) = 4.00", 0, [
        "n(CO₂) = 4.00 ~~g~~ × (1 mol / 44.01 ~~g~~) = 0.0909 mol CO₂",
        "n(CaCO₃) decomposed = 0.0909 ~~mol CO₂~~ × (1 mol CaCO₃ / 1 ~~mol CO₂~~) = 0.0909 mol CaCO₃",
        "Mass CaCO₃ = 0.0909 ~~mol~~ × (100.09 g / 1 ~~mol~~) = 9.10 g",
        "% CaCO₃ = (9.10 ~~g~~ / 10.0 ~~g~~) × 100% = 91.0%",
    ],
        "\"g\" cancels in mole conversions; \"mol CO₂\" cancels via the 1:1 stoichiometry; \"g\" cancels in the percent ratio."
    ),

    # ---- Mixed (after Mole Ratios first sub-section) ----
    # PP30: 40/12.01 → C₆H₁₂O₆ (idx 30)
    ("40.00/12.01", 0, [
        "n(C) = 40.00 ~~g C~~ × (1 mol / 12.011 ~~g C~~) = 3.331 mol C",
        "n(H) = 6.71 ~~g H~~ × (1 mol / 1.008 ~~g H~~) = 6.66 mol H",
        "n(O) = 53.29 ~~g O~~ × (1 mol / 16.00 ~~g O~~) = 3.331 mol O",
        "Ratio C:H:O = 3.331 : 6.66 : 3.331 = 1 : 2 : 1 → CH₂O",
        "M(CH₂O) = 30.03 g/mol; n = 180.16 ~~g/mol~~ / 30.03 ~~g/mol~~ = 6.00 → C₆H₁₂O₆",
    ],
        "\"g\" cancels in each mole conversion; \"g/mol\" cancels in the molecular-formula ratio. The empirical-to-molecular step multiplies subscripts by n = 6."
    ),
    # PP31: atoms in 1.0 g C-12 (idx 31)
    ("1.0/12.00", 0, [
        "n = 1.0 ~~g~~ × (1 mol / 12.00 ~~g~~) = 0.0833 mol",
        "N = 0.0833 ~~mol~~ × (6.022 × 10²³ atoms / 1 ~~mol~~) = 5.0 × 10²² atoms",
    ],
        "\"g\" cancels in step 1; \"mol\" cancels in step 2. Two sig figs (limited by \"1.0\")."
    ),
    # PP32: 8.00/25.0 = 32% (idx 32)
    ("8.00/25.0", 0, [
        "% O = (8.00 ~~g~~ O / 25.0 ~~g~~ sample) × 100% = 32.0%",
    ],
        "\"g\" cancels. Three sig figs."
    ),
    # PP33: 2.50 × 10²³ N₂ → mass (idx 33)
    ("n = 2.50", 0, [
        "n = 2.50 × 10²³ ~~molecules~~ × (1 mol / 6.022 × 10²³ ~~molecules~~) = 0.4151 mol",
        "Mass = 0.4151 ~~mol~~ × (28.02 g / 1 ~~mol~~) = 11.63 g",
    ],
        "\"molecules\" cancels in step 1; \"mol\" cancels in step 2."
    ),
    # PP34: H in 0.20 mol (NH₄)₂CO₃ (idx 34)
    ("8 H per", 0, [
        "0.20 ~~mol (NH₄)₂CO₃~~ × (8 mol H / 1 ~~mol (NH₄)₂CO₃~~) = 1.6 mol H",
    ],
        "\"mol (NH₄)₂CO₃\" cancels using the subscripts (2 N atoms × 4 H = 8 H per formula unit). Two sig figs."
    ),

    # ---- Second Mixed block (continuing) ----
    # PP37: %N in N₂O (idx 37)
    ("N: 2(14.007)", 0, [
        "M(N₂O) = 2(14.007) + 15.999 = 44.013 g/mol",
        "% N = (2 × 14.007 ~~g~~ N / 44.013 ~~g~~ N₂O) × 100% = 63.65%",
    ],
        "\"g\" cancels in the mass ratio. Four sig figs."
    ),
    # PP38: %elements in H₂O (idx 38)
    ("H: 2(1.008)", 0, [
        "M(H₂O) = 2(1.008) + 15.999 = 18.015 g/mol",
        "% H = (2.016 ~~g~~ H / 18.015 ~~g~~ H₂O) × 100% = 11.19%",
        "% O = (15.999 ~~g~~ O / 18.015 ~~g~~ H₂O) × 100% = 88.81%",
    ],
        "\"g\" cancels in each mass ratio. The two percentages sum to 100.00% as expected."
    ),
    # PP39: 36.5 g HCl → mol (idx 39)
    ("36.5 / 36.46", 0, [
        "n = 36.5 ~~g~~ × (1 mol / 36.46 ~~g~~) = 1.00 mol",
    ],
        "\"g\" cancels. Three sig figs."
    ),
    # PP40: 0.250 mol KMnO₄ → g (idx 40)
    ("Molar mass = 39.10", 0, [
        "M(KMnO₄) = 39.10 + 54.94 + 4(16.00) = 158.04 g/mol",
        "Mass = 0.250 ~~mol~~ × (158.04 g / 1 ~~mol~~) = 39.5 g",
    ],
        "\"mol\" cancels. Three sig figs (limited by \"0.250\")."
    ),
    # PP41: 5.00 g Fe → atoms (idx 41)
    ("5.00 / 55.845", 0, [
        "n = 5.00 ~~g~~ × (1 mol / 55.845 ~~g~~) = 0.0895 mol",
        "N = 0.0895 ~~mol~~ × (6.022 × 10²³ atoms / 1 ~~mol~~) = 5.39 × 10²² atoms",
    ],
        "\"g\" cancels in step 1; \"mol\" cancels in step 2."
    ),
    # PP43: 4.50 × 10²¹ glucose molecules → g (idx 43)
    ("Moles = 4.50", 0, [
        "n = 4.50 × 10²¹ ~~molecules~~ × (1 mol / 6.022 × 10²³ ~~molecules~~) = 7.473 × 10⁻³ mol",
        "Mass = 7.473 × 10⁻³ ~~mol~~ × (180.16 g / 1 ~~mol~~) = 1.346 g → 1.35 g",
    ],
        "\"molecules\" cancels in step 1; \"mol\" cancels in step 2. Three sig figs."
    ),
    # PP44: O in 2.00 mol CO₂ (idx 44)
    ("2.00 mol", 0, [
        "2.00 ~~mol CO₂~~ × (2 mol O / 1 ~~mol CO₂~~) = 4.00 mol O",
    ],
        "\"mol CO₂\" cancels via the subscript-based mole ratio. Three sig figs."
    ),
    # PP45: C in 0.500 mol glucose (idx 45)
    ("0.500 × 6", 0, [
        "0.500 ~~mol C₆H₁₂O₆~~ × (6 mol C / 1 ~~mol C₆H₁₂O₆~~) = 3.00 mol C",
    ],
        "\"mol C₆H₁₂O₆\" cancels via the formula's 6:1 carbon ratio."
    ),
    # PP46: H atoms in 1.00 g CH₄ (idx 46)
    ("Moles CH₄ =", 0, [
        "n(CH₄) = 1.00 ~~g~~ × (1 mol / 16.04 ~~g~~) = 0.0623 mol CH₄",
        "n(H) = 0.0623 ~~mol CH₄~~ × (4 mol H / 1 ~~mol CH₄~~) = 0.249 mol H",
        "N(H) = 0.249 ~~mol~~ × (6.022 × 10²³ atoms / 1 ~~mol~~) = 1.50 × 10²³ atoms H",
    ],
        "Three cancellations: \"g\" (step 1), \"mol CH₄\" (step 2), \"mol\" (step 3). Three sig figs."
    ),
    # PP47: Na, O, S → Na₂SO₃ (idx 47)
    ("36.5 g Na/22.99", 0, [
        "n(Na) = 36.5 ~~g~~ × (1 mol / 22.99 ~~g~~) = 1.587 mol",
        "n(O) = 38.4 ~~g~~ × (1 mol / 16.00 ~~g~~) = 2.40 mol",
        "n(S) = 25.1 ~~g~~ × (1 mol / 32.06 ~~g~~) = 0.7829 mol",
        "Divide by smallest (0.7829): Na 2.03 ≈ 2; O 3.07 ≈ 3; S 1.00 → empirical formula Na₂SO₃",
    ],
        "\"g\" cancels in each mass-to-mole conversion. The smallest mole count sets the divisor for the integer ratio."
    ),
    # PP48: 25.94% N, 74.06% O → N₂O₅ (idx 48)
    ("N: 25.94", 0, [
        "n(N) = 25.94 ~~g~~ × (1 mol / 14.007 ~~g~~) = 1.852 mol",
        "n(O) = 74.06 ~~g~~ × (1 mol / 16.00 ~~g~~) = 4.629 mol",
        "Divide by smallest: N 1.000; O 2.50 → multiply by 2 → empirical formula N₂O₅",
    ],
        "\"g\" cancels. The 2.5 ratio is doubled to clear the half."
    ),
    # PP50: 92.3% C, 7.7% H, M=78.0 → C₆H₆ (idx 50)
    ("C: 92.3/12.011", 0, [
        "n(C) = 92.3 ~~g~~ × (1 mol / 12.011 ~~g~~) = 7.685 mol",
        "n(H) = 7.7 ~~g~~ × (1 mol / 1.008 ~~g~~) = 7.639 mol",
        "Divide by smallest: C 1.006 ≈ 1; H 1.000 → empirical CH (mass 13.019)",
        "n = 78.0 ~~g/mol~~ / 13.019 ~~g/mol~~ = 6.0 → molecular formula C₆H₆",
    ],
        "\"g\" cancels in mole conversions; \"g/mol\" cancels in the empirical-to-molecular ratio."
    ),
    # PP51: 0.500 g hydrocarbon → CH₂ (idx 51)
    ("Mass C = 1.65", 0, [
        "Mass C: 1.65 ~~g CO₂~~ × (12.011 g C / 44.01 ~~g CO₂~~) = 0.450 g C",
        "Mass H: 0.677 ~~g H₂O~~ × (2.016 g H / 18.015 ~~g H₂O~~) = 0.0758 g H",
        "n(C) = 0.450 / 12.011 = 0.0375 mol; n(H) = 0.0758 / 1.008 = 0.0752 mol",
        "Ratio H/C = 0.0752 / 0.0375 = 2.0 → empirical formula CH₂",
    ],
        "\"g CO₂\" and \"g H₂O\" cancel using mass-of-element-per-mass-of-product factors."
    ),
    # PP52: Empirical CH₂, M=56.1 → C₄H₈ (idx 52)
    ("Empirical mass = 14.027", 0, [
        "M(CH₂) = 12.011 + 2(1.008) = 14.027 g/mol",
        "n = 56.1 ~~g/mol~~ / 14.027 ~~g/mol~~ = 4.0 → molecular formula C₄H₈",
    ],
        "\"g/mol\" cancels in the molar-mass ratio; multiply each subscript by n = 4."
    ),
    # PP53: 5.00 g fertilizer 18% N (idx 53)
    ("5.00 × 0.180", 0, [
        "Mass N = 5.00 ~~g~~ fertilizer × (18.0 g N / 100 ~~g~~ fertilizer) = 0.900 g N",
    ],
        "\"g fertilizer\" cancels using the percent-by-mass factor. Three sig figs."
    ),
    # PP54: 50.0 g rock 22% Fe₂O₃ → Fe (idx 54)
    ("Mass Fe₂O₃ =", 0, [
        "Mass Fe₂O₃ = 50.0 ~~g~~ rock × (22.0 g Fe₂O₃ / 100 ~~g~~ rock) = 11.0 g Fe₂O₃",
        "n(Fe₂O₃) = 11.0 ~~g~~ × (1 mol / 159.69 ~~g~~) = 0.0689 mol Fe₂O₃",
        "n(Fe) = 0.0689 ~~mol Fe₂O₃~~ × (2 mol Fe / 1 ~~mol Fe₂O₃~~) = 0.138 mol Fe",
        "Mass Fe = 0.138 ~~mol~~ × (55.85 g / 1 ~~mol~~) = 7.69 g Fe",
    ],
        "Four cancellations: \"g rock\" (purity), \"g\" (molar mass), \"mol Fe₂O₃\" (subscript), \"mol\" (molar mass). Three sig figs."
    ),
    # PP55: 5.00 × 10²² Cu atoms → mass (idx 55)
    ("Moles = 5.00", 0, [
        "n = 5.00 × 10²² ~~atoms~~ × (1 mol / 6.022 × 10²³ ~~atoms~~) = 0.0830 mol",
        "Mass = 0.0830 ~~mol~~ × (63.55 g / 1 ~~mol~~) = 5.28 g",
    ],
        "\"atoms\" cancels in step 1; \"mol\" cancels in step 2."
    ),
    # PP56: 7.50 g NaCl → formula units (idx 56)
    ("Moles = 7.50", 0, [
        "n = 7.50 ~~g~~ × (1 mol / 58.44 ~~g~~) = 0.1283 mol",
        "N = 0.1283 ~~mol~~ × (6.022 × 10²³ formula units / 1 ~~mol~~) = 7.73 × 10²² formula units",
    ],
        "\"g\" cancels in step 1; \"mol\" cancels in step 2. Three sig figs."
    ),
    # PP58: %water in CuSO₄·5H₂O (idx 58)
    ("90.075 / 249.69", 0, [
        "% H₂O = (5 × 18.015 ~~g~~ H₂O / 249.69 ~~g~~ CuSO₄·5H₂O) × 100% = 36.07%",
    ],
        "\"g\" cancels in the mass ratio. Five waters of hydration contribute 90.075 g/mol."
    ),
    # PP59: N in 100.0 g urea (idx 59)
    ("Molar mass urea =", 0, [
        "M(urea) = 2(14.007) + 4(1.008) + 12.011 + 16.00 = 60.06 g/mol",
        "n(urea) = 100.0 ~~g~~ × (1 mol / 60.06 ~~g~~) = 1.665 mol urea",
        "n(N) = 1.665 ~~mol urea~~ × (2 mol N / 1 ~~mol urea~~) = 3.330 mol N",
    ],
        "\"g\" cancels in step 2; \"mol urea\" cancels in step 3 via the subscript ratio."
    ),

    # ---- Multi-Concept Problems ----
    # MC1: MgSO₄·xH₂O hydrate (idx 60, original is multi-paragraph: consume_after = 2)
    ("100.0 − 51.2", 2, [
        "Mass anhydrous MgSO₄ = 100.0 g − 51.2 g = 48.8 g",
        "n(MgSO₄) = 48.8 ~~g~~ × (1 mol / 120.37 ~~g~~) = 0.4054 mol",
        "n(H₂O) = 51.2 ~~g~~ × (1 mol / 18.015 ~~g~~) = 2.842 mol",
        "Ratio = 2.842 / 0.4054 = 7.01 ≈ 7 → formula MgSO₄·7H₂O (Epsom salt)",
    ],
        "\"g\" cancels in each mole conversion; the integer ratio gives x in the hydrate formula."
    ),
    # MC2: Caffeine (idx 61, multi-paragraph: consume_after = 2)
    ("8(12.011)", 2, [
        "M(C₈H₁₀N₄O₂) = 8(12.011) + 10(1.008) + 4(14.007) + 2(15.999) = 194.19 g/mol",
        "% N = (4 × 14.007 ~~g~~ N / 194.19 ~~g~~ caffeine) × 100% = 28.85%",
        "n(caffeine) = 100.0 × 10⁻³ ~~g~~ × (1 mol / 194.19 ~~g~~) = 5.150 × 10⁻⁴ mol",
        "n(N) = 5.150 × 10⁻⁴ ~~mol caffeine~~ × (4 mol N / 1 ~~mol caffeine~~) = 2.060 × 10⁻³ mol N",
        "N atoms = 2.060 × 10⁻³ ~~mol~~ × (6.022 × 10²³ atoms / 1 ~~mol~~) = 1.241 × 10²¹ atoms",
    ],
        "Cancellations chain: \"g\" → \"g\" → \"mol caffeine\" → \"mol\". Four sig figs throughout."
    ),
    # MC3: K₂Cr₂O₇ (idx 62, multi-paragraph: consume_after = 1)
    ("K: 26.5/39.10", 1, [
        "n(K) = 26.5 ~~g~~ × (1 mol / 39.10 ~~g~~) = 0.6778 mol",
        "n(Cr) = 35.4 ~~g~~ × (1 mol / 52.00 ~~g~~) = 0.681 mol",
        "n(O) = 38.1 ~~g~~ × (1 mol / 16.00 ~~g~~) = 2.381 mol",
        "Divide by 0.678: K 1.00; Cr 1.00; O 3.51 → multiply by 2 → K₂Cr₂O₇",
        "Empirical mass = 294.18 g/mol; n = 294.2 / 294.18 ≈ 1 → molecular formula = K₂Cr₂O₇",
    ],
        "\"g\" cancels in mole conversions; the empirical-to-molecular ratio is ~1, so molecular formula equals empirical."
    ),
    # MC4: Vitamin C tablet (idx 63, multi-paragraph: consume_after = 2)
    ("5.00/250", 2, [
        "% vit C = (5.00 ~~mg~~ C₆H₈O₆ / 250 ~~mg~~ tablet) × 100% = 2.00%",
        "n(vit C) = 5.00 × 10⁻³ ~~g~~ × (1 mol / 176.12 ~~g~~) = 2.839 × 10⁻⁵ mol",
        "n(C) = 2.839 × 10⁻⁵ ~~mol C₆H₈O₆~~ × (6 mol C / 1 ~~mol C₆H₈O₆~~) = 1.703 × 10⁻⁴ mol C",
        "C atoms = 1.703 × 10⁻⁴ ~~mol~~ × (6.022 × 10²³ atoms / 1 ~~mol~~) = 1.026 × 10²⁰ atoms",
    ],
        "\"mg\" cancels in the percentage; \"g\" / \"mol C₆H₈O₆\" / \"mol\" cancel along the conversion chain."
    ),
    # MC5: CuSO₄·xH₂O loss → x = 5 (idx 64)
    ("Anhydrous CuSO₄", 0, [
        "Anhydrous CuSO₄ mass = 4.00 − 1.45 = 2.55 g",
        "n(CuSO₄) = 2.55 ~~g~~ × (1 mol / 159.61 ~~g~~) = 0.01598 mol",
        "n(H₂O) = 1.45 ~~g~~ × (1 mol / 18.015 ~~g~~) = 0.0805 mol",
        "Ratio = 0.0805 / 0.01598 = 5.04 ≈ 5 → x = 5; formula CuSO₄·5H₂O",
    ],
        "\"g\" cancels in mole conversions; the mole ratio gives x."
    ),
    # MC6: FeSO₄ in cereal (idx 65)
    ("Moles Fe =", 0, [
        "n(Fe) = 18.0 × 10⁻³ ~~g~~ × (1 mol / 55.85 ~~g~~) = 3.222 × 10⁻⁴ mol Fe",
        "n(FeSO₄) = 3.222 × 10⁻⁴ ~~mol Fe~~ × (1 mol FeSO₄ / 1 ~~mol Fe~~) = 3.222 × 10⁻⁴ mol",
        "Mass FeSO₄ = 3.222 × 10⁻⁴ ~~mol~~ × (151.91 g / 1 ~~mol~~) = 0.0490 g = 49.0 mg",
    ],
        "\"g\" / \"mol Fe\" / \"mol\" cancel in turn. The 1:1 mole ratio comes from the formula FeSO₄ (one Fe per formula unit)."
    ),
    # MC7: 40/6.71/53.29 → C₆H₁₂O₆ (idx 66)
    ("Empirical: per 100 g", 0, [
        "n(C) = 40.00 ~~g~~ × (1 mol / 12.011 ~~g~~) = 3.330 mol",
        "n(H) = 6.71 ~~g~~ × (1 mol / 1.008 ~~g~~) = 6.657 mol",
        "n(O) = 53.29 ~~g~~ × (1 mol / 16.00 ~~g~~) = 3.331 mol",
        "Divide by 3.330: 1 : 2 : 1 → empirical formula CH₂O (mass 30.03 g/mol)",
        "n = 180.18 ~~g/mol~~ / 30.03 ~~g/mol~~ = 6.00 → molecular formula C₆H₁₂O₆",
    ],
        "\"g\" cancels in mole conversions; \"g/mol\" cancels in the empirical-to-molecular ratio."
    ),
    # MC8: butane combustion (idx 67, multi-paragraph: consume_after = 3)
    ("Combustion:", 3, [
        "Balanced combustion: C₄H₁₀ + 13/2 O₂ → 4 CO₂ + 5 H₂O",
        "n(CO₂) = 1.00 ~~mol C₄H₁₀~~ × (4 mol CO₂ / 1 ~~mol C₄H₁₀~~) = 4.00 mol CO₂",
        "Mass CO₂ = 4.00 ~~mol~~ × (44.01 g / 1 ~~mol~~) = 176.0 g",
        "Molecules CO₂ = 4.00 ~~mol~~ × (6.022 × 10²³ molecules / 1 ~~mol~~) = 2.41 × 10²⁴ molecules",
    ],
        "Three cancellations: \"mol C₄H₁₀\" (stoichiometric ratio), \"mol\" (molar mass), \"mol\" (Avogadro's number)."
    ),
]


if __name__ == "__main__":
    n = apply_rewrites(
        "Chapter_08_Mole_Concept_and_Chemical_Formulas.docx",
        REWRITES,
        skip_indices=SKIP,
    )
    print(f"Chapter 8: applied {n} rewrites.")
