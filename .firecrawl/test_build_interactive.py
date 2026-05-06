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


if __name__ == "__main__":
    unittest.main()
