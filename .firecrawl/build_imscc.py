"""Build a Canvas-importable IMS Common Cartridge (.imscc) of the OER.

The output is a single ZIP file at the repo root, ``CHEM_139_OER.imscc``,
that contains every Canvas-tailored chapter HTML (from HTML_Files_Canvas/)
plus an ``imsmanifest.xml`` that organizes the pages into one Module per
chapter. Canvas imports it via:

    Settings -> Import Course Content -> Canvas Course Export Package
                                          (or "Common Cartridge 1.x Package")

Each HTML resource becomes a Canvas Page; chapters become Modules with
the pages added in order. If a chapter HTML references images by
relative path (``<img src="images/foo.svg">``), those images are
bundled into the cartridge automatically and Canvas rewrites the
``src`` attributes to per-course Canvas File URLs at import time --
solving the image-deployment problem without any per-instance
configuration.

Usage:
    python .firecrawl/build_imscc.py                       # default
    python .firecrawl/build_imscc.py --out my_export.imscc # custom path
"""
from __future__ import annotations

import argparse
import io
import re
import sys
import uuid
import zipfile
from pathlib import Path
from xml.dom import minidom
from xml.etree.ElementTree import Element, SubElement, tostring

from bs4 import BeautifulSoup

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = ROOT / "HTML_Files_Canvas"
DEFAULT_OUT = ROOT / "CHEM_139_OER.imscc"


# Page ordering for the cartridge. Each entry is (filename, module_title,
# page_title). Front and back matter live in their own one-page "modules"
# at the top and bottom; chapters get their own modules in between.
PAGE_ORDER: list[tuple[str, str, str]] = [
    ("00_Front_Matter.html",
        "Front Matter",
        "Front Matter — Preface, License, Map"),
    ("Chapter_01.html",
        "Chapter 1 — Science and Measurement",
        "Chapter 1: Science and Measurement"),
    ("Chapter_02.html",
        "Chapter 2 — Unit Systems and Dimensional Analysis",
        "Chapter 2: Unit Systems and Dimensional Analysis"),
    ("Chapter_03.html",
        "Chapter 3 — Basic Concepts About Matter",
        "Chapter 3: Basic Concepts About Matter"),
    ("Chapter_04.html",
        "Chapter 4 — Atoms, Molecules, Subatomic Particles",
        "Chapter 4: Atoms, Molecules, Subatomic Particles"),
    ("Chapter_05.html",
        "Chapter 5 — Electronic Structure and Periodicity",
        "Chapter 5: Electronic Structure and Periodicity"),
    ("Chapter_06.html",
        "Chapter 6 — Chemical Bonds",
        "Chapter 6: Chemical Bonds"),
    ("Chapter_07.html",
        "Chapter 7 — Chemical Nomenclature",
        "Chapter 7: Chemical Nomenclature"),
    ("Chapter_08.html",
        "Chapter 8 — Mole Concept and Chemical Formulas",
        "Chapter 8: Mole Concept and Chemical Formulas"),
    ("Chapter_09.html",
        "Chapter 9 — Chemical Calculations and Equations",
        "Chapter 9: Chemical Calculations and Equations"),
    ("Chapter_10.html",
        "Chapter 10 — States of Matter",
        "Chapter 10: States of Matter"),
    ("Formula_and_Constant_Reference_Sheet.html",
        "Reference Pages",
        "Formula and Constant Reference Sheet"),
    ("Periodic_Table_Reference_Page.html",
        "Reference Pages",
        "Periodic Table Reference Page"),
    ("Book_Index.html",
        "Reference Pages",
        "Index"),
]


# IMS CC 1.1 namespaces. These are mandated; do not change.
CC_NS = "http://www.imsglobal.org/xsd/imsccv1p1/imscp_v1p1"
LOM_RES_NS = "http://ltsc.ieee.org/xsd/imsccv1p1/LOM/resource"
LOM_MAN_NS = "http://ltsc.ieee.org/xsd/imsccv1p1/LOM/manifest"
XSI_NS = "http://www.w3.org/2001/XMLSchema-instance"

SCHEMA_LOCATION = (
    "http://www.imsglobal.org/xsd/imsccv1p1/imscp_v1p1 "
    "http://www.imsglobal.org/profile/cc/ccv1p1/ccv1p1_imscp_v1p2_v1p0.xsd "
    "http://ltsc.ieee.org/xsd/imsccv1p1/LOM/resource "
    "http://www.imsglobal.org/profile/cc/ccv1p1/LOM/ccv1p1_lomresource_v1p0.xsd "
    "http://ltsc.ieee.org/xsd/imsccv1p1/LOM/manifest "
    "http://www.imsglobal.org/profile/cc/ccv1p1/LOM/ccv1p1_lommanifest_v1p0.xsd"
)


def _ident(prefix: str) -> str:
    """Cartridge-unique identifier; the prefix makes the manifest readable."""
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


def find_local_image_refs(html_path: Path) -> list[str]:
    """Return every <img src="..."> value that points at a local file
    (relative path, no scheme) found in `html_path`. Used to bundle
    referenced figures into the cartridge."""
    soup = BeautifulSoup(html_path.read_text(encoding="utf-8"), "html.parser")
    out: list[str] = []
    for img in soup.find_all("img"):
        src = (img.get("src") or "").strip()
        if not src:
            continue
        # Skip absolute URLs and data URIs; those don't need bundling.
        if re.match(r"^(https?:|//|data:)", src):
            continue
        out.append(src)
    return out


def build_manifest(
    pages: list[tuple[str, str, str]],
    image_files: list[Path],
) -> str:
    """Construct an IMS CC 1.1 manifest for the given pages and bundled images.

    Pages become webcontent resources; images become extra webcontent
    resources referenced by the pages. Modules in Canvas come from the
    `<organization>` hierarchy: items at depth 1 are modules; items at
    depth 2 are pages within a module.
    """
    manifest_id = _ident("M")

    manifest = Element(
        "manifest",
        {
            "identifier": manifest_id,
            "xmlns": CC_NS,
            "xmlns:lom": LOM_RES_NS,
            "xmlns:lomimscc": LOM_MAN_NS,
            "xmlns:xsi": XSI_NS,
            "xsi:schemaLocation": SCHEMA_LOCATION,
        },
    )

    # ----- metadata --------------------------------------------------------
    meta = SubElement(manifest, "metadata")
    SubElement(meta, "schema").text = "IMS Common Cartridge"
    SubElement(meta, "schemaversion").text = "1.1.0"
    lom = SubElement(meta, "lomimscc:lom")
    general = SubElement(lom, "lomimscc:general")
    title_el = SubElement(general, "lomimscc:title")
    SubElement(title_el, "lomimscc:string").text = (
        "CHEM 139 — Introduction to Chemical Principles (2026 ed.)"
    )
    desc_el = SubElement(general, "lomimscc:description")
    SubElement(desc_el, "lomimscc:string").text = (
        "Open Educational Resource. CC BY 4.0. "
        "10-chapter introductory chemistry textbook with interactive "
        "Show/Hide solution toggles and MathJax-typeset factor-label math."
    )

    # ----- organizations: chapter -> page tree ----------------------------
    orgs = SubElement(manifest, "organizations")
    org = SubElement(
        orgs,
        "organization",
        {
            "identifier": _ident("O"),
            "structure": "rooted-hierarchy",
        },
    )
    root_item = SubElement(org, "item", {"identifier": _ident("I_root")})

    # Group pages by module title (the second tuple element).
    grouped: list[tuple[str, list[tuple[str, str, str, str]]]] = []
    # Each leaf entry: (filename, page_title, resource_id, item_id)
    page_resources: list[tuple[str, str, str, str]] = []

    last_module: str | None = None
    current_group: list[tuple[str, str, str, str]] = []
    for filename, module_title, page_title in pages:
        resource_id = _ident("R")
        item_id = _ident("I")
        page_resources.append((filename, page_title, resource_id, item_id))
        if module_title != last_module:
            if current_group:
                grouped.append((last_module, current_group))
            current_group = [(filename, page_title, resource_id, item_id)]
            last_module = module_title
        else:
            current_group.append(
                (filename, page_title, resource_id, item_id)
            )
    if current_group:
        grouped.append((last_module, current_group))

    for module_title, leaves in grouped:
        module_item = SubElement(
            root_item, "item", {"identifier": _ident("I_mod")}
        )
        SubElement(module_item, "title").text = module_title
        for filename, page_title, resource_id, item_id in leaves:
            page_item = SubElement(
                module_item,
                "item",
                {"identifier": item_id, "identifierref": resource_id},
            )
            SubElement(page_item, "title").text = page_title

    # ----- resources: HTML pages + bundled images ------------------------
    resources = SubElement(manifest, "resources")
    for filename, _page_title, resource_id, _item_id in page_resources:
        href = f"web_resources/{filename}"
        resource = SubElement(
            resources,
            "resource",
            {
                "identifier": resource_id,
                "type": "webcontent",
                "href": href,
            },
        )
        SubElement(resource, "file", {"href": href})

    # Image resources (one resource per image file). Each image is
    # referenced by relative path from the HTML pages, so Canvas will
    # rewrite the src on import.
    for img_path in image_files:
        rel = f"web_resources/{img_path.relative_to(ROOT).as_posix()}"
        resource = SubElement(
            resources,
            "resource",
            {
                "identifier": _ident("R_img"),
                "type": "webcontent",
                "href": rel,
            },
        )
        SubElement(resource, "file", {"href": rel})

    raw = tostring(manifest, encoding="utf-8")
    # Pretty-print so the manifest is readable when unzipped.
    return minidom.parseString(raw).toprettyxml(indent="  ", encoding="utf-8").decode("utf-8")


def collect_referenced_images(pages: list[tuple[str, str, str]]) -> list[Path]:
    """For every HTML page, find the local <img src="..."> targets and
    resolve them to actual files on disk. Returns a deduped list of
    absolute paths to bundle. Images that are referenced but do not
    exist on disk are skipped with a warning -- the cartridge will still
    import; the broken <img> just renders as the alt text in Canvas."""
    seen: dict[Path, None] = {}
    for filename, _module, _title in pages:
        page_path = SRC_DIR / filename
        if not page_path.exists():
            continue
        for src in find_local_image_refs(page_path):
            # Resolve relative to the HTML file's directory.
            candidate = (SRC_DIR / src).resolve()
            if not candidate.exists():
                # Fall back to repo-root-relative.
                alt = (ROOT / src).resolve()
                if alt.exists():
                    candidate = alt
                else:
                    print(f"WARN: image referenced but not found: {src}")
                    continue
            seen.setdefault(candidate, None)
    return list(seen.keys())


def build_cartridge(out_path: Path) -> dict:
    if not SRC_DIR.exists():
        sys.exit(
            f"Source dir missing: {SRC_DIR}\n"
            f"Run .firecrawl/build_canvas.py first."
        )

    # Filter to pages that actually exist (so a partial build still works).
    pages = [
        (f, mod, title)
        for f, mod, title in PAGE_ORDER
        if (SRC_DIR / f).exists()
    ]
    missing = [f for f, _, _ in PAGE_ORDER if not (SRC_DIR / f).exists()]
    if missing:
        print(f"NOTE: {len(missing)} expected page(s) not found; skipping: "
              f"{', '.join(missing)}")

    image_files = collect_referenced_images(pages)
    manifest_xml = build_manifest(pages, image_files)

    with zipfile.ZipFile(out_path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("imsmanifest.xml", manifest_xml)
        for filename, _mod, _title in pages:
            arcname = f"web_resources/{filename}"
            zf.write(SRC_DIR / filename, arcname)
        for img in image_files:
            arcname = f"web_resources/{img.relative_to(ROOT).as_posix()}"
            zf.write(img, arcname)

    return {
        "pages": len(pages),
        "images": len(image_files),
        "out": out_path,
        "size_kb": out_path.stat().st_size // 1024,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Build IMS Common Cartridge.")
    parser.add_argument(
        "--out",
        type=Path,
        default=DEFAULT_OUT,
        help="Output .imscc path (default: ./CHEM_139_OER.imscc).",
    )
    args = parser.parse_args()

    stats = build_cartridge(args.out)
    print(
        f"Cartridge built: {stats['out']}\n"
        f"  Pages bundled : {stats['pages']}\n"
        f"  Images bundled: {stats['images']}\n"
        f"  Size          : {stats['size_kb']} KB"
    )
    print(
        "\nImport in Canvas:\n"
        "  Course -> Settings -> Import Course Content\n"
        "  Content type: 'Canvas Course Export Package' "
        "(also accepts 'Common Cartridge 1.x Package')\n"
        f"  Source: {stats['out'].name}\n"
    )


if __name__ == "__main__":
    main()
