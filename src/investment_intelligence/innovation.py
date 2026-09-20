"""Public innovation discovery using the Hugging Face Hub metadata API."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, Callable

from .http import get_json

HUGGING_FACE_MODELS_URL = "https://huggingface.co/api/models"
JsonFetcher = Callable[..., Any]


def normalize_models(payload: Any, *, limit: int = 20) -> list[dict[str, Any]]:
    if not isinstance(payload, list):
        raise ValueError("Model API response must be a list")
    models: list[dict[str, Any]] = []
    for row in payload:
        if not isinstance(row, dict):
            continue
        model_id = row.get("modelId") or row.get("id")
        if not isinstance(model_id, str) or not model_id:
            continue
        models.append(
            {
                "model_id": model_id,
                "last_modified": row.get("lastModified"),
                "downloads": row.get("downloads", 0),
                "likes": row.get("likes", 0),
                "pipeline_tag": row.get("pipeline_tag"),
                "library_name": row.get("library_name"),
            }
        )
    return models[: max(1, limit)]


def build_innovation_report(*, fetcher: JsonFetcher = get_json, limit: int = 20) -> dict[str, Any]:
    payload = fetcher(
        HUGGING_FACE_MODELS_URL,
        params={"sort": "lastModified", "direction": "-1", "limit": max(1, min(limit, 100)), "full": "false"},
    )
    return {
        "kind": "innovation_watch",
        "generated_at": datetime.now(UTC).isoformat(),
        "source": "huggingface_hub",
        "models": normalize_models(payload, limit=limit),
        "disclaimer": "Discovery metadata only. Verify source licensing, capability, and commercial terms independently.",
    }
