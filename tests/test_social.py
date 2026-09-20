from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from investment_intelligence.social import build_social_report, parse_posts  # noqa: E402


class SocialTests(unittest.TestCase):
    def test_normalizes_deduplicates_and_scores_posts(self) -> None:
        posts = parse_posts(
            [
                {
                    "source": "fixture",
                    "title": "Diesel shortage concerns",
                    "text": "Refinery maintenance affects fuel supply.",
                    "url": "https://example.com/a",
                    "engagement": "25",
                },
                {
                    "source": "fixture",
                    "title": "duplicate",
                    "text": "should be skipped",
                    "url": "https://example.com/a",
                    "engagement": 99,
                },
                {"source": "fixture", "title": "bad", "url": "not-a-url"},
            ]
        )
        self.assertEqual(len(posts), 1)
        report = build_social_report(posts)
        self.assertEqual(report["input_posts"], 1)
        self.assertEqual(report["matching_posts"], 1)
        signal = report["signals"][0]
        self.assertEqual(signal["matched_terms"], ["diesel", "fuel", "refinery", "shortage"])
        self.assertGreater(signal["signal_score"], 10)

    def test_non_matching_posts_are_not_signals(self) -> None:
        posts = parse_posts(
            [{"source": "fixture", "title": "General note", "text": "Nothing relevant", "url": "https://example.com/b"}]
        )
        report = build_social_report(posts)
        self.assertEqual(report["matching_posts"], 0)
        self.assertEqual(report["signals"], [])


if __name__ == "__main__":
    unittest.main()
