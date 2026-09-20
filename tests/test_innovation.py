from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from investment_intelligence.innovation import build_innovation_report, normalize_models  # noqa: E402


class InnovationTests(unittest.TestCase):
    def test_normalizes_public_model_metadata(self) -> None:
        models = normalize_models(
            [
                {"modelId": "org/model-a", "lastModified": "2026-01-01T00:00:00Z", "downloads": 2, "likes": 1},
                {"id": "org/model-b", "pipeline_tag": "text-generation"},
                {"likes": 50},
            ]
        )
        self.assertEqual([model["model_id"] for model in models], ["org/model-a", "org/model-b"])

    def test_report_uses_bounded_limit(self) -> None:
        received: dict[str, object] = {}

        def fake_fetcher(url: str, *, params=None):
            received["url"] = url
            received["params"] = params
            return [{"modelId": "org/model-a"}, {"modelId": "org/model-b"}]

        report = build_innovation_report(fetcher=fake_fetcher, limit=1)
        self.assertEqual(len(report["models"]), 1)
        self.assertEqual(received["params"]["limit"], 1)


if __name__ == "__main__":
    unittest.main()
