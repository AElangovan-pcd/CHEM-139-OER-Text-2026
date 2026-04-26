"""Convert inline (a)/(b)/(c)/(d) sub-options in any problem or solution
paragraph into a real ordered sub-list with lowercase-letter format,
preserving every character of the original text. Only the layout changes;
no word in the source text is added, removed, or rephrased.

Heuristic for triggering: the paragraph's full text contains the markers
"(a) ", "(b) ", ... in alphabetical sequence (at least two letters). For
each such paragraph:

  * Lead text: everything before the first "(a) " marker stays in the
    parent paragraph (preserving its existing runs/formatting/numPr).
  * Option text: each "(letter) ..." substring (without the marker token)
    becomes its own paragraph immediately after, marked up as a real
    ordered-list item via <w:numPr> referencing a fresh decimal-lowerLetter
    abstract numbering definition with lvlText "(%1)" — so screen readers
    announce "list of N items, item 1 of N" while sighted readers see
    "(a)", "(b)", "(c)", ...

Idempotent: once a paragraph's text no longer matches the inline pattern,
re-running the script is a no-op.
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
R_TAG = qn("w:r")
T_TAG = qn("w:t")

# Marker like "(a) ", "(b) ", … — capture the letter for sequence check.
MARKER_RE = re.compile(r"\(([a-z])\)\s+")


# ---------- helpers ------------------------------------------------------ #


def text_of(p_el):
    return "".join(t.text or "" for t in p_el.iter(T_TAG))


def style_id_or_none(doc, name):
    for s in doc.styles:
        try:
            if s.name == name:
                return s.style_id
        except Exception:
            continue
    return None


def has_numPr(p_el):
    pPr = p_el.find(qn("w:pPr"))
    return pPr is not None and pPr.find(qn("w:numPr")) is not None


# ---------- numbering setup --------------------------------------------- #


def get_numbering_xml(doc):
    return doc.part.numbering_part.element


def add_lower_letter_abstract_num(numbering_el):
    """Decimal-paren-letter abstract num used for sub-options."""
    used = {int(a.get(qn("w:abstractNumId")))
            for a in numbering_el.findall(qn("w:abstractNum"))}
    new_id = max(used, default=-1) + 1
    an = OxmlElement("w:abstractNum")
    an.set(qn("w:abstractNumId"), str(new_id))
    lvl = OxmlElement("w:lvl"); lvl.set(qn("w:ilvl"), "0")
    start = OxmlElement("w:start"); start.set(qn("w:val"), "1")
    fmt = OxmlElement("w:numFmt"); fmt.set(qn("w:val"), "lowerLetter")
    txt = OxmlElement("w:lvlText"); txt.set(qn("w:val"), "(%1)")
    jc = OxmlElement("w:jc"); jc.set(qn("w:val"), "left")
    pPr = OxmlElement("w:pPr")
    ind = OxmlElement("w:ind")
    ind.set(qn("w:left"), "1440")
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
    used = {int(n.get(qn("w:numId"))) for n in numbering_el.findall(qn("w:num"))}
    new_id = max(used, default=0) + 1
    num = OxmlElement("w:num"); num.set(qn("w:numId"), str(new_id))
    aref = OxmlElement("w:abstractNumId"); aref.set(qn("w:val"), str(abstract_num_id))
    num.append(aref)
    lo = OxmlElement("w:lvlOverride"); lo.set(qn("w:ilvl"), "0")
    so = OxmlElement("w:startOverride"); so.set(qn("w:val"), "1")
    lo.append(so); num.append(lo)
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


# ---------- truncation: keep all runs/formatting before split_pos ------- #


def truncate_runs_at_text_position(p_el, split_pos):
    """Walk runs/text in order; keep characters up to split_pos; truncate
    the <w:t> that straddles split_pos and discard every <w:r> after.
    Preserves formatting on the kept portion."""
    if split_pos <= 0:
        return
    consumed = 0
    keep_phase = True
    runs_to_remove_after = []
    runs = list(p_el.findall(R_TAG))
    for r in runs:
        if not keep_phase:
            runs_to_remove_after.append(r)
            continue
        run_text_total = sum(len(t.text or "") for t in r.findall(T_TAG))
        if consumed + run_text_total <= split_pos:
            consumed += run_text_total
            continue
        # split is inside this run
        truncate_inside_run(r, split_pos - consumed)
        keep_phase = False
    for r in runs_to_remove_after:
        p_el.remove(r)


def truncate_inside_run(run_el, offset):
    """Walk <w:t> in order; let through `offset` chars; truncate the <w:t>
    that contains position `offset`; remove all subsequent <w:t>."""
    consumed = 0
    truncated = False
    t_els = list(run_el.findall(T_TAG))
    for t in t_els:
        if t.text is None:
            continue
        if truncated:
            run_el.remove(t)
            continue
        tlen = len(t.text)
        if consumed + tlen <= offset:
            consumed += tlen
            continue
        local_off = offset - consumed
        t.text = t.text[:local_off]
        truncated = True


# ---------- per-paragraph conversion ------------------------------------ #


def find_sublist_options(full_text):
    """Return (split_pos, [(letter, content), ...]) if the paragraph contains
    a real (a)(b)(c)... option list; otherwise None.

    Rules:
      * At least two markers present.
      * Letters appear in strict ascending sequence starting at 'a'.
    """
    matches = list(MARKER_RE.finditer(full_text))
    if len(matches) < 2:
        return None
    letters = [m.group(1) for m in matches]
    expected = [chr(ord("a") + i) for i in range(len(matches))]
    if letters != expected:
        return None
    split_pos = matches[0].start()
    options = []
    for i, m in enumerate(matches):
        content_start = m.end()
        content_end = (matches[i + 1].start()
                       if i + 1 < len(matches) else len(full_text))
        content = full_text[content_start:content_end]
        options.append((m.group(1), content))
    return (split_pos, options)


def make_option_paragraph(option_text, num_id, list_para_style_id):
    """Build a fresh <w:p> containing exactly option_text in one default run,
    marked as item ilvl=0 of num_id."""
    p = OxmlElement("w:p")
    r = OxmlElement("w:r")
    t = OxmlElement("w:t")
    t.set(qn("xml:space"), "preserve")
    t.text = option_text
    r.append(t)
    p.append(r)
    apply_numPr(p, num_id, list_para_style_id)
    return p


def convert_paragraph(p_el, abstract_id, numbering_el, list_para_style_id):
    """If p_el contains an inline (a)(b)(c) sub-list, split it. Returns
    (paragraph_count, option_count) — (0, 0) if nothing was changed."""
    full_text = text_of(p_el)
    detected = find_sublist_options(full_text)
    if detected is None:
        return (0, 0)
    split_pos, options = detected

    # Build new option paragraphs first (don't mutate p_el yet — we still need
    # to reference its content).
    num_id = add_num_instance(numbering_el, abstract_id)

    # Truncate parent paragraph to the lead text.
    truncate_runs_at_text_position(p_el, split_pos)

    # Insert option paragraphs immediately after the parent.
    anchor = p_el
    for _letter, content in options:
        new_p = make_option_paragraph(content, num_id, list_para_style_id)
        anchor.addnext(new_p)
        anchor = new_p

    return (1, len(options))


# ---------- driver ------------------------------------------------------- #


def process_chapter(num, filename):
    src = ROOT / filename
    if not src.exists():
        return f"Ch {num}: missing"

    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    backup = BACKUP_DIR / f"{src.stem}.before-sublists.docx"
    shutil.copy2(src, backup)

    doc = Document(str(src))
    list_para_style_id = style_id_or_none(doc, "List Paragraph")
    numbering_el = get_numbering_xml(doc)
    abstract_id = add_lower_letter_abstract_num(numbering_el)

    body = doc.element.body
    paragraphs = list(body.iter(P_TAG))

    parents_changed = 0
    options_made = 0
    for p_el in paragraphs:
        # Skip paragraphs that we just created (heuristic: empty or short).
        # The conversion logic itself is idempotent because converted
        # paragraphs no longer contain the inline marker pattern.
        pc, oc = convert_paragraph(p_el, abstract_id, numbering_el, list_para_style_id)
        parents_changed += pc
        options_made += oc

    doc.save(str(src))
    return f"Ch {num}: parent-paragraphs split={parents_changed}, sub-list items created={options_made}"


def main():
    for num, filename in CHAPTER_FILES.items():
        try:
            print(process_chapter(num, filename))
        except PermissionError as e:
            print(f"Ch {num}: locked ({e}); close in Word and re-run")


if __name__ == "__main__":
    main()
