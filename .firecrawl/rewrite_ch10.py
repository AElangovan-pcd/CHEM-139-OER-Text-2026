"""Apply factor-label rewrites to Chapter 10 (States of Matter) Solutions.

Chapter 10 is mostly conceptual: KMT postulates, IMF identification, vapor
pressure interpretation, anomalies of water. Only the specific-heat
arithmetic and the volume-expansion problem need factor-label treatment;
everything else is left untouched.
"""
from rewrite_engine import apply_rewrites

# Indices to LEAVE UNTOUCHED (0-based Solution paragraph order).
# Almost everything in this chapter is qualitative; we rewrite only the
# nine genuinely numerical Solutions.
REWRITE_INDICES = {15, 16, 17, 18, 45, 46, 48, 49, 55}
ALL_INDICES = set(range(60))
SKIP = ALL_INDICES - REWRITE_INDICES

REWRITES = [
    # idx 15: q = 100.0 × 4.184 × 50.0 (heat to warm water)
    ("q = m × c", 0, [
        "q = m × c × ΔT = 100.0 ~~g~~ × (4.184 J / 1 ~~g~~·~~°C~~) × 50.0 ~~°C~~ = 20,920 J = 20.9 kJ",
    ],
        "\"g\" cancels against the mass; \"°C\" cancels against the temperature change. Three sig figs throughout. Specific heat of water (4.184 J/g·°C) carries the units that make this calculation work."
    ),
    # idx 16: q = 50.0 × 0.897 × (-55) for aluminum cooling
    ("q = 50.0 × 0.897", 0, [
        "ΔT = T_f − T_i = 25.0 − 80.0 = −55.0 °C (negative because the metal cools)",
        "q = m × c × ΔT = 50.0 ~~g~~ × (0.897 J / 1 ~~g~~·~~°C~~) × (−55.0 ~~°C~~) = −2466.8 J ≈ −2.47 kJ",
    ],
        "\"g\" / \"°C\" cancel as in the standard q = mcΔT chain. Negative q means heat is released by the aluminum."
    ),
    # idx 17: water vs iron temperature rise from same heat input
    ("Water: ΔT", 0, [
        "Water: ΔT = q / (m × c) = 1000 ~~J~~ / (100 ~~g~~ × (4.184 ~~J~~ / 1 ~~g~~·°C)) = 1000 / 418.4 = 2.39 °C",
        "Iron:  ΔT = q / (m × c) = 1000 ~~J~~ / (100 ~~g~~ × (0.449 ~~J~~ / 1 ~~g~~·°C)) = 1000 / 44.9 = 22.27 °C",
    ],
        "\"J\" and \"g\" cancel in each calculation, leaving the temperature rise in °C. Water's higher specific heat (4.184 vs 0.449 J/g·°C) means the same 1000 J raises water's temperature ~10× less than iron's — the basis of water as a thermal buffer."
    ),
    # idx 18: 1.00 kg water → ice volume increase
    ("Volume of liquid", 0, [
        "Volume of liquid water = 1.00 ~~kg~~ × (1000 ~~g~~ / 1 ~~kg~~) × (1 mL / 1.000 ~~g~~) = 1000 mL",
        "Volume of ice = 1.00 ~~kg~~ × (1000 ~~g~~ / 1 ~~kg~~) × (1 mL / 0.917 ~~g~~) = 1090.5 mL",
        "Increase = 1090.5 − 1000 = 90.5 mL (≈ 9.0% expansion)",
    ],
        "\"kg\" and \"g\" cancel through the unit chain in each volume calculation. The ice has more empty space because hydrogen bonding locks water molecules into an open tetrahedral lattice."
    ),
    # idx 45: q = 100.0 × 4.184 × 50.0 (APP duplicate)
    ("q = mcΔT = 100.0", 0, [
        "q = m × c × ΔT = 100.0 ~~g~~ × (4.184 J / 1 ~~g~~·~~°C~~) × 50.0 ~~°C~~ = 20,920 J = 20.9 kJ",
    ],
        "\"g\" / \"°C\" cancel in the standard q = mcΔT chain, leaving energy in joules."
    ),
    # idx 46: c = q/(mΔT) for unknown metal
    ("c = q/(mΔT)", 0, [
        "ΔT = 84.0 − 20.0 = 64.0 °C",
        "c = q / (m × ΔT) = 1200 J / (50.0 ~~g~~ × 64.0 ~~°C~~) = 1200 / 3200 = 0.375 J/(~~g~~·~~°C~~)",
        "Wait — the cancellation here is the reverse: \"g\" and \"°C\" appear in the DENOMINATOR, so they survive into the unit of c (J/g·°C). Final: c = 0.375 J/(g·°C)",
    ],
        "Solving q = mcΔT for c: divide both sides by m × ΔT. The \"g\" and \"°C\" in the denominator do NOT cancel against anything — they become part of the units of c (J per gram per degree)."
    ),
    # idx 48: 250 g aluminum heated 30.0 °C
    ("q = 250 × 0.897", 0, [
        "q = m × c × ΔT = 250 ~~g~~ × (0.897 J / 1 ~~g~~·~~°C~~) × 30.0 ~~°C~~ = 6728 J ≈ 6.73 kJ",
    ],
        "\"g\" and \"°C\" cancel; result is in joules. Three sig figs."
    ),
    # idx 49: 500 J → 25.0 g Cu final temperature
    ("ΔT = q/(mc)", 0, [
        "ΔT = q / (m × c) = 500.0 ~~J~~ / (25.0 ~~g~~ × (0.385 ~~J~~ / 1 ~~g~~·°C)) = 500.0 / 9.625 = 51.95 °C",
        "T_f = T_i + ΔT = 22.0 + 51.95 = 74.0 °C",
    ],
        "\"J\" and \"g\" cancel in the ΔT calculation, leaving °C. The final temperature is the initial temperature plus the rise."
    ),
    # idx 55: athlete sweat (multi-line, consume_after=1)
    ("Mass = 0.500", 1, [
        "Mass = 0.500 ~~L~~ × (1000 ~~mL~~ / 1 ~~L~~) × (1.00 g / 1 ~~mL~~) = 500. g",
        "n = 500. ~~g~~ × (1 mol / 18.015 ~~g~~) = 27.75 mol H₂O",
        "Heat removed = 27.75 ~~mol~~ × (44 kJ / 1 ~~mol~~) = 1221 kJ ≈ 1.2 × 10³ kJ",
    ],
        "Cancellations: \"L\" → \"mL\" (volume to mass via density); \"g\" (mass to moles via molar mass); \"mol\" (moles to energy via heat of vaporization). At ~44 kJ/mol, evaporative cooling can lower body temperature by several degrees if the sweat is not replaced."
    ),
]


if __name__ == "__main__":
    n = apply_rewrites(
        "Chapter_10_States_of_Matter.docx",
        REWRITES,
        skip_indices=SKIP,
    )
    print(f"Chapter 10: applied {n} rewrites.")
