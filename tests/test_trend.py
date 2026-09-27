from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Sequence

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from investment_intelligence.trend import build_trend_report, load_closes, trend_signal  # noqa: E402


def _series(values: Sequence[float]) -> list[tuple[str, float]]:
    return [(f"2026-{1 + i // 28:02d}-{1 + i % 28:02d}", value) for i, value in enumerate(values)]


class TrendTests(unittest.TestCase):
    def test_recovery_after_decline_confirms(self) -> None:
        own = [100 - i for i in range(50)] + [50 + 2 * i for i in range(30)]
        closes = {"AAA": _series(own), "BENCH": _series([100.0] * 80)}
        signal = trend_signal(closes, symbol="AAA", benchmark="BENCH")
        self.assertTrue(signal["above_sma"])
        self.assertFalse(signal["rs_new_low"])
        self.assertTrue(signal["trend_turn_confirmed"])

    def test_steady_decline_does_not_confirm(self) -> None:
        closes = {"AAA": _series([100 - i for i in range(80)]), "BENCH": _series([100.0] * 80)}
        signal = trend_signal(closes, symbol="AAA", benchmark="BENCH")
        self.assertFalse(signal["above_sma"])
        self.assertTrue(signal["rs_new_low"])
        self.assertFalse(signal["trend_turn_confirmed"])

    def test_new_relative_low_blocks_confirmation_even_above_average(self) -> None:
        # Price rises above its average but the benchmark rises faster, so the ratio keeps making lows.
        own = [50.0] * 60 + [50 + i for i in range(1, 21)]
        bench = [100.0] * 60 + [100 + 10 * i for i in range(1, 21)]
        signal = trend_signal({"AAA": _series(own), "BENCH": _series(bench)}, symbol="AAA", benchmark="BENCH")
        self.assertTrue(signal["above_sma"])
        self.assertTrue(signal["rs_new_low"])
        self.assertFalse(signal["trend_turn_confirmed"])

    def test_insufficient_history_raises(self) -> None:
        closes = {"AAA": _series([10.0] * 30), "BENCH": _series([10.0] * 30)}
        with self.assertRaises(ValueError):
            trend_signal(closes, symbol="AAA", benchmark="BENCH")

    def test_example_file_report(self) -> None:
        closes = load_closes(ROOT / "examples" / "daily-closes.example.csv")
        report = build_trend_report(closes, symbols=["EXA", "EXB"], benchmark="BENCH")
        self.assertEqual(report["kind"], "trend_turn_report")
        self.assertEqual(report["confirmed"], ["EXA"])

    def test_missing_columns_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "bad.csv"
            path.write_text("day,ticker,price\n2026-01-02,AAA,1\n", encoding="utf-8")
            with self.assertRaises(ValueError):
                load_closes(path)

    def test_cli_trend_command(self) -> None:
        env = os.environ.copy()
        env["PYTHONPATH"] = str(ROOT / "src")
        result = subprocess.run(
            [
                sys.executable, "-m", "investment_intelligence", "trend",
                "--closes", "examples/daily-closes.example.csv",
                "--symbols", "EXA,EXB", "--benchmark", "BENCH",
            ],
            cwd=ROOT, env=env, text=True, capture_output=True, check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["confirmed"], ["EXA"])


if __name__ == "__main__":
    unittest.main()
