"""Apply factor-label rewrites to Chapter 3 (Basic Concepts About Matter) Solutions.

Chapter 3 is overwhelmingly qualitative: classifying matter as elements,
compounds, mixtures; identifying physical vs chemical changes; listing
common element symbols. Only two Solutions in the chapter use a percentage
as a conversion factor — those get the factor-label treatment.
"""
from rewrite_engine import apply_rewrites

REWRITE_INDICES = {19, 38}
ALL_INDICES = set(range(45))
SKIP = ALL_INDICES - REWRITE_INDICES

REWRITES = [
    # idx 19: oxygen mass in 70.0 kg adult, 65% by mass
    ("65% of 70.0", 0, [
        "Mass O = 70.0 ~~kg~~ body × (65 kg O / 100 ~~kg~~ body) = 45.5 kg O",
    ],
        "\"kg body\" cancels using the percent-by-mass factor as a conversion factor; the result is the mass of oxygen (in any chemical form: water, organic molecules, etc.)."
    ),
    # idx 38: iron in 1.0 × 10^6 metric tons crust, 5% by mass
    ("0.05 × 1.0 × 10⁶", 0, [
        "Mass Fe = 1.0 × 10⁶ ~~tons~~ crust × (5 tons Fe / 100 ~~tons~~ crust) = 5 × 10⁴ tons Fe",
    ],
        "\"tons crust\" cancels using the 5% mass-abundance factor. Two sig figs (limited by the rough \"5%\" estimate)."
    ),
]


if __name__ == "__main__":
    n = apply_rewrites(
        "Chapter_03_Basic_Concepts_About_Matter.docx",
        REWRITES,
        skip_indices=SKIP,
    )
    print(f"Chapter 3: applied {n} rewrites.")
