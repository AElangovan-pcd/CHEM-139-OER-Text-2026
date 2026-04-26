"""Apply factor-label strikethrough to Chapter 8 Worked Examples.

Targets the math-chain Step paragraphs in EXAMPLE 8.4 through 8.10 and
8.13 / 8.14 — the ones with genuine unit cancellation. Examples 8.1-8.3
(formula-mass additions), 8.11-8.12 (compact mol calculations), and 8.15
(trivial n=1) are left as-is because their arithmetic carries the same
unit throughout rather than converting between units.
"""
from rewrite_engine_examples import apply_example_rewrites

REWRITES = [
    # EX 8.5 Step 1: 5.00 g C -> mol
    ("Step 1 — Convert grams to moles using molar mass: 5.00 g",
     "Step 1 — Convert grams to moles using molar mass: 5.00 ~~g~~ × (1 mol / 12.011 ~~g~~) = 0.4163 mol.",
     "\"g\" cancels via the inverted molar mass, leaving \"mol\". Three sig figs from \"5.00\"."),

    # EX 8.5 Step 2: 0.4163 mol -> atoms
    ("Step 2 — Convert moles to atoms using NA: 0.4163 mol",
     "Step 2 — Convert moles to atoms using NA: 0.4163 ~~mol~~ × (6.022 × 10²³ atoms / 1 ~~mol~~) = 2.507 × 10²³ atoms.",
     "\"mol\" cancels via Avogadro's number, leaving \"atoms\"."),

    # EX 8.6 Step 1: 4.50e22 H2O molecules -> mol
    ("Step 1 — Moles: 4.50",
     "Step 1 — Moles: 4.50 × 10²² ~~molecules~~ × (1 mol / 6.022 × 10²³ ~~molecules~~) = 7.473 × 10⁻² mol.",
     "\"molecules\" cancels via Avogadro's number (inverted), leaving \"mol\"."),

    # EX 8.6 Step 2: 7.473e-2 mol H2O -> mass
    ("Step 2 — Mass: 7.473",
     "Step 2 — Mass: 7.473 × 10⁻² ~~mol~~ × (18.015 g / 1 ~~mol~~) = 1.347 g.",
     "\"mol\" cancels via the molar mass of H₂O, leaving \"g\"."),

    # EX 8.7 Step 1: 25.0 g sample × 0.950 purity
    ("Step 1 — Mass of pure NaCl = 25.0",
     "Step 1 — Mass of pure NaCl = 25.0 ~~g~~ sample × (95.0 g NaCl / 100 ~~g~~ sample) = 23.75 g NaCl.",
     "\"g sample\" cancels via the purity-fraction conversion factor, leaving \"g NaCl\"."),

    # EX 8.7 Step 2: 23.75 g NaCl -> mol
    ("Step 2 — Moles = 23.75",
     "Step 2 — Moles = 23.75 ~~g~~ × (1 mol / 58.44 ~~g~~) = 0.4063 mol.",
     "\"g\" cancels via the inverted molar mass of NaCl."),

    # EX 8.8 Step 2: per-element mol conversions (composite)
    ("Step 2 — Convert to moles: C: 40.0",
     "Step 2 — Convert to moles. C: 40.0 ~~g~~ × (1 mol / 12.011 ~~g~~) = 3.330 mol; H: 6.71 ~~g~~ × (1 mol / 1.008 ~~g~~) = 6.657 mol; O: 53.3 ~~g~~ × (1 mol / 15.999 ~~g~~) = 3.331 mol.",
     "\"g\" cancels in each element's mass-to-mole conversion, leaving \"mol\". The mole values then go into the Step-3 ratio test."),

    # EX 8.10 Step 1: mass of C from CO2
    ("Step 1 — All C in the original sample is now in CO₂. Mass of C = 8.92",
     "Step 1 — All C in the original sample is now in CO₂. Mass of C = 8.92 ~~g CO₂~~ × (12.011 g C / 44.01 ~~g CO₂~~) = 2.434 g C.",
     "\"g CO₂\" cancels via the carbon-mass-per-formula-mass factor (12.011 g C in every 44.01 g of CO₂), leaving \"g C\"."),

    # EX 8.10 Step 2: mass of H from H2O
    ("Step 2 — All H is now in H₂O. Mass of H = 3.65",
     "Step 2 — All H is now in H₂O. Mass of H = 3.65 ~~g H₂O~~ × (2 × 1.008 g H / 18.015 ~~g H₂O~~) = 0.4084 g H.",
     "\"g H₂O\" cancels via the hydrogen-mass-per-formula-mass factor (2 × 1.008 g H in every 18.015 g of H₂O), leaving \"g H\"."),

    # EX 8.13 Step 2: n = 180.16 / 30.026 (g/mol cancellation)
    ("Step 2 — n = 180.16 / 30.026",
     "Step 2 — n = (180.16 ~~g/mol~~) / (30.026 ~~g/mol~~) = 6.000.",
     "\"g/mol\" cancels in the molar-mass ratio, giving a pure integer multiplier. The molecular formula is the empirical formula scaled up by n = 6."),

    # EX 8.14 Step 2: n = 92.02 / 46.005
    ("Step 2 — n = 92.02 / 46.005",
     "Step 2 — n = (92.02 ~~g/mol~~) / (46.005 ~~g/mol~~) = 2.00.",
     "\"g/mol\" cancels in the molar-mass ratio. Multiply each subscript in NO₂ by 2 → N₂O₄."),
]


if __name__ == "__main__":
    n = apply_example_rewrites(
        "Chapter_08_Mole_Concept_and_Chemical_Formulas.docx",
        REWRITES,
    )
    print(f"Chapter 8 Worked Examples: applied {n} rewrites.")
