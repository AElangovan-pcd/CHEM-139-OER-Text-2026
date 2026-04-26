"""Generate copy-paste-ready Canvas Page HTML from the existing HTML_Files.

Output: ``HTML_Files_Canvas/<basename>.html`` for each chapter / front-matter /
back-matter file. Each output:

  * Strips the page chrome (no <html>/<head>, no nav header/footer).
  * Inlines the static CSS rules onto each matched element so styling
    survives the Canvas Page sanitizer.
  * Keeps a small <style> block at the top for state-dependent rules
    (``details[open]`` label swap, hover, ::before arrow). Most Canvas
    instances preserve <style> inside Page content; if a stricter
    sanitizer strips it, the page still works -- only the open-state
    label swap and the custom arrow are lost.
  * Replaces the JS-driven "Show solution / Hide solution" swap with a
    CSS-only two-span technique that works in Canvas without scripts.
  * Strips all <script> tags (Canvas removes JS anyway).
  * Removes the per-page MathJax bootstrap; Canvas ships its own MathJax
    that recognises ``\\(...\\)`` and ``\\[...\\]`` delimiters globally.
  * Optionally rewrites ``<img src="...">`` paths via a JSON map (so
    once images are uploaded to Canvas Files, one ``image_map.json``
    flips every reference to the canonical Canvas URL).

Open the generated ``.html`` in a browser to preview. To paste into
Canvas: open the page in your editor, copy everything in the file, then
in Canvas click the ``</>`` HTML editor button on the Page and paste.

Usage:
    python .firecrawl/build_canvas.py
    python .firecrawl/build_canvas.py --image-map images.json
"""
from __future__ import annotations

import argparse
import io
import json
import re
import sys
from pathlib import Path

from bs4 import BeautifulSoup, NavigableString, Tag

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = ROOT / "HTML_Files"
OUT_DIR = ROOT / "HTML_Files_Canvas"


# ---------- inline CSS rules ----------------------------------------------- #
# Rules that target a static element (no :hover / [open] / ::before). These
# are pushed onto each matched element's `style` attribute.
INLINE_RULES = [
    (
        "main.container",
        "max-width:800px;margin:1.5rem auto 3rem;padding:2.5rem;background:#fff;"
        "border:1px solid #d8d8d8;font-family:Georgia,'Times New Roman',serif;"
        "color:#1a1a1a;line-height:1.65;"
    ),
    ("h1", "font-family:-apple-system,system-ui,Helvetica,Arial,sans-serif;"
           "color:#111;line-height:1.25;font-size:1.95rem;"
           "border-bottom:2px solid #0b5cad;padding-bottom:0.4rem;"
           "margin:1.5em 0 0.5em;"),
    ("h2", "font-family:-apple-system,system-ui,Helvetica,Arial,sans-serif;"
           "color:#0b5cad;line-height:1.25;font-size:1.45rem;margin:1.5em 0 0.5em;"),
    ("h3", "font-family:-apple-system,system-ui,Helvetica,Arial,sans-serif;"
           "color:#111;line-height:1.25;font-size:1.15rem;margin:1.5em 0 0.5em;"),
    ("h4", "font-family:-apple-system,system-ui,Helvetica,Arial,sans-serif;"
           "color:#333;line-height:1.25;font-size:1rem;margin:1.5em 0 0.5em;"),
    ("p", "margin:0.7em 0;"),
    ("ol, ul", "padding-left:1.6rem;"),
    ("li", "margin:0.25em 0;"),
    ("table", "border-collapse:collapse;margin:1rem 0;font-size:0.95rem;"),
    ("th", "border:1px solid #d8d8d8;padding:0.4rem 0.7rem;text-align:left;"
           "vertical-align:top;background:#e8f0fb;"),
    ("td", "border:1px solid #d8d8d8;padding:0.4rem 0.7rem;text-align:left;"
           "vertical-align:top;"),
    ("a", "color:#0b5cad;"),
    ("strong", "color:#000;"),
    ("img", "max-width:100%;height:auto;display:block;margin:1rem auto;"
            "border-radius:4px;"),
    ("figure", "margin:1.2rem 0;text-align:center;"),
    ("figcaption", "font-size:0.9rem;color:#555;margin-top:0.4rem;font-style:italic;"),
    ("aside.figure-description",
        "background:#f3f3f3;border-left:4px solid #b9b9b9;padding:0.9rem 1.1rem;"
        "margin:1.2rem 0;font-size:0.95rem;"),
    ("p.problem-stem", "margin-top:1.4em;margin-bottom:0.4em;"),
    ("p.math-chain", "text-align:left;margin:0.4em 0;overflow-x:auto;"),
    ("details.solution",
        "background:#eef7ee;border-left:4px solid #2e7d32;padding:0.55rem 1rem;"
        "margin:0.6rem 0 1.1rem;border-radius:4px;"),
    ("details.solution > summary",
        "cursor:pointer;font-weight:600;color:#2e7d32;"
        "font-family:-apple-system,system-ui,Helvetica,Arial,sans-serif;"
        "list-style:none;display:inline-block;padding:0.3rem 0.85rem;"
        "background:#fff;border:1px solid #2e7d32;border-radius:999px;"
        "user-select:none;font-size:0.9rem;"),
    ("details.solution s",
        "text-decoration:line-through;text-decoration-color:#c0392b;"
        "text-decoration-thickness:0.12em;"),
]


# State-dependent rules that can ONLY live in a <style> block.
SCOPED_STYLE_BLOCK = """
<style>
/* Scoped to .oer-page so this CSS does not leak into Canvas chrome. */
.oer-page details.solution[open] { padding-bottom: 0.9rem; }
.oer-page details.solution > summary::-webkit-details-marker { display: none; }
.oer-page details.solution > summary:hover {
  background: #2e7d32 !important;
  color: #fff !important;
}
/* Show / Hide solution label swap (CSS-only, no JS). */
.oer-page details.solution > summary > .oer-hide-label { display: none; }
.oer-page details.solution[open] > summary > .oer-show-label { display: none; }
.oer-page details.solution[open] > summary > .oer-hide-label { display: inline; }
@media print {
  .oer-page details.solution { background: none !important; border: 1px dashed #888 !important; }
  .oer-page details.solution > summary { display: none !important; }
}
</style>
""".strip()


# ---------- transformations ----------------------------------------------- #


def merge_style(el: Tag, css: str) -> None:
    """Append `css` to the element's existing `style` attribute, deduping."""
    existing = (el.get("style") or "").strip()
    if existing and not existing.endswith(";"):
        existing += ";"
    el["style"] = existing + css


def inline_static_css(soup: BeautifulSoup) -> None:
    for selector, css in INLINE_RULES:
        try:
            matches = soup.select(selector)
        except Exception:
            continue
        for el in matches:
            merge_style(el, css)


def swap_solution_summary(soup: BeautifulSoup) -> int:
    """Replace each <summary>Show solution</summary> with a two-span CSS swap."""
    count = 0
    for details in soup.select("details.solution"):
        summary = details.find("summary", recursive=False)
        if not summary:
            continue
        summary.clear()
        show_span = soup.new_tag("span", **{"class": "oer-show-label"})
        show_span.string = "Show solution"
        hide_span = soup.new_tag(
            "span",
            **{"class": "oer-hide-label", "style": "display:none;"},
        )
        hide_span.string = "Hide solution"
        summary.append(show_span)
        summary.append(hide_span)
        count += 1
    return count


def strip_scripts(soup: BeautifulSoup) -> int:
    n = 0
    for s in soup.find_all("script"):
        s.decompose()
        n += 1
    return n


def apply_image_map(soup: BeautifulSoup, image_map: dict) -> int:
    if not image_map:
        return 0
    n = 0
    for img in soup.find_all("img"):
        src = img.get("src", "")
        if src in image_map:
            img["src"] = image_map[src]
            n += 1
    return n


# ---------- per-file build ------------------------------------------------- #


def transform_one(src: Path, image_map: dict) -> tuple[str, dict]:
    raw = src.read_text(encoding="utf-8")
    soup = BeautifulSoup(raw, "html.parser")

    # The chapter content sits inside <main class="container">. Pull just that.
    main = soup.find("main", class_="container")
    if main is None:
        # Fallback: take the body.
        main = soup.find("body") or soup
    inner = BeautifulSoup(main.decode_contents(), "html.parser")

    n_scripts = strip_scripts(inner)
    n_summaries = swap_solution_summary(inner)
    n_imgs = apply_image_map(inner, image_map)
    inline_static_css(inner)

    # Wrap the content in .oer-page so the scoped <style> rules apply.
    wrapper = BeautifulSoup(
        '<div class="oer-page" '
        'style="font-family:Georgia,\'Times New Roman\',serif;color:#1a1a1a;'
        'line-height:1.65;"></div>',
        "html.parser",
    )
    div = wrapper.find("div")
    div.append(inner)

    out_html = SCOPED_STYLE_BLOCK + "\n" + str(wrapper)
    return out_html, {
        "scripts_stripped": n_scripts,
        "summaries_swapped": n_summaries,
        "images_remapped": n_imgs,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Build Canvas-ready HTML pages.")
    parser.add_argument(
        "--image-map",
        type=Path,
        help="Optional JSON file mapping <img src> values to Canvas File URLs.",
    )
    args = parser.parse_args()

    image_map: dict = {}
    if args.image_map:
        if not args.image_map.exists():
            sys.exit(f"image map not found: {args.image_map}")
        image_map = json.loads(args.image_map.read_text(encoding="utf-8"))
        print(f"Loaded {len(image_map)} image mappings.")

    if not SRC_DIR.exists():
        sys.exit(
            f"Source directory missing: {SRC_DIR}\n"
            f"Run .firecrawl/build_html.py first."
        )

    OUT_DIR.mkdir(exist_ok=True)
    files = sorted(SRC_DIR.glob("*.html"))
    if not files:
        sys.exit(f"No HTML files found in {SRC_DIR}")

    print(f"Building {len(files)} Canvas page(s) -> {OUT_DIR}/")
    totals = {"scripts_stripped": 0, "summaries_swapped": 0, "images_remapped": 0}
    for src in files:
        if src.name in {"index.html"}:
            # The contents page is local-only navigation; skip it for Canvas.
            continue
        out_html, stats = transform_one(src, image_map)
        out_path = OUT_DIR / src.name
        out_path.write_text(out_html, encoding="utf-8")
        for k in totals:
            totals[k] += stats[k]
        print(
            f"  {src.name:40s} -> {out_path.name}   "
            f"summaries: {stats['summaries_swapped']:3d}, "
            f"images: {stats['images_remapped']:3d}"
        )

    print(
        f"\nTotal: {totals['summaries_swapped']} solution toggles, "
        f"{totals['images_remapped']} images remapped, "
        f"{totals['scripts_stripped']} scripts stripped."
    )
    print(f"Output: {OUT_DIR}")


if __name__ == "__main__":
    main()
