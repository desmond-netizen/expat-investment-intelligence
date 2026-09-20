from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from investment_intelligence.markets import build_market_report, normalize_events  # noqa: E402


class MarketTests(unittest.TestCase):
    def test_excludes_sports_and_keeps_research_topics(self) -> None:
        events = normalize_events(
            [
                {"title": "Will oil exceed a threshold?", "slug": "oil", "volume24hr": "12.5"},
                {"title": "Will the NBA team win?", "slug": "sports", "volume24hr": "999"},
                {"title": "Will inflation fall?", "slug": "inflation", "volume24hr": "23"},
                {"title": "A general event", "slug": "general", "volume24hr": "50"},
            ]
        )
        self.assertEqual([event["slug"] for event in events], ["inflation", "oil"])
        self.assertEqual(events[0]["matched_terms"], ["inflation"])

    def test_report_fetches_broadly_then_applies_output_limit(self) -> None:
        captured: dict[str, object] = {}

        def fake_fetcher(url: str, *, params=None):
            captured["params"] = params
            return [
                {"title": "Will oil rise?", "slug": "oil", "volume24hr": "10"},
                {"title": "Will inflation fall?", "slug": "inflation", "volume24hr": "20"},
            ]

        report = build_market_report(fetcher=fake_fetcher, limit=1)
        self.assertEqual(captured["params"]["limit"], 100)
        self.assertEqual([event["slug"] for event in report["events"]], ["inflation"])


if __name__ == "__main__":
    unittest.main()
