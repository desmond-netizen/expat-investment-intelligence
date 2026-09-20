from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCANNER = ROOT / "scripts" / "secret_scan.py"


def init_git_repository(root: Path) -> None:
    subprocess.run(["git", "init", "-q", str(root)], check=True, capture_output=True, text=True)


class SecretScanTests(unittest.TestCase):
    def test_scanner_passes_clean_tree(self) -> None:
        result = subprocess.run(
            [sys.executable, str(SCANNER), str(ROOT), "--strict"],
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_scanner_redacts_suspected_value(self) -> None:
        token = "gh" + "p_" + ("a" * 36)
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            (root / "sample.py").write_text(f"value = '{token}'\n", encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(SCANNER), str(root), "--strict"],
                text=True,
                capture_output=True,
                check=False,
            )
        self.assertEqual(result.returncode, 1)
        self.assertIn("github_token", result.stdout)
        self.assertNotIn(token, result.stdout)

    def test_scans_staged_env_example_but_ignores_local_ignored_env(self) -> None:
        token = "gh" + "p_" + ("b" * 36)
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            init_git_repository(root)
            (root / ".gitignore").write_text(".env\n", encoding="utf-8")
            (root / ".env").write_text("", encoding="utf-8")
            (root / ".env.example").write_text("PROVIDER_TOKEN=" + token + "\n", encoding="utf-8")
            subprocess.run(["git", "-C", str(root), "add", ".gitignore", ".env.example"], check=True, capture_output=True, text=True)
            result = subprocess.run(
                [sys.executable, str(SCANNER), str(root), "--strict"],
                text=True,
                capture_output=True,
                check=False,
            )
        self.assertEqual(result.returncode, 1)
        self.assertIn(".env.example", result.stdout)
        self.assertIn("github_token", result.stdout)
        self.assertNotIn(token, result.stdout)

    def test_empty_ignored_env_does_not_block_a_release_scan(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            init_git_repository(root)
            (root / ".gitignore").write_text(".env\n", encoding="utf-8")
            (root / ".env").write_text("", encoding="utf-8")
            (root / ".env.example").write_text("EIA_API_KEY=\n", encoding="utf-8")
            subprocess.run(["git", "-C", str(root), "add", ".gitignore", ".env.example"], check=True, capture_output=True, text=True)
            result = subprocess.run(
                [sys.executable, str(SCANNER), str(root), "--strict"],
                text=True,
                capture_output=True,
                check=False,
            )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_scans_nonignored_untracked_candidate_files(self) -> None:
        token = "gh" + "p_" + ("c" * 36)
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            init_git_repository(root)
            (root / ".gitignore").write_text(".env\n", encoding="utf-8")
            subprocess.run(["git", "-C", str(root), "add", ".gitignore"], check=True, capture_output=True, text=True)
            (root / "new_provider.py").write_text("value = '" + token + "'\n", encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(SCANNER), str(root), "--strict"],
                text=True,
                capture_output=True,
                check=False,
            )
        self.assertEqual(result.returncode, 1)
        self.assertIn("new_provider.py", result.stdout)
        self.assertIn("github_token", result.stdout)
        self.assertNotIn(token, result.stdout)


if __name__ == "__main__":
    unittest.main()
