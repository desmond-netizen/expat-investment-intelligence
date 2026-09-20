"""Public prediction-market metadata for research, with no trading capability."""

from __future__ import annotations

from datetime import UTC, datetime
import re
from typing import Any, Callable

from .http import get_json

POLYMARKET_EVENTS_URL = "https://gamma-api.polymarket.com/events"
SPORTS_TERMS = {"nba", "nfl", "mlb", "nhl", "soccer", "football", "tennis", "golf", "playoff", "championship"}
RESEARCH_TERMS = {"inflation", "interest rate", "fed", "oil", "diesel", "brazil", "tariff", "sanction", "war", "shipping", "recession"}
JsonFetcher = Callable[..., Any]


def _as_float(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def normalize_events(payload: Any, *, limit: int = 100) -> list[dict[str, Any]]:
    if not isinstance(payload, list):
        raise ValueError("Market API response must be a list")
    events: list[dict[str, Any]] = []
    for raw in payload:
        if not isinstance(raw, dict):
            continue
        title = str(raw.get("title") or raw.get("question") or "").strip()
        if not title:
            continue
        corpus = title.lower()
        if any(re.search(rf"\b{re.escape(term)}\b", corpus) for term in SPORTS_TERMS):
            continue
        terms = sorted(term for term in RESEARCH_TERMS if re.search(rf"\b{re.escape(term)}\b", corpus))
        if not terms:
            continue
        events.append(
            {
                "title": title[:300],
                "slug": raw.get("slug"),
                "end_date": raw.get("endDate"),
                "volume_24h": round(_as_float(raw.get("volume24hr")), 2),
                "matched_terms": terms,
            }
        )
    events.sort(key=lambda row: row["volume_24h"], reverse=True)
    return events[: max(1, limit)]


def build_market_report(*, fetcher: JsonFetcher = get_json, limit: int = 100) -> dict[str, Any]:
    payload = fetcher(
        POLYMARKET_EVENTS_URL,
        params={"active": "true", "closed": "false", "limit": 100, "order": "volume24hr", "ascending": "false"},
    )
    return {
        "kind": "prediction_market_metadata",
        "generated_at": datetime.now(UTC).isoformat(),
        "source": "polymarket_gamma",
        "events": normalize_events(payload, limit=limit),
        "disclaimer": "Public market metadata for research only. It is not trading advice or a recommendation to transact.",
    }
