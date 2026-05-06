"""Build the interactive variant of HTML_Files/Chapter_01.html.

Reads `interactive_specs/chapter_01.yaml`, postprocesses
`HTML_Files/Chapter_01.html`, copies the engine assets, and writes
`HTML_Files_Interactive/Chapter_01.html`.

Does NOT read or write any .docx file. Does NOT modify HTML_Files/.
"""
from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

import yaml
from bs4 import BeautifulSoup

SUPPORTED_OPERATIONS = {
    "subtract", "add", "multiply", "count_sig_figs",
    "to_sci_notation", "sci_notation_arithmetic", "linear_function",
}

REQUIRED_PROBLEM_FIELDS = {"id", "match_text", "question", "answer", "explanation_template"}


class ValidationError(Exception):
    pass


def load_spec(path: Path) -> dict:
    """Parse and validate the YAML spec. Raise ValidationError on schema violations."""
    try:
        with open(path, encoding="utf-8") as f:
            raw = yaml.safe_load(f) or {}
    except yaml.YAMLError as e:
        raise ValidationError(f"YAML parse error in {path}: {e}")
    problems = raw.get("problems") or []
    if not isinstance(problems, list):
        raise ValidationError(f"`problems` must be a list, got {type(problems).__name__}")
    for i, prob in enumerate(problems):
        missing = REQUIRED_PROBLEM_FIELDS - set(prob.keys())
        # custom_js entries skip most schema checks
        if "custom_js" in prob:
            if "id" not in prob or "match_text" not in prob:
                raise ValidationError(f"problems[{i}]: custom_js entries still require id and match_text")
            continue
        if missing:
            raise ValidationError(f"problems[{i}] (id={prob.get('id', '?')}): missing fields: {sorted(missing)}")
        op = prob.get("answer", {}).get("operation")
        if op not in SUPPORTED_OPERATIONS:
            raise ValidationError(
                f"problems[{i}] (id={prob.get('id')}): unsupported operation '{op}'. "
                f"Supported: {sorted(SUPPORTED_OPERATIONS)}"
            )
    return raw


def attach_variant_attrs(html: str, spec: dict) -> str:
    """For each spec problem, find the matching <div class="problem-stem"> by
    text substring and add a data-variant-spec attribute. Raise ValidationError
    if a match_text doesn't resolve to exactly one element.
    """
    soup = BeautifulSoup(html, "html.parser")
    # build_html.py renders problem stems as <p class="problem-stem">; tests use
    # <div class="problem-stem"> fixtures. Match by class only so both work.
    stems = soup.find_all(class_="problem-stem")
    for prob in spec.get("problems", []):
        match_text = prob["match_text"]
        matches = [s for s in stems if match_text in s.get_text()]
        if not matches:
            raise ValidationError(
                f"match_text {match_text!r} for spec {prob['id']!r} not found in HTML"
            )
        if len(matches) > 1:
            raise ValidationError(
                f"match_text {match_text!r} for spec {prob['id']!r} matched "
                f"{len(matches)} problem-stem elements; make it unique"
            )
        matches[0]["data-variant-spec"] = prob["id"]
    return str(soup)


def inline_spec_json(html: str, spec: dict) -> str:
    """Insert <script type="application/json" id="variant-specs"> and
    <link>/<script> for engine assets just before </head>."""
    soup = BeautifulSoup(html, "html.parser")
    head = soup.find("head")
    if head is None:
        raise ValidationError("HTML has no <head>")
    # Spec JSON
    json_tag = soup.new_tag("script", id="variant-specs", type="application/json")
    json_tag.string = json.dumps(spec, separators=(",", ":"))
    head.append(json_tag)
    # Engine CSS
    css_tag = soup.new_tag("link", rel="stylesheet", href="assets/engine.css")
    head.append(css_tag)
    # Engine JS (ES module)
    js_tag = soup.new_tag("script", type="module", src="assets/engine.js")
    head.append(js_tag)
    return str(soup)


REPO = Path(__file__).resolve().parents[1]
SPEC_FILE = REPO / ".firecrawl" / "interactive_specs" / "chapter_01.yaml"
ENGINE_DIR = REPO / ".firecrawl" / "interactive_engine"
INPUT_HTML = REPO / "HTML_Files" / "Chapter_01.html"
OUTPUT_DIR = REPO / "HTML_Files_Interactive"
OUTPUT_HTML = OUTPUT_DIR / "Chapter_01.html"
ASSETS_DIR = OUTPUT_DIR / "assets"


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--validate", action="store_true",
                   help="parse and verify spec without writing output")
    p.add_argument("--show-samples", type=int, metavar="N",
                   help="print N sampled variants per problem (does not write output)")
    p.add_argument("--fuzz", type=int, metavar="N",
                   help="generate N variants per problem and assert all pass guardrails")
    args = p.parse_args()

    if args.validate:
        return cmd_validate()
    if args.show_samples is not None:
        return cmd_show_samples(args.show_samples)
    if args.fuzz is not None:
        return cmd_fuzz(args.fuzz)
    return cmd_build()


def cmd_build() -> int:
    spec = load_spec(SPEC_FILE)
    if not INPUT_HTML.exists():
        print(f"ERROR: {INPUT_HTML} not found. Run build_html.py first.", file=sys.stderr)
        return 2
    html = INPUT_HTML.read_text(encoding="utf-8")
    html = attach_variant_attrs(html, spec)
    html = inline_spec_json(html, spec)
    OUTPUT_DIR.mkdir(exist_ok=True)
    ASSETS_DIR.mkdir(exist_ok=True)
    OUTPUT_HTML.write_text(html, encoding="utf-8")
    shutil.copy2(ENGINE_DIR / "engine.js", ASSETS_DIR / "engine.js")
    shutil.copy2(ENGINE_DIR / "engine.css", ASSETS_DIR / "engine.css")
    print(f"Wrote {OUTPUT_HTML} and assets.")
    return 0


def cmd_validate() -> int:
    try:
        spec = load_spec(SPEC_FILE)
    except ValidationError as e:
        print(f"VALIDATE FAIL: {e}", file=sys.stderr)
        return 1
    if not INPUT_HTML.exists():
        print(f"VALIDATE FAIL: {INPUT_HTML} not found.", file=sys.stderr)
        return 1
    html = INPUT_HTML.read_text(encoding="utf-8")
    try:
        attach_variant_attrs(html, spec)
    except ValidationError as e:
        print(f"VALIDATE FAIL: {e}", file=sys.stderr)
        return 1
    n = len(spec.get("problems", []))
    print(f"VALIDATE OK: {n} problems, all match_text resolve to unique HTML elements.")
    return 0


def cmd_show_samples(n: int) -> int:
    spec = load_spec(SPEC_FILE)
    import subprocess as sp
    spec_json = json.dumps(spec)
    spec_tmp = REPO / ".firecrawl" / "interactive_engine" / "_spec_for_driver.json"
    spec_tmp.write_text(spec_json, encoding="utf-8")
    try:
        r = sp.run(
            ["node", "sample_driver.js", str(spec_tmp.name), str(n)],
            capture_output=True, text=True,
            cwd=str(ENGINE_DIR), check=False,
        )
    finally:
        spec_tmp.unlink(missing_ok=True)
    if r.returncode != 0:
        print(f"SHOW-SAMPLES FAIL: {r.stderr}", file=sys.stderr)
        return 1
    payload = json.loads(r.stdout)
    for prob in payload["samples"]:
        print(f"\n=== {prob['id']} (failures: {prob['failures']}/{n}) ===")
        for i, v in enumerate(prob["variants"]):
            if "error" in v:
                print(f"  [{i}] ERROR: {v['error']}")
            else:
                params = v.get("params", {})
                computed = v.get("computed", {})
                print(f"  [{i}] params={params}  ->  computed={computed}")
    return 0


def cmd_fuzz(n: int) -> int:
    spec = load_spec(SPEC_FILE)
    import subprocess as sp
    import re
    spec_json = json.dumps(spec)
    spec_tmp = REPO / ".firecrawl" / "interactive_engine" / "_spec_for_driver.json"
    spec_tmp.write_text(spec_json, encoding="utf-8")
    try:
        r = sp.run(
            ["node", "sample_driver.js", str(spec_tmp.name), str(n)],
            capture_output=True, text=True,
            cwd=str(ENGINE_DIR), check=False,
        )
    finally:
        spec_tmp.unlink(missing_ok=True)
    if r.returncode != 0:
        print(f"FUZZ FAIL: {r.stderr}", file=sys.stderr)
        return 1
    payload = json.loads(r.stdout)
    placeholder_re = re.compile(r"\{[a-zA-Z_]\w*\}")
    failed = False
    for prob in payload["samples"]:
        if prob["failures"] > 0:
            print(f"FUZZ FAIL: {prob['id']} had {prob['failures']}/{n} guardrail failures",
                  file=sys.stderr)
            failed = True
            continue
        # Spot-check: pick the first 5 variants, check no unfilled {token}s in the explanation.
        spec_entry = next(p for p in spec["problems"] if p["id"] == prob["id"])
        if "custom_js" in spec_entry:
            continue
        template = spec_entry["explanation_template"]
        for i, v in enumerate(prob["variants"][:5]):
            tokens = {**v["params"], **(v["computed"] if isinstance(v["computed"], dict) else {})}
            substituted = template
            for k, val in tokens.items():
                substituted = substituted.replace("{" + k + "}", str(val))
            leftover = placeholder_re.findall(substituted)
            if leftover:
                print(f"FUZZ FAIL: {prob['id']} variant {i} explanation has unfilled tokens: {leftover}",
                      file=sys.stderr)
                failed = True
        print(f"FUZZ OK: {prob['id']} {n}/{n} variants passed.")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
