"""Audit Problem - Solution pairing across every chapter's standalone HTML.

The bug: a solution displayed under a problem stem actually belongs to a
different problem. Confirmed in Chapter 02; the source `.docx` has the
mismatch too, so the bug is in content not the build pipeline.

Heuristic (intentionally low-recall, high-precision):
  1. Extract every DECIMAL number (e.g. ``4.0``, ``2.54``, ``0.082``) from
     the problem stem - decimals are distinctive enough that if they appear
     in the stem they should also appear in a correctly-paired solution.
  2. If NONE of the stem's decimals appear as a substring in the solution
     text, flag it as a likely mismatch.
  3. If the stem has no decimals (purely conceptual problem), skip it -
     those need eyeball review, not auto-flagging.

This intentionally misses some real mismatches (e.g. the "List the
prefixes" stem in Chapter 02, which has no decimals). But it's accurate
enough to surface the dominant pattern - solutions paired with the wrong
numeric stem - without drowning the user in false positives from
chemistry-equation stoichiometry coefficients.

Output: per-chapter list of flagged mismatches plus a final summary.
"""
from __future__ import annotations

import io
import re
import sys
from pathlib import Path

from bs4 import BeautifulSoup

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = ROOT / "HTML_Files"

# Decimal numbers like "4.0", "2.54", "0.082", "121.92", but NOT integers
# alone (which are too common: "1 ft", "12 in", "10^3", coefficients).
# We also skip "10.5" if it's part of "Table 10.5" (table reference) by
# requiring the decimal to be followed by either whitespace+letter (a unit)
# or end-of-string.
_DECIMAL_RE = re.compile(r"(?<![\d.])(\d+\.\d+)(?![\d.])")


def stem_decimals(text: str) -> set[str]:
    """Return the set of decimal numbers present in the stem text. Skip
    tokens that look like section / table cross-references (``Table 10.5``,
    ``Section 2.3``, ``Figure 1.10``)."""
    out: set[str] = set()
    # Strip cross-references first.
    cleaned = re.sub(
        r"\b(?:Table|Section|Figure|Sec\.|Fig\.|Ch\.|Chapter)\s*\d+(?:\.\d+)?",
        " ",
        text,
    )
    for m in _DECIMAL_RE.finditer(cleaned):
        out.add(m.group(1))
    return out


def solution_text(details_soup) -> str:
    """All text content of the solution, including math chains."""
    return details_soup.get_text(" ", strip=True)


def stem_text(stem) -> str:
    text = stem.get_text(" ", strip=True)
    return re.sub(r"^\d+\.\s*", "", text)


def number_appears(num: str, hay: str) -> bool:
    """True if `num` appears in `hay` as its own decimal token (so "2.5"
    inside "12.54" is not counted, but "2.5" inside "2.5 mg" is)."""
    pattern = r"(?<![\d.])" + re.escape(num) + r"(?![\d])"
    return re.search(pattern, hay) is not None


def audit_chapter(html_path: Path) -> tuple[list[dict], int, int, int]:
    """Returns (mismatches, total_stems, decimal_stems, conceptual_skipped)."""
    soup = BeautifulSoup(html_path.read_text(encoding="utf-8"), "html.parser")
    flagged: list[dict] = []
    total = 0
    decimal_count = 0
    skipped = 0

    for stem in soup.find_all("p", class_="problem-stem"):
        total += 1
        # Find the next <details class="solution"> sibling.
        sib = stem.find_next_sibling()
        details = None
        while sib is not None:
            if sib.name == "details" and "solution" in (sib.get("class") or []):
                details = sib
                break
            if sib.name == "p" and "problem-stem" in (sib.get("class") or []):
                break
            sib = sib.find_next_sibling()
        if details is None:
            continue

        stem_t = stem_text(stem)
        decimals = stem_decimals(stem_t)
        if not decimals:
            skipped += 1
            continue
        decimal_count += 1

        sol_t = solution_text(details)
        present = {n for n in decimals if number_appears(n, sol_t)}
        if not present:
            flagged.append(
                {
                    "stem": stem_t[:160],
                    "stem_decimals": sorted(decimals),
                    "sol_excerpt": sol_t[:220],
                }
            )

    return flagged, total, decimal_count, skipped


def main() -> None:
    chapters = sorted(SRC_DIR.glob("Chapter_*.html"))
    if not chapters:
        sys.exit(f"No chapters found in {SRC_DIR}")

    summary = []
    for ch in chapters:
        flagged, total, dec, skipped = audit_chapter(ch)
        summary.append((ch.name, total, dec, len(flagged), skipped))
        if not flagged:
            continue
        print(f"\n=== {ch.name} - {len(flagged)} likely mismatch(es) ===")
        for f in flagged:
            print(f"  STEM:  {f['stem']}")
            print(f"  STEM-DECIMALS: {f['stem_decimals']}")
            print(f"  SOL :  {f['sol_excerpt']}")
            print()

    print("\n=== SUMMARY ===")
    print(
        f"{'Chapter':40s}  {'Stems':>6s}  {'WithDec':>8s}  "
        f"{'Flagged':>8s}  {'Conceptual':>10s}"
    )
    for name, total, dec, m, sk in summary:
        print(f"{name:40s}  {total:>6d}  {dec:>8d}  {m:>8d}  {sk:>10d}")


if __name__ == "__main__":
    main()
