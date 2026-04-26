"""Two cleanup tasks:

  1. Strip the duplicate "Solution: Solution:" prefix from every solution
     paragraph in the new "Additional Practice Problems by Topic" sections.
     The duplication happened because my insertion script prepended a bold
     "Solution: " run AND the source-data solution strings already began
     with "Solution: ".

  2. Renumber every still-typed problem prefix in any chapter (e.g. the
     original 1-25 problems in Ch 07 and Ch 08 that now sit between two
     H2 headings after the earlier move pass). Uses a *global walk* so it
     picks up problems regardless of which two H2 headings flank them.

Skips paragraphs that already carry <w:numPr>. Idempotent.
"""
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

DUP_PREFIX_RE = re.compile(r"^Solution:\s+Solution:\s+")
PROBLEM_PATTERNS = [
    (re.compile(r"^MC(\d+)\.\s+"), "MC%1."),  # process MC first (more specific)
    (re.compile(r"^(\d+)\.\s+"),    "%1."),
]


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


# ---------- duplicate "Solution: Solution:" repair ---------------------- #


def fix_duplicate_solution_prefix(p_el):
    """If the visible text of p_el begins with 'Solution: Solution:', remove
    one occurrence from whichever <w:t> contains it. Preserves the other
    runs (including the bolded leading 'Solution: ' run)."""
    if not DUP_PREFIX_RE.match(text_of(p_el) + " "):
        return False
    # Find the FIRST <w:t> whose text contains "Solution:" preceded by
    # at most whitespace, and remove that "Solution: " (with following space).
    # The first run is typically the bold "Solution: " label run; the second
    # run holds the duplicate. We strip the duplicate (the SECOND occurrence)
    # by removing it from the first <w:t> that begins with "Solution: " AFTER
    # we've seen the bold label.
    seen_label = False
    target = re.compile(r"^Solution:\s+")
    for r in p_el.iter(W_R):
        for t in r.iter(W_T):
            if t.text is None:
                continue
            if not seen_label:
                if target.match(t.text):
                    seen_label = True
                continue
            # second match -> strip
            if target.match(t.text):
                t.text = target.sub("", t.text, count=1)
                return True
    return False


# ---------- numbering machinery ----------------------------------------- #


def get_numbering_xml(doc):
    return doc.part.numbering_part.element


def add_abstract_num(numbering_el, lvl_text):
    used = {int(a.get(qn("w:abstractNumId")))
            for a in numbering_el.findall(qn("w:abstractNum"))}
    new_id = max(used, default=-1) + 1
    an = OxmlElement("w:abstractNum")
    an.set(qn("w:abstractNumId"), str(new_id))
    lvl = OxmlElement("w:lvl"); lvl.set(qn("w:ilvl"), "0")
    start = OxmlElement("w:start"); start.set(qn("w:val"), "1")
    fmt = OxmlElement("w:numFmt"); fmt.set(qn("w:val"), "decimal")
    txt = OxmlElement("w:lvlText"); txt.set(qn("w:val"), lvl_text)
    jc = OxmlElement("w:jc"); jc.set(qn("w:val"), "left")
    pPr = OxmlElement("w:pPr")
    ind = OxmlElement("w:ind"); ind.set(qn("w:left"), "720"); ind.set(qn("w:hanging"), "360")
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
    used = {int(n.get(qn("w:numId"))) for n in numbering_el.findall(qn("w:num"))}
    new_id = max(used, default=0) + 1
    num = OxmlElement("w:num"); num.set(qn("w:numId"), str(new_id))
    aref = OxmlElement("w:abstractNumId"); aref.set(qn("w:val"), str(abstract_num_id))
    num.append(aref)
    lvl_override = OxmlElement("w:lvlOverride"); lvl_override.set(qn("w:ilvl"), "0")
    start_override = OxmlElement("w:startOverride"); start_override.set(qn("w:val"), "1")
    lvl_override.append(start_override); num.append(lvl_override)
    numbering_el.append(num)
    return str(new_id)


def apply_numPr(p_el, num_id, list_para_style_id=None):
    pPr = p_el.find(qn("w:pPr"))
    if pPr is None:
        pPr = OxmlElement("w:pPr"); p_el.insert(0, pPr)
    for existing in pPr.findall(qn("w:numPr")):
        pPr.remove(existing)
    if list_para_style_id and pPr.find(qn("w:pStyle")) is None:
        ps = OxmlElement("w:pStyle"); ps.set(qn("w:val"), list_para_style_id)
        pPr.insert(0, ps)
    numPr = OxmlElement("w:numPr")
    ilvl = OxmlElement("w:ilvl"); ilvl.set(qn("w:val"), "0")
    nid = OxmlElement("w:numId"); nid.set(qn("w:val"), str(num_id))
    numPr.append(ilvl); numPr.append(nid)
    pPr.append(numPr)


def strip_prefix_in_paragraph(p_el, prefix_re):
    for r in p_el.iter(W_R):
        for t in r.iter(W_T):
            if t.text:
                m = prefix_re.match(t.text)
                if m:
                    t.text = t.text[m.end():]
                    return True
                else:
                    return False
    return False


# ---------- global renumber pass ---------------------------------------- #


def renumber_global(doc, list_para_style_id):
    """Walk the document body once; for each typed-numbered problem
    paragraph (matching one of PROBLEM_PATTERNS), strip its prefix and
    apply numPr. Restart numbering on H2 crossing or number-drop."""
    numbering_el = get_numbering_xml(doc)
    body = doc.element.body
    children = list(body.iterchildren())

    abstract_for_lvl = {}    # lvl_text -> abstractNumId
    state = {pat: {"num_id": None, "last_value": 0} for pat, _lvl in PROBLEM_PATTERNS}
    converted = 0

    for el in children:
        if el.tag != P_TAG:
            continue
        if is_heading(el, 2):
            # H2 boundary -> reset every running num assignment
            for pat in state:
                state[pat]["num_id"] = None
                state[pat]["last_value"] = 0
            continue
        if has_numPr(el):
            continue
        full = text_of(el)
        if not full:
            continue

        for pat, lvl_text in PROBLEM_PATTERNS:
            m = pat.match(full)
            if not m:
                continue
            try:
                value = int(m.group(1))
            except (IndexError, ValueError):
                value = None

            st = state[pat]
            if st["num_id"] is None or (value is not None and value <= st["last_value"]):
                if lvl_text not in abstract_for_lvl:
                    abstract_for_lvl[lvl_text] = add_abstract_num(numbering_el, lvl_text)
                st["num_id"] = add_num_instance(numbering_el, abstract_for_lvl[lvl_text])
                st["last_value"] = 0

            if not strip_prefix_in_paragraph(el, pat):
                break
            apply_numPr(el, st["num_id"], list_para_style_id)
            converted += 1
            if value is not None:
                st["last_value"] = value
            break  # only one pattern per paragraph

    return converted


def fix_solution_dups(doc):
    fixed = 0
    for el in doc.element.body.iter(P_TAG):
        if fix_duplicate_solution_prefix(el):
            fixed += 1
    return fixed


def process_chapter(num, filename):
    src = ROOT / filename
    if not src.exists():
        return f"Ch {num}: missing"
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    backup = BACKUP_DIR / f"{src.stem}.before-a11y-fix.docx"
    shutil.copy2(src, backup)

    doc = Document(str(src))
    list_para_style_id = style_id_or_none(doc, "List Paragraph")

    n_dups = fix_solution_dups(doc)
    n_listed = renumber_global(doc, list_para_style_id)

    doc.save(str(src))
    return f"Ch {num}: solution-dup-fixed={n_dups}, additional-list-items={n_listed}"


def main():
    for num, filename in CHAPTER_FILES.items():
        try:
            print(process_chapter(num, filename))
        except PermissionError as e:
            print(f"Ch {num}: locked ({e}); close in Word and re-run")


if __name__ == "__main__":
    main()
