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

# Resource type identifiers. Canvas's IMSCC importer dispatches on these:
# - WIKI_PAGE_TYPE causes the resource to be imported as a Canvas Page
#   (with the HTML body extracted from the file). This requires the file
#   to be located under "wiki_content/" by Canvas convention.
# - WEB_CONTENT_TYPE causes the resource to be imported as a File in the
#   course Files area (used here for bundled images).
WIKI_PAGE_TYPE = "associatedcontent/imscc_xmlv1p1/learning-application-resource"
WEB_CONTENT_TYPE = "webcontent"

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


def _slug(filename: str) -> str:
    """Turn a chapter HTML filename into the slug Canvas uses for the
    wiki_content/<slug>/<slug>.html directory layout.

    "Chapter_01.html" -> "chapter-01"
    "00_Front_Matter.html" -> "00-front-matter"
    """
    stem = Path(filename).stem
    return stem.lower().replace("_", "-")


def build_grouped_structure(
    pages: list[tuple[str, str, str]],
) -> list[dict]:
    """Build a per-module grouped structure shared by the manifest, the
    Canvas module_meta.xml, and the page wrapper. Each top-level dict is
    one module; each item in `items` is one Wiki Page.

    Returns a list of:
        {
          "module_id":   str,
          "title":       str,
          "items": [
             {
               "filename":    "Chapter_01.html",
               "slug":        "chapter-01",
               "page_id":     str,           # also identifier on the org item
               "page_title":  "Chapter 1: ...",
               "resource_id": str,           # matches manifest <resource>
               "item_id":     str,           # matches module_meta <item>
             },
             ...
          ],
        }
    """
    groups: list[dict] = []
    last_module: str | None = None
    for filename, module_title, page_title in pages:
        page = {
            "filename": filename,
            "slug": _slug(filename),
            "page_id": _ident("g_page"),
            "page_title": page_title,
            "resource_id": _ident("g_res"),
            "item_id": _ident("g_item"),
        }
        if module_title != last_module:
            groups.append(
                {
                    "module_id": _ident("g_mod"),
                    "title": module_title,
                    "items": [page],
                }
            )
            last_module = module_title
        else:
            groups[-1]["items"].append(page)
    return groups


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
        # Skip absolute URLs, protocol-relative URLs, data URIs, and any
        # server-relative path (starts with "/") — the latter covers Canvas's
        # ``/equation_images/...`` URLs produced by build_canvas.py for
        # server-rendered LaTeX, which must not be bundled as local files.
        if re.match(r"^(https?:|//|data:|/)", src):
            continue
        out.append(src)
    return out


def build_manifest(
    groups: list[dict],
    image_files: list[Path],
) -> str:
    """Construct an IMS CC 1.1 manifest for the given pre-grouped pages and
    bundled images. The same identifiers used here are referenced from
    course_settings/module_meta.xml so Canvas can match items across
    files.

    Pages become learning-application-resource entries; images stay as
    webcontent. Modules in Canvas come from the ``<organization>``
    hierarchy: items at depth 1 are modules; items at depth 2 are pages.
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
        "CHEM 139 — General Chemistry Prep (2026 ed.)"
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

    for grp in groups:
        module_item = SubElement(
            root_item, "item", {"identifier": grp["module_id"]}
        )
        SubElement(module_item, "title").text = grp["title"]
        for page in grp["items"]:
            page_item = SubElement(
                module_item,
                "item",
                {
                    "identifier": page["item_id"],
                    "identifierref": page["resource_id"],
                },
            )
            SubElement(page_item, "title").text = page["page_title"]

    # ----- resources: HTML pages + bundled images ------------------------
    resources = SubElement(manifest, "resources")
    for grp in groups:
        for page in grp["items"]:
            # Canvas's Canvas-flavored importer expects each Wiki Page in
            # its own subdirectory: wiki_content/<slug>/<slug>.html . That
            # layout plus the canvas_export.txt marker file and a
            # course_settings/module_meta.xml entry tagging this resource
            # as <content_type>WikiPage</content_type> is what makes
            # Canvas treat the HTML as a Page rather than a generic File.
            href = f"wiki_content/{page['slug']}/{page['slug']}.html"
            resource = SubElement(
                resources,
                "resource",
                {
                    "identifier": page["resource_id"],
                    "type": WIKI_PAGE_TYPE,
                    "href": href,
                },
            )
            SubElement(resource, "file", {"href": href})

    # Image resources stay as webcontent in web_resources/ so Canvas
    # imports them as Files and rewrites <img src=...> on each Page to
    # the canonical Canvas Files URL at import time.
    for img_path in image_files:
        rel = f"web_resources/{img_path.relative_to(ROOT).as_posix()}"
        resource = SubElement(
            resources,
            "resource",
            {
                "identifier": _ident("R_img"),
                "type": WEB_CONTENT_TYPE,
                "href": rel,
            },
        )
        SubElement(resource, "file", {"href": rel})

    raw = tostring(manifest, encoding="utf-8")
    # Pretty-print so the manifest is readable when unzipped.
    return minidom.parseString(raw).toprettyxml(indent="  ", encoding="utf-8").decode("utf-8")


# Canvas's own xsd schema for the content of course_settings/. Required by
# Canvas's Canvas-flavored importer (the one that creates Pages, Modules,
# etc.) - the standard CC importer ignores course_settings/ entirely.
CANVAS_NS = "http://canvas.instructure.com/xsd/cccv1p0"
CANVAS_SCHEMA_LOCATION = (
    "http://canvas.instructure.com/xsd/cccv1p0 "
    "https://canvas.instructure.com/xsd/cccv1p0.xsd"
)


def _pretty(elem: Element) -> str:
    """ElementTree -> pretty UTF-8 XML string."""
    return minidom.parseString(
        tostring(elem, encoding="utf-8")
    ).toprettyxml(indent="  ", encoding="utf-8").decode("utf-8")


def build_module_meta(groups: list[dict]) -> str:
    """Build course_settings/module_meta.xml.

    This is the file that tells Canvas's Pages-aware importer that each
    item under each module is specifically a WikiPage (rather than a
    File, Quiz, Discussion, etc.). The identifiers here MUST match the
    organization-tree item identifiers in the manifest.
    """
    root = Element(
        "modules",
        {
            "xmlns": CANVAS_NS,
            "xmlns:xsi": XSI_NS,
            "xsi:schemaLocation": CANVAS_SCHEMA_LOCATION,
        },
    )
    for position, grp in enumerate(groups, start=1):
        module = SubElement(
            root, "module", {"identifier": grp["module_id"]}
        )
        SubElement(module, "title").text = grp["title"]
        SubElement(module, "workflow_state").text = "active"
        SubElement(module, "position").text = str(position)
        SubElement(module, "require_sequential_progress").text = "false"
        SubElement(module, "locked").text = "false"
        items = SubElement(module, "items")
        for item_pos, page in enumerate(grp["items"], start=1):
            item = SubElement(
                items, "item", {"identifier": page["item_id"]}
            )
            SubElement(item, "content_type").text = "WikiPage"
            SubElement(item, "workflow_state").text = "published"
            SubElement(item, "title").text = page["page_title"]
            SubElement(item, "identifierref").text = page["resource_id"]
            SubElement(item, "position").text = str(item_pos)
            SubElement(item, "new_tab").text = "false"
            SubElement(item, "indent").text = "0"
            SubElement(item, "link_settings_json").text = "null"
    return _pretty(root)


def build_course_settings(course_id: str, course_title: str) -> str:
    """Build course_settings/course_settings.xml — minimal course-level
    metadata. Canvas's Pages-aware importer expects this file to exist
    (alongside canvas_export.txt and module_meta.xml). Most fields are
    optional; we provide just the title and code so Canvas has something
    to display."""
    root = Element(
        "course",
        {
            "identifier": course_id,
            "xmlns": CANVAS_NS,
            "xmlns:xsi": XSI_NS,
            "xsi:schemaLocation": CANVAS_SCHEMA_LOCATION,
        },
    )
    SubElement(root, "title").text = course_title
    SubElement(root, "course_code").text = "CHEM 139"
    SubElement(root, "is_public").text = "false"
    return _pretty(root)


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

    groups = build_grouped_structure(pages)
    image_files = collect_referenced_images(pages)
    manifest_xml = build_manifest(groups, image_files)
    module_meta_xml = build_module_meta(groups)
    course_settings_xml = build_course_settings(
        course_id=_ident("g_course"),
        course_title="CHEM 139 — General Chemistry Prep (2026 ed.)",
    )

    with zipfile.ZipFile(out_path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("imsmanifest.xml", manifest_xml)

        # Canvas-flavored cartridge marker. Canvas's importer dispatches to
        # the Pages-aware code path only when this file is present AND
        # module_meta.xml + course_settings.xml are alongside it. Contents
        # of the marker are not parsed; presence is the trigger.
        zf.writestr(
            "course_settings/canvas_export.txt",
            "Canvas Course Export marker — CHEM 139 OER\n",
        )
        zf.writestr("course_settings/course_settings.xml", course_settings_xml)
        zf.writestr("course_settings/module_meta.xml", module_meta_xml)

        for grp in groups:
            for page in grp["items"]:
                # The arcname here MUST match the href in build_manifest()
                # and the identifierref in build_module_meta().
                arcname = (
                    f"wiki_content/{page['slug']}/{page['slug']}.html"
                )
                fragment = (
                    SRC_DIR / page["filename"]
                ).read_text(encoding="utf-8")
                # Wrap the fragment in a minimal UTF-8 document with the
                # Canvas page-meta block in <head>. Canvas's Pages
                # importer reads the <body> content as the Page body and
                # picks up identifier / workflow_state / editing_roles
                # from the named <meta> tags (matches what canvas-cc
                # produces on export). Charset is also declared here so
                # the importer doesn't fall back to Windows-1252 (which
                # mangles em dashes / arrows into "â€"" / "â†'").
                wrapped = (
                    '<?xml version="1.0" encoding="UTF-8"?>\n'
                    '<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 '
                    'Transitional//EN" '
                    '"http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">\n'
                    '<html xmlns="http://www.w3.org/1999/xhtml" lang="en">\n'
                    '<head>\n'
                    '<meta http-equiv="Content-Type" '
                    'content="text/html; charset=utf-8" />\n'
                    f'<title>{page["page_title"]}</title>\n'
                    f'<meta name="identifier" content="{page["page_id"]}" />\n'
                    '<meta name="editing_roles" content="teachers" />\n'
                    '<meta name="workflow_state" content="active" />\n'
                    '<meta name="front_page" content="false" />\n'
                    '</head>\n'
                    '<body>\n'
                    f'{fragment}\n'
                    '</body>\n'
                    '</html>\n'
                )
                zf.writestr(arcname, wrapped.encode("utf-8"))
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
