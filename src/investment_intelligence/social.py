"""Local, provider-neutral social-listening analysis."""

from __future__ import annotations

import json
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

KEYWORDS = {
    "fuel": 2,
    "diesel": 3,
    "refinery": 3,
    "shipping": 2,
    "sanction": 3,
    "shortage": 3,
    "pipeline": 2,
    "port": 1,
    "freight": 1,
}


@dataclass(frozen=True)
class SocialPost:
    source: str
    title: str
    text: str
    url: str
    engagement: int
    published_at: str | None = None


def _clean_string(value: Any, *, limit: int) -> str:
    return " ".join(str(value or "").split())[:limit]


def _valid_url(value: str) -> bool:
    parsed = urlsplit(value)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def parse_posts(raw_posts: Iterable[dict[str, Any]]) -> list[SocialPost]:
    """Validate and normalize provider exports. Invalid posts are skipped."""

    posts: list[SocialPost] = []
    seen_urls: set[str] = set()
    for raw in raw_posts:
        if not isinstance(raw, dict):
            continue
        url = _clean_string(raw.get("url"), limit=1000)
        if not _valid_url(url) or url in seen_urls:
            continue
        source = _clean_string(raw.get("source"), limit=80) or "unknown"
        title = _clean_string(raw.get("title"), limit=240)
        text = _clean_string(raw.get("text"), limit=1200)
        try:
            engagement = max(0, int(raw.get("engagement", 0)))
        except (TypeError, ValueError):
            engagement = 0
        seen_urls.add(url)
        posts.append(
            SocialPost(
                source=source,
                title=title,
                text=text,
                url=url,
                engagement=engagement,
                published_at=_clean_string(raw.get("published_at"), limit=64) or None,
            )
        )
    return posts


def score_post(post: SocialPost) -> dict[str, Any]:
    corpus = f"{post.title} {post.text}".lower()
    matches = sorted(keyword for keyword in KEYWORDS if keyword in corpus)
    score = sum(KEYWORDS[keyword] for keyword in matches) + min(post.engagement, 100) / 50
    return {
        "source": post.source,
        "title": post.title,
        "url": post.url,
        "published_at": post.published_at,
        "engagement": post.engagement,
        "matched_terms": matches,
        "signal_score": round(score, 2),
    }


def build_social_report(posts: Iterable[SocialPost], *, limit: int = 20) -> dict[str, Any]:
    scored = [score_post(post) for post in posts]
    signals = [row for row in scored if row["matched_terms"]]
    signals.sort(key=lambda row: (row["signal_score"], row["engagement"]), reverse=True)
    return {
        "kind": "social_signal_report",
        "input_posts": len(scored),
        "matching_posts": len(signals),
        "signals": signals[: max(1, limit)],
        "disclaimer": "Signals are keyword matches from user-supplied data, not verified events or investment advice.",
    }


def load_posts(path: Path) -> list[SocialPost]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError("Social input must be a JSON list of post objects")
    return parse_posts(data)
