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


if __name__ == "__main__":
    unittest.main()
