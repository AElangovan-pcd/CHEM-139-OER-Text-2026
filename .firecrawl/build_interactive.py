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
        with open(path) as f:
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
    raise NotImplementedError("cmd_build will be implemented in task E4")


def cmd_validate() -> int:
    raise NotImplementedError("cmd_validate will be implemented in task E5")


def cmd_show_samples(n: int) -> int:
    raise NotImplementedError("cmd_show_samples will be implemented in task E6")


def cmd_fuzz(n: int) -> int:
    raise NotImplementedError("cmd_fuzz will be implemented in task E7")


if __name__ == "__main__":
    sys.exit(main())
