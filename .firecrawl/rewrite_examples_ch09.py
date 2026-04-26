"""Apply factor-label strikethrough to Chapter 9 Worked Examples.

Targets math-chain Step paragraphs in EXAMPLE 9.4 through 9.13. Examples
9.1-9.3 are equation balancing (no unit cancellation) and 9.10-9.12
share their math with 9.11/9.13 below. We rewrite the Steps that
demonstrate genuine factor-label cancellation in stoichiometry.
"""
from rewrite_engine_examples import apply_example_rewrites

REWRITES = [
    # EX 9.4 Step 3: 5.00 mol H2 -> mol O2
    ("Step 3 — 5.00 mol H₂",
     "Step 3 — 5.00 ~~mol H₂~~ × (1 mol O₂ / 2 ~~mol H₂~~) = 2.50 mol O₂.",
     "\"mol H₂\" cancels via the 2:1 stoichiometric ratio, leaving \"mol O₂\"."),

    # EX 9.5 Step 2: 0.250 mol H2 × (mol H2O/mol H2)
    ("Step 2 — 0.250 mol H₂ × 1",
     "Step 2 — 0.250 ~~mol H₂~~ × (2 mol H₂O / 2 ~~mol H₂~~) = 0.250 mol H₂O.",
     "\"mol H₂\" cancels via the 2:2 stoichiometric ratio (effectively 1:1)."),

    # EX 9.5 Step 3: 0.250 mol H2O -> mass
    ("Step 3 — Mass: 0.250 × 18.015",
     "Step 3 — Mass = 0.250 ~~mol~~ × (18.015 g / 1 ~~mol~~) = 4.50 g H₂O.",
     "\"mol\" cancels via the molar mass of water, leaving \"g\"."),

    # EX 9.6 Step 1: 8.00 g CH4 -> mol
    ("Step 1 — Moles CH₄ = 8.00",
     "Step 1 — Moles CH₄ = 8.00 ~~g~~ × (1 mol / 16.04 ~~g~~) = 0.4988 mol CH₄.",
     "\"g\" cancels via the inverted molar mass of CH₄."),

    # EX 9.6 Step 3: 0.4988 mol CO2 -> mass
    ("Step 3 — Mass CO₂ = 0.4988 × 44.01",
     "Step 3 — Mass CO₂ = 0.4988 ~~mol~~ × (44.01 g / 1 ~~mol~~) = 21.95 g.",
     "\"mol\" cancels via the molar mass of CO₂."),

    # EX 9.7 Step 1: 100.0 g NH3 -> mol
    ("Step 1 — Moles NH₃ = 100.0",
     "Step 1 — Moles NH₃ = 100.0 ~~g~~ × (1 mol / 17.03 ~~g~~) = 5.872 mol NH₃.",
     "\"g\" cancels via the inverted molar mass."),

    # EX 9.7 Step 2: 5.872 mol NH3 -> mol N2
    ("Step 2 — Mole ratio N₂ / NH₃ = 1/2",
     "Step 2 — n(N₂) = 5.872 ~~mol NH₃~~ × (1 mol N₂ / 2 ~~mol NH₃~~) = 2.936 mol N₂.",
     "\"mol NH₃\" cancels via the 1:2 stoichiometric ratio (N₂ + 3 H₂ → 2 NH₃)."),

    # EX 9.7 Step 3: 2.936 mol N2 -> mass
    ("Step 3 — Mass N₂ = 2.936",
     "Step 3 — Mass N₂ = 2.936 ~~mol~~ × (28.014 g / 1 ~~mol~~) = 82.26 g → 82.3 g.",
     "\"mol\" cancels via the molar mass of N₂."),

    # EX 9.8 Step 2: 50.0 g C3H8 -> mol
    ("Step 2 — Moles C₃H₈ = 50.0",
     "Step 2 — Moles C₃H₈ = 50.0 ~~g~~ × (1 mol / 44.10 ~~g~~) = 1.134 mol.",
     "\"g\" cancels via the inverted molar mass of propane."),

    # EX 9.8 Step 3: 1.134 mol C3H8 -> mol O2
    ("Step 3 — Mole ratio O₂ / C₃H₈ = 5",
     "Step 3 — n(O₂) = 1.134 ~~mol C₃H₈~~ × (5 mol O₂ / 1 ~~mol C₃H₈~~) = 5.669 mol O₂.",
     "\"mol C₃H₈\" cancels via the 5:1 stoichiometric ratio."),

    # EX 9.8 Step 4: 5.669 mol O2 -> mass
    ("Step 4 — Mass O₂ = 5.669",
     "Step 4 — Mass O₂ = 5.669 ~~mol~~ × (31.998 g / 1 ~~mol~~) = 181.4 g.",
     "\"mol\" cancels via the molar mass of O₂."),

    # EX 9.9 Step 1: 5.00 g H2 -> mol
    ("Step 1 — Moles H₂ = 5.00",
     "Step 1 — Moles H₂ = 5.00 ~~g~~ × (1 mol / 2.016 ~~g~~) = 2.480 mol H₂.",
     "\"g\" cancels via the inverted molar mass of H₂."),

    # EX 9.12 Step 2: 0.357 mol N2 -> mol NH3
    ("Step 2 — Mole ratio NH₃ / N₂ = 2",
     "Step 2 — n(NH₃) = 0.357 ~~mol N₂~~ × (2 mol NH₃ / 1 ~~mol N₂~~) = 0.714 mol.",
     "\"mol N₂\" cancels via the 2:1 stoichiometric ratio."),

    # EX 9.12 Step 3: 0.714 mol NH3 -> mass
    ("Step 3 — Mass NH₃ = 0.714",
     "Step 3 — Mass NH₃ = 0.714 ~~mol~~ × (17.031 g / 1 ~~mol~~) = 12.16 g.",
     "\"mol\" cancels via the molar mass of NH₃."),
]


if __name__ == "__main__":
    n = apply_example_rewrites(
        "Chapter_09_Chemical_Calculations_and_Equations.docx",
        REWRITES,
    )
    print(f"Chapter 9 Worked Examples: applied {n} rewrites.")
