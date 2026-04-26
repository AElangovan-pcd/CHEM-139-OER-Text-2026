"""Move the entire "Additional Practice Problems by Topic" section so that it
sits directly above the original "Mixed" / "Mixed practice" Heading 3 in
each chapter that has one.

For chapters where the original content does not contain a "Mixed" anchor,
the section stays in its current place (immediately above "Multi-Concept
Problems"). The script reports which chapters were moved and which were
skipped.

Idempotent: if the new section already sits directly above the anchor,
nothing changes.
"""
from pathlib import Path
import shutil
import sys

from docx import Document
from docx.oxml.ns import qn

ROOT = Path(r"C:/Users/easam/Documents/Claude/Projects/OER/CHEM_139_OER_Text_2026")
BACKUP_DIR = ROOT / ".firecrawl" / "backups"

CHAPTER_FILES = {
    "01": "Chapter_01_Science_and_Measurement.docx",
    "02": "Chapter_02_Unit_Systems_and_Dimensional_Analysis.docx",
    "03": "Chapter_03_Basic_Concepts_About_Matter.docx",
    "04": "Chapter_04_Atoms_Molecules_Subatomic_Particles.docx",
    "05": "Chapter_05_Electronic_Structure_and_Periodicity.docx",
    "06": "Chapter_06_Chemical_Bonds.docx",
    "07": "Chapter_07_Chemical_Nomenclature.docx",
    "08": "Chapter_08_Mole_Concept_and_Chemical_Formulas.docx",
    "09": "Chapter_09_Chemical_Calculations_and_Equations.docx",
    "10": "Chapter_10_States_of_Matter.docx",
}

P_TAG = qn("w:p")
NEW_SECTION_TITLE = "Additional Practice Problems by Topic"


def text_of(p_el):
    return "".join(t.text or "" for t in p_el.iter(qn("w:t"))).strip()


def is_heading(p_el, level):
    pPr = p_el.find(qn("w:pPr"))
    if pPr is None:
        return False
    style = pPr.find(qn("w:pStyle"))
    if style is None:
        return False
    val = style.get(qn("w:val")) or ""
    return val == f"Heading{level}" or val.startswith(f"Heading{level}")


def find_new_section_range(body_children):
    """Return (start_idx, end_idx_exclusive) of the new section, or None."""
    start = None
    for i, el in enumerate(body_children):
        if el.tag != P_TAG:
            continue
        if is_heading(el, 2) and text_of(el).startswith(NEW_SECTION_TITLE):
            start = i
            break
    if start is None:
        return None
    end = len(body_children)
    for j in range(start + 1, len(body_children)):
        el = body_children[j]
        if el.tag == P_TAG and is_heading(el, 2):
            end = j
            break
    return (start, end)


def find_mixed_anchor(body_children, before_idx):
    """First H3 paragraph whose trimmed text equals 'Mixed' or starts with
    'Mixed practice', located at an index < before_idx. Returns the
    element or None."""
    for i in range(before_idx):
        el = body_children[i]
        if el.tag != P_TAG or not is_heading(el, 3):
            continue
        t = text_of(el)
        if t == "Mixed" or t.startswith("Mixed practice"):
            return el
    return None


def already_above_anchor(body_children, start_idx, anchor_el):
    """True if the new section already sits directly above the anchor."""
    if start_idx == 0:
        return False
    # The anchor's position is its current index in body_children.
    try:
        anchor_idx = body_children.index(anchor_el)
    except ValueError:
        return False
    # The section ends at end_idx (exclusive); we want body_children[end_idx]
    # to BE the anchor.
    rng = find_new_section_range(body_children)
    if rng is None:
        return False
    return rng[1] == anchor_idx


def process_chapter(num, filename):
    src = ROOT / filename
    if not src.exists():
        return f"Ch {num}: missing file"
    doc = Document(str(src))
    body = doc.element.body
    children = list(body.iterchildren())

    rng = find_new_section_range(children)
    if rng is None:
        return f"Ch {num}: no new section found; nothing to move."
    start, end = rng

    anchor = find_mixed_anchor(children, start)
    if anchor is None:
        return f"Ch {num}: no original 'Mixed' anchor; left in place."

    if already_above_anchor(children, start, anchor):
        return f"Ch {num}: already above 'Mixed' anchor; no change."

    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    backup = BACKUP_DIR / f"{src.stem}.before-move-mixed.docx"
    shutil.copy2(src, backup)

    # Slice and move: remove children[start:end], then re-insert each before
    # the anchor in original order. (addprevious always inserts immediately
    # before the calling element, so a forward sweep preserves order.)
    to_move = children[start:end]
    for el in to_move:
        el.getparent().remove(el)
    for el in to_move:
        anchor.addprevious(el)

    doc.save(str(src))
    anchor_text = text_of(anchor)
    return (f"Ch {num}: moved new section to sit directly above "
            f"original H3 {anchor_text!r}.")


def main():
    for num, filename in CHAPTER_FILES.items():
        print(process_chapter(num, filename))


if __name__ == "__main__":
    main()
