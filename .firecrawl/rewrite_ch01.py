"""Apply factor-label rewrites to Chapter 1 (Science and Measurement) Solutions.

Chapter 1's emphasis is the scientific method, accuracy/precision, sig figs,
and scientific notation. Most Solutions are conceptual or about sig-fig
discipline; only a handful involve unit cancellation. We rewrite only those.
"""
from rewrite_engine import apply_rewrites

# Indices to LEAVE UNTOUCHED (everything except idx 21 and idx 53).
REWRITE_INDICES = {21, 53}
ALL_INDICES = set(range(69))
SKIP = ALL_INDICES - REWRITE_INDICES

REWRITES = [
    # idx 21: (4.50 × 10³ g) × (2.0 × 10⁻² mL/g) = 90. mL
    ("9.0 × 10¹", 0, [
        "(4.50 × 10³ ~~g~~) × (2.0 × 10⁻² mL / 1 ~~g~~) = 9.0 × 10¹ mL = 90. mL",
    ],
        "\"g\" cancels against the \"g\" in the denominator of the conversion factor, leaving \"mL\". Two sig figs (limited by 2.0 × 10⁻²)."
    ),
    # idx 53: (0.0250 mol)(98.08 g/mol) = 2.45 g
    ("0.0250 × 98.08", 0, [
        "0.0250 ~~mol~~ × (98.08 g / 1 ~~mol~~) = 2.452 g → 2.45 g",
    ],
        "\"mol\" cancels in the molar-mass conversion, leaving \"g\". Three sig figs (limited by 0.0250)."
    ),
]


if __name__ == "__main__":
    n = apply_rewrites(
        "Chapter_01_Science_and_Measurement.docx",
        REWRITES,
        skip_indices=SKIP,
    )
    print(f"Chapter 1: applied {n} rewrites.")
