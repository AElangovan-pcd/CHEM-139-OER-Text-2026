"""Apply factor-label strikethrough to Chapter 2 Worked Examples.

Targets the "Step N —" math-chain paragraph in each EXAMPLE 2.X block.
EX 2.8 (percent error) and EX 2.9 (temperature conversion) use formulas
rather than factor-label conversions, so they're left alone.
"""
from rewrite_engine_examples import apply_example_rewrites

REWRITES = [
    # EX 2.1: 4.50 km -> m
    ("Step 3 — Set up: 4.50 km",
     "Step 3 — Set up: 4.50 ~~km~~ × (10³ m / 1 ~~km~~) = 4.50 × 10³ m.",
     "Units cancel as marked: \"km\" cancels against the conversion factor, leaving \"m\". Three sig figs from \"4.50 km\"."),

    # EX 2.2: 75.0 ft -> in
    ("Step 3 — 75.0 ft",
     "Step 3 — 75.0 ~~ft~~ × (12 in / 1 ~~ft~~) = 900. in (the period denotes the exact 3-sig-fig result).",
     "\"ft\" cancels, leaving \"in\". The 12 in/ft factor is exact, so the input \"75.0 ft\" sets the 3 sig figs."),

    # EX 2.3: 165 lb -> kg
    ("Step 3 — 165 lb",
     "Step 3 — 165 ~~lb~~ × (453.59 ~~g~~ / 1 ~~lb~~) × (1 kg / 10³ ~~g~~) = 74.84 kg.",
     "Two cancellations: \"lb\" in step 1, \"g\" in step 2. Three sig figs from \"165 lb\" govern the answer."),

    # EX 2.4: 65.0 mi/h -> m/s
    ("Step 3 — 65.0 (mi/h)",
     "Step 3 — 65.0 ~~mi~~/~~h~~ × (1.609 ~~km~~ / 1 ~~mi~~) × (10³ m / 1 ~~km~~) × (1 ~~h~~ / 60 ~~min~~) × (1 ~~min~~ / 60 s) = ?",
     "Four pairs cancel: \"mi\", \"km\", \"h\", \"min\" — leaving \"m\" in the numerator and \"s\" in the denominator (m/s)."),

    # EX 2.5: 250.0 g Hg -> mL
    ("Step 3 — V = 250.0 g",
     "Step 3 — V = 250.0 ~~g~~ × (1 mL / 13.546 ~~g~~) = 18.456 mL.",
     "\"g\" cancels via the inverted density (used to convert mass to volume). Four sig figs throughout."),

    # EX 2.6: 250. mL ethanol -> g
    ("Step 3 — m = 250. mL",
     "Step 3 — m = 250. ~~mL~~ × (0.789 g / 1 ~~mL~~) = 197.25 g.",
     "\"mL\" cancels via the density factor. Three sig figs from \"250.\" (the trailing decimal makes the zero significant) and \"0.789\"."),

    # EX 2.7: 90.0 mg dose -> mL
    ("Step 3 — 90.0 mg ×",
     "Step 3 — 90.0 ~~mg~~ × (5.00 mL / 125 ~~mg~~) = 3.60 mL.",
     "\"mg\" cancels via the dose-concentration factor (125 mg per 5.00 mL inverted). Three sig figs."),
]


if __name__ == "__main__":
    n = apply_example_rewrites(
        "Chapter_02_Unit_Systems_and_Dimensional_Analysis.docx",
        REWRITES,
    )
    print(f"Chapter 2 Worked Examples: applied {n} rewrites.")
