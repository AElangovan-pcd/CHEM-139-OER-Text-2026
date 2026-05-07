"""Tests for build_interactive.py."""
import unittest
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / ".firecrawl" / "build_interactive.py"


class TestCli(unittest.TestCase):
    def test_help(self):
        r = subprocess.run(
            [sys.executable, str(SCRIPT), "--help"],
            capture_output=True, text=True, cwd=str(REPO)
        )
        self.assertEqual(r.returncode, 0)
        self.assertIn("--validate", r.stdout)
        self.assertIn("--show-samples", r.stdout)
        self.assertIn("--fuzz", r.stdout)


import tempfile
from pathlib import Path

# Add the script's directory to path so we can import it
sys.path.insert(0, str(REPO / ".firecrawl"))
from build_interactive import load_spec, ValidationError


class TestSpecLoading(unittest.TestCase):
    def write_spec(self, content: str) -> Path:
        f = tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False, encoding='utf-8')
        f.write(content)
        f.close()
        self.addCleanup(lambda: Path(f.name).unlink())
        return Path(f.name)

    def test_loads_valid_spec(self):
        path = self.write_spec("""
problems:
  - id: "test.subtract"
    match_text: "Compute (8.42 m)"
    question: "Compute ({a} m) − ({b} m)"
    variables:
      a: { range: [5.0, 50.0], decimal_places: 2 }
      b: { range: [1.0, 5.0], decimal_places: 1 }
    answer:
      operation: subtract
    explanation_template: "Test."
""")
        spec = load_spec(path)
        self.assertEqual(len(spec["problems"]), 1)
        self.assertEqual(spec["problems"][0]["id"], "test.subtract")

    def test_rejects_missing_id(self):
        path = self.write_spec("""
problems:
  - match_text: "x"
    question: "x"
    answer: { operation: subtract }
    explanation_template: "x"
""")
        with self.assertRaises(ValidationError):
            load_spec(path)

    def test_rejects_unknown_operation(self):
        path = self.write_spec("""
problems:
  - id: "x"
    match_text: "x"
    question: "x"
    answer: { operation: bogus }
    explanation_template: "x"
""")
        with self.assertRaises(ValidationError):
            load_spec(path)


from build_interactive import attach_variant_attrs


class TestAttachVariantAttrs(unittest.TestCase):
    def test_attaches_attribute_to_matching_stem(self):
        html = '''
        <div class="problem-stem">How many feet are in 12.4 meters?</div>
        <div class="solution">40.7 ft</div>
        <div class="problem-stem">Other problem.</div>
        <div class="solution">x</div>
        '''
        spec = {"problems": [{
            "id": "test.feet",
            "match_text": "How many feet are in 12.4",
            "question": "x", "answer": {"operation": "subtract"},
            "explanation_template": "x", "variables": {},
        }]}
        result_html = attach_variant_attrs(html, spec)
        self.assertIn('data-variant-spec="test.feet"', result_html)
        self.assertIn('How many feet are in 12.4 meters?', result_html)

    def test_raises_when_match_text_not_found(self):
        html = '<div class="problem-stem">Hello</div><div class="solution">x</div>'
        spec = {"problems": [{
            "id": "missing", "match_text": "GoodbyeNotFound",
            "question": "x", "answer": {"operation": "subtract"},
            "explanation_template": "x", "variables": {},
        }]}
        with self.assertRaises(ValidationError):
            attach_variant_attrs(html, spec)

    def test_raises_when_match_text_ambiguous(self):
        html = ('<div class="problem-stem">Convert X</div><div class="solution">x</div>'
                '<div class="problem-stem">Convert X</div><div class="solution">y</div>')
        spec = {"problems": [{
            "id": "ambig", "match_text": "Convert X",
            "question": "x", "answer": {"operation": "subtract"},
            "explanation_template": "x", "variables": {},
        }]}
        with self.assertRaises(ValidationError):
            attach_variant_attrs(html, spec)


class TestValidateFlag(unittest.TestCase):
    def test_validate_returns_zero_on_clean_spec(self):
        r = subprocess.run(
            [sys.executable, str(SCRIPT), "--validate"],
            capture_output=True, text=True, cwd=str(REPO)
        )
        self.assertEqual(r.returncode, 0, msg=r.stderr)


from build_interactive import discover_chapters


class TestDiscoverChapters(unittest.TestCase):
    def test_finds_chapter_01_yaml(self):
        chapters = discover_chapters()
        ids = [c['number'] for c in chapters]
        self.assertIn('01', ids, msg=f'Expected 01 in {ids}')

    def test_each_entry_has_required_fields(self):
        chapters = discover_chapters()
        self.assertGreaterEqual(len(chapters), 1)
        for c in chapters:
            self.assertIn('number', c)
            self.assertIn('spec_path', c)
            self.assertIn('input_html', c)
            self.assertIn('output_html', c)

    def test_paths_resolve_to_real_files(self):
        chapters = discover_chapters()
        for c in chapters:
            self.assertTrue(c['spec_path'].exists(), msg=f"spec missing: {c['spec_path']}")
            # input_html must exist for the build to work; output_html may not exist yet
            self.assertTrue(c['input_html'].exists(), msg=f"input HTML missing: {c['input_html']}")


class TestChapterFlag(unittest.TestCase):
    def test_chapter_flag_in_help(self):
        r = subprocess.run(
            [sys.executable, str(SCRIPT), "--help"],
            capture_output=True, text=True, cwd=str(REPO)
        )
        self.assertEqual(r.returncode, 0)
        self.assertIn("--chapter", r.stdout)

    def test_validate_chapter_01_explicit(self):
        r = subprocess.run(
            [sys.executable, str(SCRIPT), "--validate", "--chapter", "01"],
            capture_output=True, text=True, cwd=str(REPO)
        )
        self.assertEqual(r.returncode, 0, msg=r.stderr)

    def test_validate_unknown_chapter_fails(self):
        r = subprocess.run(
            [sys.executable, str(SCRIPT), "--validate", "--chapter", "99"],
            capture_output=True, text=True, cwd=str(REPO)
        )
        self.assertNotEqual(r.returncode, 0)


if __name__ == "__main__":
    unittest.main()
