from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class CliTests(unittest.TestCase):
    def test_social_command_runs_on_included_example(self) -> None:
        env = os.environ.copy()
        env["PYTHONPATH"] = str(ROOT / "src")
        result = subprocess.run(
            [sys.executable, "-m", "investment_intelligence", "social", "--input", "examples/social-posts.example.json"],
            cwd=ROOT,
            env=env,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["kind"], "social_signal_report")
        self.assertEqual(payload["input_posts"], 2)

    def test_output_file_is_opt_in(self) -> None:
        env = os.environ.copy()
        env["PYTHONPATH"] = str(ROOT / "src")
        with tempfile.TemporaryDirectory() as temporary_directory:
            output = Path(temporary_directory) / "nested" / "output.json"
            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "investment_intelligence",
                    "social",
                    "--input",
                    "examples/social-posts.example.json",
                    "--output",
                    str(output),
                ],
                cwd=ROOT,
                env=env,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout, "")
            self.assertEqual(json.loads(output.read_text(encoding="utf-8"))["kind"], "social_signal_report")

    def test_invalid_input_fails_without_echoing_local_path(self) -> None:
        env = os.environ.copy()
        env["PYTHONPATH"] = str(ROOT / "src")
        missing = "private-input-that-must-not-be-echoed.json"
        result = subprocess.run(
            [sys.executable, "-m", "investment_intelligence", "social", "--input", missing],
            cwd=ROOT,
            env=env,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(result.returncode, 1)
        self.assertIn("Command failed safely", result.stderr)
        self.assertNotIn(missing, result.stderr)


if __name__ == "__main__":
    unittest.main()
