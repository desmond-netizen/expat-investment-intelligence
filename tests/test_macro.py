from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from investment_intelligence.macro import (  # noqa: E402
    BCB_SELIC_URL,
    BCB_USD_BRL_URL,
    EIA_WEEKLY_URL,
    build_macro_snapshot,
    latest_bcb_observation,
)


class MacroTests(unittest.TestCase):
    def test_normalizes_bcb_decimal_formats(self) -> None:
        self.assertEqual(latest_bcb_observation([{"data": "01/01/2026", "valor": "5,25"}])["value"], 5.25)
        self.assertEqual(latest_bcb_observation([{"data": "01/01/2026", "valor": "5.25"}])["value"], 5.25)
        self.assertEqual(latest_bcb_observation([{"data": "01/01/2026", "valor": "1.234,56"}])["value"], 1234.56)
        self.assertEqual(latest_bcb_observation([{"data": "01/01/2026", "valor": "1,234.56"}])["value"], 1234.56)

    def test_snapshot_is_output_only_and_marks_missing_eia_configuration(self) -> None:
        calls: list[str] = []

        def fake_fetcher(url: str, *, params=None):
            calls.append(url)
            if url == BCB_USD_BRL_URL:
                return [{"data": "01/01/2026", "valor": "5,25"}]
            if url == BCB_SELIC_URL:
                return [{"data": "01/01/2026", "valor": "13,75"}]
            self.fail(f"Unexpected URL: {url}")

        snapshot = build_macro_snapshot(fetcher=fake_fetcher, include_energy=True)
        self.assertEqual(calls, [BCB_USD_BRL_URL, BCB_SELIC_URL])
        self.assertEqual(snapshot["sources"][0]["data"]["value"], 5.25)
        self.assertEqual(snapshot["sources"][2]["status"], "not_configured")

    def test_snapshot_includes_energy_when_configured(self) -> None:
        def fake_fetcher(url: str, *, params=None):
            if url in {BCB_USD_BRL_URL, BCB_SELIC_URL}:
                return [{"data": "01/01/2026", "valor": "1,00"}]
            if url == EIA_WEEKLY_URL:
                self.assertIn("api_key", params)
                return {"response": {"data": [{"period": "2026-01-01", "value": "123.4", "units": "thousand barrels"}]}}
            self.fail(f"Unexpected URL: {url}")

        snapshot = build_macro_snapshot(fetcher=fake_fetcher, include_energy=True, eia_api_key="local-test-value")
        energy = snapshot["sources"][2]
        self.assertEqual(energy["status"], "ok")
        self.assertEqual(energy["data"]["value"], 123.4)


if __name__ == "__main__":
    unittest.main()
