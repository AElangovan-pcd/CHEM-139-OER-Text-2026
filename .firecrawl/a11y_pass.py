"""Accessibility cleanup pass for every chapter.

Tasks:
  1. Convert every typed-numbered problem paragraph (e.g. "1. ", "2. ",
     ..., "MC1. ", "MC2. ") in the problem-set sections to a real Word
     ordered-list item: removes the typed prefix, applies <w:numPr> with
     <w:numId> referencing a freshly-created decimal abstract-num
     definition, and applies the "List Paragraph" style.
  2. Numbering RESTARTS at 1 at the start of each problem-set section
     (Practice Problems by Topic; Multi-Concept Problems; Multiple-Choice
     Practice Test) and at any in-section number-drop.
  3. Removes the redundant introductory paragraph that begins
     "Five additional problems per topic, ..." under the
     "Additional Practice Problems by Topic" heading -- it duplicates the
     instruction already stated under the original "Practice Problems by
     Topic" heading.

Idempotent. Skips any paragraph that already carries a <w:numPr>.
"""
from copy import deepcopy
from pathlib import Path
import re
import shutil
import sys

from docx import Document
from docx.oxml import OxmlElement
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
W_T = qn("w:t")
W_R = qn("w:r")

# Sections to process and the lvlText format their numbering should use.
SECTIONS_TO_NUMBER = [
    ("Practice Problems by Topic", r"^(\d+)\.\s+", "%1."),
    ("Multi-Concept Problems",      r"^MC(\d+)\.\s+", "MC%1."),
    ("Multiple Choice Practice Test", r"^(\d+)\.\s+", "%1."),
]

REDUNDANT_INTRO_PREFIX = "Five additional problems per topic"


# ---------- helpers ------------------------------------------------------ #


def text_of(p_el):
    return "".join(t.text or "" for t in p_el.iter(W_T)).strip()


def is_heading(p_el, level):
    pPr = p_el.find(qn("w:pPr"))
    if pPr is None:
        return False
    style = pPr.find(qn("w:pStyle"))
    if style is None:
        return False
    val = style.get(qn("w:val")) or ""
    return val == f"Heading{level}"


def has_numPr(p_el):
    pPr = p_el.find(qn("w:pPr"))
    return pPr is not None and pPr.find(qn("w:numPr")) is not None


def style_id_or_none(doc, name):
    for s in doc.styles:
        try:
            if s.name == name:
                return s.style_id
        except Exception:
            continue
    return None


# ---------- numbering definitions ---------------------------------------- #


def get_numbering_xml(doc):
    return doc.part.numbering_part.element


def add_abstract_num(numbering_el, lvl_text):
    """Create a fresh decimal abstractNum with the given lvlText. Return id."""
    used = {int(a.get(qn("w:abstractNumId")))
            for a in numbering_el.findall(qn("w:abstractNum"))}
    new_id = max(used, default=-1) + 1

    an = OxmlElement("w:abstractNum")
    an.set(qn("w:abstractNumId"), str(new_id))

    lvl = OxmlElement("w:lvl")
    lvl.set(qn("w:ilvl"), "0")

    start = OxmlElement("w:start"); start.set(qn("w:val"), "1")
    fmt = OxmlElement("w:numFmt"); fmt.set(qn("w:val"), "decimal")
    txt = OxmlElement("w:lvlText"); txt.set(qn("w:val"), lvl_text)
    jc = OxmlElement("w:jc"); jc.set(qn("w:val"), "left")

    pPr = OxmlElement("w:pPr")
    ind = OxmlElement("w:ind")
    ind.set(qn("w:left"), "720")
    ind.set(qn("w:hanging"), "360")
    pPr.append(ind)

    for child in (start, fmt, txt, jc, pPr):
        lvl.append(child)
    an.append(lvl)

    first_num = numbering_el.find(qn("w:num"))
    if first_num is not None:
        first_num.addprevious(an)
    else:
        numbering_el.append(an)
    return str(new_id)


def add_num_instance(numbering_el, abstract_num_id):
    """Append a fresh <w:num> with startOverride=1, return its numId."""
    used = {int(n.get(qn("w:numId")))
            for n in numbering_el.findall(qn("w:num"))}
    new_id = max(used, default=0) + 1

    num = OxmlElement("w:num")
    num.set(qn("w:numId"), str(new_id))
    aref = OxmlElement("w:abstractNumId")
    aref.set(qn("w:val"), str(abstract_num_id))
    num.append(aref)
    lvl_override = OxmlElement("w:lvlOverride")
    lvl_override.set(qn("w:ilvl"), "0")
    start_override = OxmlElement("w:startOverride")
    start_override.set(qn("w:val"), "1")
    lvl_override.append(start_override)
    num.append(lvl_override)

    numbering_el.append(num)
    return str(new_id)


def apply_numPr(p_el, num_id, list_para_style_id=None):
    pPr = p_el.find(qn("w:pPr"))
    if pPr is None:
        pPr = OxmlElement("w:pPr")
        p_el.insert(0, pPr)
    # Remove any old numPr
    for existing in pPr.findall(qn("w:numPr")):
        pPr.remove(existing)
    # Apply the List Paragraph style if available (visual indent + tabs).
    if list_para_style_id:
        existing_pStyle = pPr.find(qn("w:pStyle"))
        if existing_pStyle is None:
            ps = OxmlElement("w:pStyle")
            ps.set(qn("w:val"), list_para_style_id)
            pPr.insert(0, ps)
    numPr = OxmlElement("w:numPr")
    ilvl = OxmlElement("w:ilvl"); ilvl.set(qn("w:val"), "0")
    nid = OxmlElement("w:numId"); nid.set(qn("w:val"), str(num_id))
    numPr.append(ilvl); numPr.append(nid)
    pPr.append(numPr)


# ---------- prefix stripping -------------------------------------------- #


def strip_prefix_in_paragraph(p_el, prefix_re):
    """Remove the leading prefix matching prefix_re from the paragraph's
    first non-empty <w:t>. Returns True if a strip happened."""
    pattern = re.compile(prefix_re)
    for r in p_el.iter(W_R):
        for t in r.iter(W_T):
            if t.text:
                m = pattern.match(t.text)
                if m:
                    t.text = t.text[m.end():]
                    return True
                else:
                    return False  # first run/text didn't match prefix
    return False


# ---------- core --------------------------------------------------------- #


def find_section_ranges(body_children, section_title):
    """Return list of (start_idx_inclusive, end_idx_exclusive) for every
    block of body elements that starts with an H2 paragraph whose text
    begins with section_title and ends at the next H2 paragraph (or end)."""
    ranges = []
    for i, el in enumerate(body_children):
        if el.tag != P_TAG:
            continue
        if is_heading(el, 2) and text_of(el).startswith(section_title):
            end = len(body_children)
            for j in range(i + 1, len(body_children)):
                e2 = body_children[j]
                if e2.tag == P_TAG and is_heading(e2, 2):
                    end = j
                    break
            ranges.append((i, end))
    return ranges


def renumber_in_range(body_children, start, end, prefix_re, numbering_el,
                      list_para_style_id, abstract_num_cache, lvl_text):
    """Walk body_children[start:end] and convert every paragraph whose text
    begins with prefix_re into a real numbered-list item. Numbering
    restarts on a number-drop. Returns count of paragraphs converted."""
    pattern = re.compile(prefix_re)
    count = 0
    current_num_id = None
    last_value = 0

    # Ensure an abstractNum exists for this lvl_text
    if lvl_text not in abstract_num_cache:
        abstract_num_cache[lvl_text] = add_abstract_num(numbering_el, lvl_text)
    abstract_id = abstract_num_cache[lvl_text]

    for idx in range(start, end):
        el = body_children[idx]
        if el.tag != P_TAG:
            continue
        if has_numPr(el):
            continue  # already a list item; skip
        full_text = text_of(el)
        m = pattern.match(full_text)
        if not m:
            continue
        try:
            value = int(m.group(1))
        except (IndexError, ValueError):
            value = None

        # Restart logic: new num if no current, or value <= last_value.
        if current_num_id is None or (value is not None and value <= last_value):
            current_num_id = add_num_instance(numbering_el, abstract_id)
            last_value = 0

        if not strip_prefix_in_paragraph(el, prefix_re):
            continue
        apply_numPr(el, current_num_id, list_para_style_id)
        count += 1
        if value is not None:
            last_value = value
    return count


def remove_redundant_intro(body_children):
    """Find the paragraph immediately after the H2 'Additional Practice
    Problems by Topic' that begins with the redundant intro phrase, and
    remove it. Returns 1 if removed, 0 otherwise."""
    for i, el in enumerate(body_children):
        if el.tag != P_TAG:
            continue
        if is_heading(el, 2) and text_of(el).startswith("Additional Practice Problems by Topic"):
            # Look at the very next non-empty paragraph
            for j in range(i + 1, min(i + 4, len(body_children))):
                cand = body_children[j]
                if cand.tag != P_TAG:
                    continue
                t = text_of(cand)
                if not t:
                    continue
                if t.startswith(REDUNDANT_INTRO_PREFIX):
                    cand.getparent().remove(cand)
                    return 1
                else:
                    return 0
    return 0


def process_chapter(num, filename):
    src = ROOT / filename
    if not src.exists():
        return f"Ch {num}: missing"

    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    backup = BACKUP_DIR / f"{src.stem}.before-a11y-pass.docx"
    shutil.copy2(src, backup)

    doc = Document(str(src))
    body = doc.element.body
    list_para_style_id = style_id_or_none(doc, "List Paragraph")
    numbering_el = get_numbering_xml(doc)
    abstract_cache = {}

    body_children = list(body.iterchildren())
    removed_intro = remove_redundant_intro(body_children)

    # Refresh after possible removal
    body_children = list(body.iterchildren())

    section_counts = {}
    for section_title, prefix_re, lvl_text in SECTIONS_TO_NUMBER:
        ranges = find_section_ranges(body_children, section_title)
        section_total = 0
        for start, end in ranges:
            section_total += renumber_in_range(
                body_children, start, end, prefix_re, numbering_el,
                list_para_style_id, abstract_cache, lvl_text)
        section_counts[section_title] = section_total

    doc.save(str(src))
    summary = ", ".join(f"{title.split()[0]}={n}" for title, n in section_counts.items())
    return f"Ch {num}: removed_intro={removed_intro}, list-items: {summary}"


def main():
    for num, filename in CHAPTER_FILES.items():
        try:
            print(process_chapter(num, filename))
        except PermissionError as e:
            print(f"Ch {num}: locked ({e}); close in Word and re-run")


if __name__ == "__main__":
    main()
