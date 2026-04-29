#!/usr/bin/env python3
"""Convert OER textbook .docx files to HTML with collapsible Solution blocks.

Output: HTML_Files/index.html plus one HTML page per source document.
"""

import io
import re
import sys
from pathlib import Path

import mammoth
from bs4 import BeautifulSoup, NavigableString

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "HTML_Files"
OUT.mkdir(exist_ok=True)

SOLUTION_RE = re.compile(r"^\s*(Solution|Answer)\s*:\s*", re.IGNORECASE)
PROBLEM_SECTION_RE = re.compile(
    r"(Practice\s+Problems?|Multi.?Concept|Multiple.?Choice|"
    r"Additional\s+Practice|Mixed.?Concept|Practice\s+Test|"
    r"Problems?\s+by\s+Topic|Problem\s+Set|End.?of.?Chapter)",
    re.IGNORECASE,
)
_IMPERATIVE_VERBS = (
    r"Convert|Calculate|Compute|Solve|Determine|Find|Identify|Describe|Explain|"
    r"Compare|Contrast|Predict|Sketch|Draw|Write|Use|Show|Round|Estimate|Express|"
    r"Verify|Apply|Construct|Distinguish|Define|State|Provide|List|Match|Name|"
    r"Pick|Choose|Select|Arrange|Rank|Classify|Categorize|Group|Order|Sort|Label|"
    r"Indicate|Suggest|Justify|Prove|Derive|Balance|Translate|Plot|Graph"
)
QUESTION_STARTERS = re.compile(
    r"^\s*("
    + _IMPERATIVE_VERBS
    + r"|How|What|Why|Which|Where|When|If|Given|For\s+each|Suppose|Imagine|Consider|"
    r"An?\s+\w+|The\s+\w+|One\s+\w+|Some\s+\w+|Each\s+\w+|Every\s+\w+|"
    r"Two\s+|Three\s+|Four\s+|Five\s+|Six\s+|Seven\s+|Eight\s+|Nine\s+|Ten\s+|"
    r"\w+\s+synthesis|\w+\s+reaction|\w+\s+process|"
    r"[A-Z][a-z]+(?:ium|ine|ate|ide|ogen|ic\s+acid)\s+(?:reacts|forms|combines|burns|dissolves|melts|boils|decomposes)"
    r")\b",
    re.IGNORECASE,
)
QUESTION_IMPERATIVE_MIDSENTENCE = re.compile(
    r"\b(" + _IMPERATIVE_VERBS + r")\s+(?:the|a|an|each|both|these|those|how|why|what|which)\b",
    re.IGNORECASE,
)
STOP_LABEL_RE = re.compile(
    r"^\s*("
    r"Solution\s*:|Answer\s*:|"
    r"Practice Problem|Worked Example|Example\s+\d|"
    r"NOTE\s*:|FIGURE\s+DESCRIPTION|Figure\s+\d+\.\d+|"
    r"Concepts to Remember|Key Terms|"
    r"Multi.?concept|Multiple.?choice|"
    r"Practice Test|Answer Key|"
    r"Instructor Notes|Section\s+\d|Part\s+[A-Z]\b"
    r")",
    re.IGNORECASE,
)
STOP_HEADINGS = {"h1", "h2", "h3", "h4", "h5", "h6"}

CSS = r"""
:root {
  --max-w: 800px;
  --accent: #0b5cad;
  --accent-soft: #e8f0fb;
  --rule: #d8d8d8;
  --figure-bg: #f3f3f3;
  --figure-border: #b9b9b9;
  --solution-bg: #eef7ee;
  --solution-border: #2e7d32;
  --text: #1a1a1a;
}
* { box-sizing: border-box; }
html { scroll-behavior: smooth; }
body {
  margin: 0;
  font-family: Georgia, "Times New Roman", serif;
  color: var(--text);
  line-height: 1.65;
  background: #fafafa;
}
header.site, footer.site {
  background: #fff;
  border-bottom: 1px solid var(--rule);
  padding: 0.85rem 1.5rem;
}
footer.site { border-top: 1px solid var(--rule); border-bottom: none; }
header.site nav, footer.site nav {
  max-width: var(--max-w);
  margin: 0 auto;
  display: flex;
  justify-content: space-between;
  gap: 1rem;
  font: 600 0.9rem -apple-system, system-ui, sans-serif;
}
header.site nav a, footer.site nav a {
  color: var(--accent);
  text-decoration: none;
}
header.site nav a:hover, footer.site nav a:hover { text-decoration: underline; }
main.container {
  max-width: var(--max-w);
  margin: 1.5rem auto 3rem;
  padding: 2.5rem;
  background: #fff;
  border: 1px solid var(--rule);
}
@media (max-width: 700px) {
  main.container { padding: 1.25rem; margin: 0.5rem; }
}
h1, h2, h3, h4 {
  font-family: -apple-system, system-ui, "Helvetica Neue", Arial, sans-serif;
  color: #111;
  line-height: 1.25;
  margin-block: 1.5em 0.5em;
}
h1 { font-size: 1.95rem; border-bottom: 2px solid var(--accent); padding-bottom: 0.4rem; }
h2 { font-size: 1.45rem; color: var(--accent); }
h3 { font-size: 1.15rem; }
h4 { font-size: 1.0rem; color: #333; }
p { margin-block: 0.7em; }
ol, ul { padding-left: 1.6rem; }
li { margin-block: 0.25em; }
table { border-collapse: collapse; margin: 1rem 0; font-size: 0.95rem; }
th, td { border: 1px solid var(--rule); padding: 0.4rem 0.7rem; text-align: left; vertical-align: top; }
th { background: var(--accent-soft); }

a { color: var(--accent); }
strong { color: #000; }

.problem-stem {
  margin-top: 1.4em;
  margin-bottom: 0.4em;
}
.problem-stem > strong:first-child {
  display: inline-block;
  min-width: 2em;
  color: var(--accent);
}
.problem-subparts { margin-top: 0.2em; }
.problem-subparts > li { margin-block: 0.3em; }

img {
  max-width: 100%;
  height: auto;
  display: block;
  margin: 1rem auto;
  border-radius: 4px;
}
figure { margin: 1.2rem 0; text-align: center; }
figure img { margin: 0 auto; }
figcaption { font-size: 0.9rem; color: #555; margin-top: 0.4rem; font-style: italic; }

.figure-description {
  background: var(--figure-bg);
  border-left: 4px solid var(--figure-border);
  padding: 0.9rem 1.1rem;
  margin: 1.2rem 0;
  font-size: 0.95rem;
}
.figure-description > p:first-child { margin-top: 0; }
.figure-description > p:last-child { margin-bottom: 0; }

details.solution {
  background: var(--solution-bg);
  border-left: 4px solid var(--solution-border);
  padding: 0.55rem 1rem 0.55rem;
  margin: 0.6rem 0 1.1rem;
  border-radius: 4px;
}
details.solution[open] { padding-bottom: 0.9rem; }
details.solution > summary {
  cursor: pointer;
  font-weight: 600;
  color: var(--solution-border);
  font-family: -apple-system, system-ui, "Helvetica Neue", Arial, sans-serif;
  list-style: none;
  display: inline-flex;
  align-items: center;
  gap: 0.45rem;
  padding: 0.3rem 0.85rem;
  background: #fff;
  border: 1px solid var(--solution-border);
  border-radius: 999px;
  user-select: none;
  font-size: 0.9rem;
}
details.solution > summary::-webkit-details-marker { display: none; }
details.solution > summary::before {
  content: "▶";
  font-size: 0.7em;
  transition: transform 0.15s ease;
}
details.solution[open] > summary::before { transform: rotate(90deg); }
details.solution > summary:hover {
  background: var(--solution-border);
  color: #fff;
}
details.solution > *:not(summary) { margin-top: 0.6rem; }
details.solution > p:empty { display: none; }

@media print {
  details.solution { background: none; border: 1px dashed #888; }
  details.solution > summary { display: none; }
}

.toc { font-size: 1.05rem; }
.toc li { margin: 0.4em 0; }

/* Solution math chains rendered by MathJax. The plain-text fallback (before
   MathJax loads) wraps in a slightly smaller serif. */
p.math-chain {
  text-align: left;
  margin-block: 0.4em;
  overflow-x: auto;
}

/* In case any <s> tags survive in solutions where MathJax was not applied
   (e.g. multi-step prose mixing words and math), give the strikethrough a
   bold red rule so cancellation is unmistakable. */
details.solution s {
  text-decoration: line-through;
  text-decoration-color: #c0392b;
  text-decoration-thickness: 0.12em;
}
"""

JS_PRINT_OPEN = r"""
window.addEventListener("beforeprint", () => {
  document.querySelectorAll("details.solution").forEach(d => {
    d.dataset.wasOpen = d.open ? "1" : "0";
    d.open = true;
  });
});
window.addEventListener("afterprint", () => {
  document.querySelectorAll("details.solution").forEach(d => {
    d.open = d.dataset.wasOpen === "1";
  });
});

// Swap the summary label between "Show solution" / "Hide solution" so the
// pill mirrors the disclosure state.
document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll("details.solution").forEach(d => {
    const summary = d.querySelector("summary");
    if (!summary) return;
    const setLabel = () => {
      summary.textContent = d.open ? "Hide solution" : "Show solution";
    };
    setLabel();
    d.addEventListener("toggle", setLabel);
  });
});
"""


def strip_label_from_paragraph(p):
    """Remove leading 'Solution:' / 'Answer:' label from a <p>, including a wrapping <strong>."""
    first = p.find(["strong", "b"])
    if first and SOLUTION_RE.match(first.get_text()):
        strong_text = first.get_text()
        m = SOLUTION_RE.match(strong_text)
        remainder = strong_text[m.end():].strip()
        if remainder:
            first.clear()
            first.append(NavigableString(remainder))
        else:
            first.decompose()
        return True
    for desc in list(p.descendants):
        if isinstance(desc, NavigableString):
            txt = str(desc)
            m = SOLUTION_RE.match(txt)
            if m:
                desc.replace_with(txt[m.end():])
                return True
            if txt.strip():
                return False
    return False


def is_stop_element(node):
    if not getattr(node, "name", None):
        return False
    if node.name in STOP_HEADINGS:
        return True
    if node.name == "ol" and node.get("data-next-question"):
        return True
    text = node.get_text(" ", strip=True)
    return bool(STOP_LABEL_RE.match(text))


def is_paragraph_empty(p):
    return p.get_text(strip=True) == ""


def restructure_problem_sets(soup):
    """In problem-set sections, renumber problems and convert sub-parts to lettered lists.

    Mammoth outputs each problem as its own <ol start="1">, so a section of 8 problems
    appears as eight "1." items. We renumber by replacing each problem-set <ol> with a
    numbered stem paragraph plus an <ol type="a"> for sub-parts. Counters reset on h2
    boundaries (new problem-set section) and on h3 sub-section boundaries within them.
    The matching answer <ol> inside the immediately-following <details> is also retyped
    to "a" so answers like (a), (b), (c) line up with question sub-parts.
    """
    doc = soup.find("div", class_="doc")
    if doc is None:
        return 0

    in_section = False
    counter = 0
    actions = []

    for elem in doc.children:
        if not getattr(elem, "name", None):
            continue
        if elem.name in ("h1", "h2"):
            txt = elem.get_text(" ", strip=True)
            if PROBLEM_SECTION_RE.search(txt):
                in_section = True
                counter = 0
            else:
                in_section = False
        elif elem.name == "h3" and in_section:
            counter = 0
        elif elem.name == "ol" and in_section:
            counter += 1
            items = elem.find_all("li", recursive=False)
            actions.append((elem, counter, len(items) >= 2))

    fixed = 0
    for ol, n, has_subparts in actions:
        items = ol.find_all("li", recursive=False)
        if not items:
            continue

        stem_li = items[0]
        stem_p = soup.new_tag("p", **{"class": "problem-stem"})
        strong = soup.new_tag("strong")
        strong.string = f"{n}."
        stem_p.append(strong)
        stem_p.append(NavigableString(" "))
        for c in list(stem_li.contents):
            stem_p.append(c)

        ol.insert_before(stem_p)

        sub_ol = None
        if has_subparts:
            sub_ol = soup.new_tag("ol", type="a", **{"class": "problem-subparts"})
            for li in items[1:]:
                sub_ol.append(li.extract())
            ol.insert_before(sub_ol)

        anchor = sub_ol if sub_ol is not None else stem_p
        ol.decompose()

        nxt = anchor.find_next_sibling()
        if nxt and getattr(nxt, "name", None) == "details" and "solution" in (nxt.get("class") or []):
            for inner_ol in nxt.find_all("ol"):
                if has_subparts:
                    inner_ol["type"] = "a"

        fixed += 1
    return fixed


def split_merged_lists_after_solution(soup):
    """Mammoth merges adjacent <ol> lists across an empty `<p>Solution:</p>` boundary.

    For each <ol> immediately following a Solution paragraph, find the first <li>
    that looks like the start of the next question and split the list there.
    Items before the split are answers (stay with the Solution); items at and
    after the split are the next question (move to a new sibling <ol>).
    """
    splits = 0
    for p in list(soup.find_all("p")):
        text = p.get_text(" ", strip=True)
        m = SOLUTION_RE.match(text)
        if not m:
            continue
        if text[m.end():].strip():
            continue  # Solution has inline content; no following list to split
        nxt = p.next_sibling
        while isinstance(nxt, NavigableString) and not str(nxt).strip():
            nxt = nxt.next_sibling
        if not (nxt and getattr(nxt, "name", None) == "ol"):
            continue
        ol = nxt
        items = ol.find_all("li", recursive=False)
        split_at = None
        for i, li in enumerate(items):
            li_text = li.get_text(" ", strip=True)
            if not li_text:
                continue
            if i == 0:
                continue  # First item is always the start of the answer
            looks_like_question = (
                QUESTION_STARTERS.match(li_text)
                or li_text.endswith("?")
                or (len(li_text) > 50 and QUESTION_IMPERATIVE_MIDSENTENCE.search(li_text))
            )
            if looks_like_question:
                split_at = i
                break
        if split_at is None:
            continue
        new_ol = soup.new_tag("ol")
        new_ol["data-next-question"] = "1"
        for li in items[split_at:]:
            new_ol.append(li.extract())
        ol.insert_after(new_ol)
        splits += 1
    return splits


def wrap_solutions(soup):
    count = 0
    consumed = set()
    for p in list(soup.find_all("p")):
        if id(p) in consumed:
            continue
        text = p.get_text(" ", strip=True)
        m = SOLUTION_RE.match(text)
        if not m:
            continue
        count += 1
        body_inline_present = bool(text[m.end():].strip())
        strip_label_from_paragraph(p)

        details = soup.new_tag("details", **{"class": "solution"})
        summary = soup.new_tag("summary")
        summary.string = "Show solution"
        details.append(summary)
        p.insert_before(details)
        details.append(p.extract())
        consumed.add(id(p))

        if is_paragraph_empty(p):
            p.extract()

        # Walk forward and absorb continuation content into the details block.
        # When the Solution paragraph had no inline body, mammoth typically
        # left the answer in subsequent paragraphs/lists, and we want all of
        # them inside the details. When the Solution paragraph already has
        # inline math (the new factor-label format), the rewriter inserts
        # additional math <p> lines and an italic explanation <p> as siblings;
        # those must also be absorbed -- but we must stop before the next
        # question's <ol>, the next "Solution:"/"Answer:" paragraph, or any
        # heading / labelled section break.
        nxt = details.next_sibling
        while nxt is not None:
            if isinstance(nxt, NavigableString):
                nxt_next = nxt.next_sibling
                if str(nxt).strip() == "":
                    nxt.extract()
                    nxt = nxt_next
                    continue
                break
            if not getattr(nxt, "name", None):
                break
            if is_stop_element(nxt):
                break
            if body_inline_present and nxt.name != "p":
                # When the Solution had inline content, only continuation
                # <p> elements (extra math lines, italic explanation) belong
                # inside this details block. A following <ol> is the next
                # question's list and must remain outside.
                break
            if nxt.name == "p":
                # Stop at the next "Solution:" or "Answer:" paragraph -- it
                # belongs to the next problem and will be wrapped on its own.
                nxt_text = nxt.get_text(" ", strip=True)
                if SOLUTION_RE.match(nxt_text):
                    break
            nxt_next = nxt.next_sibling
            if nxt.name == "p":
                consumed.add(id(nxt))
            details.append(nxt.extract())
            nxt = nxt_next
    return count


def style_figure_descriptions(soup):
    fig_re = re.compile(r"^\s*(FIGURE\s+DESCRIPTION|Figure\s+\d+\.\d+)", re.IGNORECASE)
    label_re = re.compile(r"^\s*(Alt\s*text\s*:|Description\s*:|Caption\s*:)", re.IGNORECASE)
    paragraphs = soup.find_all("p")
    i = 0
    n = len(paragraphs)
    while i < n:
        p = paragraphs[i]
        text = p.get_text(" ", strip=True)
        if fig_re.match(text):
            group = [p]
            j = i + 1
            while j < n:
                nxt = paragraphs[j]
                if nxt.parent is not p.parent:
                    break
                ntext = nxt.get_text(" ", strip=True)
                if label_re.match(ntext) or fig_re.match(ntext):
                    group.append(nxt)
                    j += 1
                else:
                    break
            aside = soup.new_tag("aside", **{"class": "figure-description"})
            group[0].insert_before(aside)
            for g in group:
                aside.append(g.extract())
            i = j
        else:
            i += 1


def build_page(title, body_html, prev_link=None, next_link=None, index_link="index.html"):
    parts = []
    if prev_link:
        parts.append(f'<a href="{prev_link}" rel="prev">&larr; Previous</a>')
    else:
        parts.append("<span></span>")
    if index_link:
        parts.append(f'<a href="{index_link}">Contents</a>')
    else:
        parts.append("<span></span>")
    if next_link:
        parts.append(f'<a href="{next_link}" rel="next">Next &rarr;</a>')
    else:
        parts.append("<span></span>")
    nav_html = "\n  ".join(parts)
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<style>{CSS}</style>
<script>
window.MathJax = {{
  loader: {{ load: ['[tex]/cancel'] }},
  tex: {{
    packages: {{ '[+]': ['cancel'] }},
    inlineMath: [['\\\\(', '\\\\)']],
    displayMath: [['\\\\[', '\\\\]']]
  }},
  svg: {{ fontCache: 'global' }},
  startup: {{
    typeset: true
  }}
}};
</script>
<script async src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-chtml.js"></script>
</head>
<body>
<header class="site"><nav>
  {nav_html}
</nav></header>
<main class="container">
{body_html}
</main>
<footer class="site"><nav>
  {nav_html}
</nav></footer>
<script>{JS_PRINT_OPEN}</script>
</body>
</html>
"""


def collect_files():
    files = []
    fm = ROOT / "Front_Matter_Preface_License.docx"
    if fm.exists():
        files.append(("00_Front_Matter.html", fm, "Front Matter — Preface, License, Map"))
    for ch in sorted(ROOT.glob("Chapter_*.docx")):
        m = re.match(r"Chapter_(\d+)_(.+)\.docx", ch.name)
        if not m:
            continue
        num = m.group(1)
        title_slug = m.group(2).replace("_", " ")
        files.append((f"Chapter_{num}.html", ch, f"Chapter {int(num)} — {title_slug}"))
    for nm, outname, label in [
        ("Formula_and_Constant_Reference_Sheet.docx", "Formula_and_Constant_Reference_Sheet.html", "Formula & Constant Reference Sheet"),
        ("Periodic_Table_Reference_Page.docx", "Periodic_Table_Reference_Page.html", "Periodic Table Reference Page"),
        ("Index.docx", "Book_Index.html", "Index"),
    ]:
        p = ROOT / nm
        if p.exists():
            files.append((outname, p, label))
    return files


# Mammoth style-map: preserve strikethrough so the dimensional-analysis
# unit-cancellation marks survive into HTML. Mammoth's default mapping does
# not emit strikethrough, so we add an explicit rule.
MAMMOTH_STYLE_MAP = """
r[strikethrough] => s
"""


# ---------- MathJax / dimensional-analysis math rendering ---------------- #

# Plain-text math chains in the .docx (e.g. "2.50 km × (1000 m / 1 km) = 2500 m")
# are converted, post-mammoth, into MathJax LaTeX so cancelled units render
# with \cancel{} crossing them out. Strikethrough on units in the .docx
# survives mammoth as <s>...</s>; we read those tags to know which tokens
# to wrap in \cancel{}.

_SUP_MAP = str.maketrans({
    "⁰": "0", "¹": "1", "²": "2", "³": "3", "⁴": "4",
    "⁵": "5", "⁶": "6", "⁷": "7", "⁸": "8", "⁹": "9",
    "⁻": "-", "⁺": "+",
})

# Units we recognize and wrap in \text{} so they render upright. Order matters:
# longer compound units first so they win over shorter prefixes.
_UNIT_TOKENS = [
    "fl oz", "troy oz", "g alloy", "g solution", "g milk", "g fat", "g Ag", "g Zn",
    "g glucose", "g NaCl", "g CO₂", "g C", "g ethanol", "g gasoline",
    "kJ", "kcal", "kPa", "mol", "mmol",
    "kg", "mg", "ng", "µg", "ug",
    "km", "cm", "mm", "nm", "pm", "µm", "um",
    "mL", "dL", "µL", "uL", "cL",
    "min", "qt", "gal", "atm",
    "cup", "cups",
    "mi", "ft", "in", "yd", "lb", "oz",
    "Hz", "Pa", "h", "s", "g", "L", "m", "K", "J", "M",
    "°C", "°F",
]

_MATH_CHAIN_RE = re.compile(r"=")  # Pre-screen: must contain "="


def _is_math_chain(p):
    text = p.get_text(" ", strip=True)
    if not _MATH_CHAIN_RE.search(text):
        return False
    # Heuristic: math chain has × or a fraction marker " / " or arithmetic.
    if "×" in text or "÷" in text:
        return True
    if re.search(r"\(\s*[^()]+/\s*[^()]+\)", text):
        return True
    if re.search(r"\d\s*[+\-−]\s*\d", text):
        return True
    return False


def _paragraph_chunks(p):
    """Walk paragraph, returning a list of (text, is_struck) tuples."""
    chunks = []

    def walk(node, struck):
        for child in node.children:
            if isinstance(child, NavigableString):
                t = str(child)
                if t:
                    chunks.append((t, struck))
            elif getattr(child, "name", None) in ("s", "strike"):
                walk(child, True)
            else:
                walk(child, struck)

    walk(p, False)
    return chunks


def _convert_supers(s):
    def repl(m):
        digits = m.group(0).translate(_SUP_MAP)
        return "^{" + digits + "}"
    return re.sub(r"[⁰¹²³⁴⁵⁶⁷⁸⁹⁻⁺]+", repl, s)


_UNIT_PATTERN = re.compile(
    # Single regex with longest-first alternation so each substring is matched
    # at most once. The lookbehinds prevent matching units that are part of a
    # larger word ("kg" inside "kgmol") or already inside an emitted \text{}.
    r"(?<!\\text\{)"
    r"(?<![A-Za-zµ°])"
    + r"(" + "|".join(re.escape(u) for u in _UNIT_TOKENS) + r")"
    + r"(?![A-Za-z])"
)


def _wrap_units(s):
    """Wrap recognized unit tokens in \\text{} so they render upright."""
    return _UNIT_PATTERN.sub(lambda m: r"\text{" + m.group(1) + "}", s)


_LABEL_PREFIX_RE = re.compile(
    # Detect a leading English-language label like "Mass of solution =",
    # "Volume in 8.0 h =", "Student A:", "Dose mass =", "Rate =". The label
    # ends just before "=" or ":" and consists of multi-word natural text
    # (i.e. contains a lowercase letter and a space, OR a "Student X:" form).
    r"^\s*([A-Z][^=:]{2,40}?)\s*([:=])\s*"
)


def _split_label_and_math(s):
    """If s starts with an English-language label like 'Mass of solution =',
    return (label_text, sep, rest); otherwise return ("", "", s).

    Reject candidates whose "label" actually contains math content (strike
    markers, ``×``/``÷``/``→`` operators, or fraction-style ``(.../...)``).
    A Worked Example "Step 3 — 75.0 ⌐ft¬ × (...) = 900. in" line ends with
    ``=`` and looks superficially label-like, but emitting it as a label
    drops the math content into ``\\text{...}`` *before* strike-sentinel
    substitution runs -- so the ``\\x01...\\x02`` markers survive into
    output and Canvas's /equation_images/ endpoint chokes on them.
    """
    m = _LABEL_PREFIX_RE.match(s)
    if not m:
        return "", "", s
    label = m.group(1).strip()
    sep = m.group(2)
    # Heuristic: real labels contain a space (multi-word) OR the form
    # "Student X". A bare single math-token like "T_K" or "V" or "ρ"
    # shouldn't be wrapped -- those are math variables.
    if " " not in label and not re.match(r"Student\s+[A-Z]", label):
        return "", "", s
    # Reject if the candidate label contains math content. Strike markers
    # are the unambiguous signal; ``×``/``÷``/``→`` and ``(.../...)`` cover
    # the rest. Without this guard, "Step N — 75.0 ⌐ft¬ × (...) =" would
    # match as a 38-char "label" and bypass cancel-marker substitution.
    if any(c in label for c in ("\x01", "\x02", "×", "÷", "→")):
        return "", "", s
    if re.search(r"\([^()]*?/[^()]*?\)", label):
        return "", "", s
    return label, sep, s[m.end():]


def _math_text_to_latex(s):
    """Convert a plain-text math expression with \\x01...\\x02 markers
    around cancelled regions into a LaTeX math string.

    Order matters: unit wrapping happens BEFORE cancel-marker substitution
    so a struck "km" gets wrapped exactly once -> \\cancel{\\text{km}}.
    """
    # 0. Pull off any leading English-language label so it renders as text.
    label, sep, body = _split_label_and_math(s)
    s = body
    # 0b. Peel a trailing English parenthetical off the math expression so
    #     it renders upright via \text{...} instead of in italic math mode.
    #     Example: "... = 900. in (the period denotes the exact 3-sig-fig
    #     result)." -> math part is "... = 900. in", trailing is
    #     "(the period denotes the exact 3-sig-fig result)." rendered upright.
    trailing = ""
    m_trail = re.search(r"\s*(\([^()]{6,}\)\.?)\s*$", s)
    if m_trail:
        cand = m_trail.group(1)
        # English parentheticals contain spaces and lowercase letters and
        # don't look like a fraction (no slash splitting two units).
        if (" " in cand
                and re.search(r"[a-z]", cand)
                and not re.search(r"^\([^()]*?/[^()]*?\)\.?$", cand)):
            trailing = cand
            s = s[:m_trail.start()]
    # 1. Fractions: (X / Y) -> \dfrac{X}{Y}. Iterate to handle nested chains.
    for _ in range(4):
        new_s = re.sub(
            r"\(\s*([^()]+?)\s*/\s*([^()]+?)\s*\)",
            r"\\dfrac{\1}{\2}",
            s,
        )
        if new_s == s:
            break
        s = new_s
    # 2. Operators / arrows / Unicode minus / approximate
    s = s.replace("×", r" \times ")
    s = s.replace("÷", r" \div ")
    s = s.replace("→", r" \;\longrightarrow\; ")
    s = s.replace("−", "-")
    s = s.replace("≈", r" \approx ")
    s = s.replace("≤", r" \le ")
    s = s.replace("≥", r" \ge ")
    # 3. Superscript digits
    s = _convert_supers(s)
    # 4. Wrap units in \text{}. The \x01..\x02 strike markers are still in
    #    place and do not interfere with unit detection.
    s = _wrap_units(s)
    # 5. Now collapse strike markers into \cancel{...}. The unit inside is
    #    already wrapped in \text{}, so the result is \cancel{\text{km}}.
    s = re.sub(
        r"\x01(.+?)\x02",
        lambda m: r"\cancel{" + m.group(1).strip() + "}",
        s,
    )
    # 6. Escape LaTeX-special characters that survived from the source.
    #    "%" ends a TeX comment, so "100%" must become "100\%".
    #    "$" toggles math mode, so "$3.49" must become "\$3.49".
    s = s.replace("%", r"\%")
    s = s.replace("$", r"\$")
    # 7. Tidy double spaces
    s = re.sub(r" +", " ", s)
    s = s.strip()
    if label:
        s = r"\text{" + label + " " + sep + r"}\ " + s
    if trailing:
        s = s + r"\ \text{" + trailing + "}"
    return s


def _paragraph_to_latex(p):
    chunks = _paragraph_chunks(p)
    parts = []
    for text, struck in chunks:
        if struck:
            parts.append("\x01" + text + "\x02")
        else:
            parts.append(text)
    return _math_text_to_latex("".join(parts))


def mathjax_ify_solutions(soup):
    """Replace math-chain paragraphs anywhere in the doc with MathJax LaTeX.

    Restricted to paragraphs that contain at least one <s> strikethrough tag
    AND match the math-chain heuristic. The strikethrough acts as an
    explicit marker that the rewriter has been over this paragraph -- this
    keeps free-form prose and unrewritten chapters untouched.

    Originally this scanned only paragraphs inside <details class="solution">,
    but the Worked Example "Step N —" math chains live inside table cells
    (the EXAMPLE blocks are formatted as tables) and need the same
    treatment. Scanning globally is safe because the <s>-tag prerequisite
    keeps the conversion scoped to genuinely-rewritten paragraphs.
    """
    count = 0
    for p in list(soup.find_all("p")):
        if not p.find(["s", "strike"]):
            continue
        if not _is_math_chain(p):
            continue
        latex = _paragraph_to_latex(p)
        p.clear()
        classes = p.get("class") or []
        classes.append("math-chain")
        p["class"] = classes
        p.append(NavigableString(f"\\[{latex}\\]"))
        count += 1
    return count


def convert_one(docx_path):
    with open(docx_path, "rb") as f:
        result = mammoth.convert_to_html(f, style_map=MAMMOTH_STYLE_MAP)
    soup = BeautifulSoup(f'<div class="doc">{result.value}</div>', "html.parser")
    style_figure_descriptions(soup)
    n_splits = split_merged_lists_after_solution(soup)
    n_solutions = wrap_solutions(soup)
    n_renumbered = restructure_problem_sets(soup)
    n_math = mathjax_ify_solutions(soup)
    for ol in soup.find_all("ol", attrs={"data-next-question": True}):
        del ol["data-next-question"]
    return str(soup), n_solutions, n_splits, n_renumbered, n_math, result.messages


def build_index(files):
    items = []
    for outname, _src, label in files:
        items.append(f'  <li><a href="{outname}">{label}</a></li>')
    body = (
        "<h1>CHEM 139 — General Chemistry Prep</h1>\n"
        "<p><em>Open Educational Resource (2026 ed.) — CC BY 4.0</em></p>\n"
        "<p>HTML edition. Solutions to practice problems are hidden by default — click "
        "the <strong>Show solution</strong> pill to reveal an answer.</p>\n"
        "<h2>Contents</h2>\n"
        "<ol class=\"toc\">\n" + "\n".join(items) + "\n</ol>\n"
    )
    return build_page("CHEM 139 — Contents", body, index_link=None)


def main():
    files = collect_files()
    print(f"Found {len(files)} source files.")
    total_solutions = 0
    for i, (outname, src, label) in enumerate(files):
        prev_link = files[i - 1][0] if i > 0 else None
        next_link = files[i + 1][0] if i + 1 < len(files) else None
        print(f"  {src.name} -> {outname}")
        try:
            body, n_sol, n_splits, n_renum, n_math, _msgs = convert_one(src)
        except Exception as e:
            print(f"    ERROR: {e}")
            continue
        total_solutions += n_sol
        page = build_page(label, body, prev_link, next_link)
        (OUT / outname).write_text(page, encoding="utf-8")
        print(f"    {n_sol} solutions wrapped, {n_splits} merged lists split, {n_renum} problems renumbered, {n_math} math chains -> LaTeX")
    (OUT / "index.html").write_text(build_index(files), encoding="utf-8")
    print(f"\nTotal: {total_solutions} solution blocks across {len(files)} files.")
    print(f"Open: {OUT / 'index.html'}")


if __name__ == "__main__":
    main()
