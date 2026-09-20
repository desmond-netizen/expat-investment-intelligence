"""Public macro collectors with no delivery side effects."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, Callable

from .http import FetchError, get_json

BCB_USD_BRL_URL = "https://api.bcb.gov.br/dados/serie/bcdata.sgs.1/dados/ultimos/1?formato=json"
BCB_SELIC_URL = "https://api.bcb.gov.br/dados/serie/bcdata.sgs.1178/dados/ultimos/1?formato=json"
EIA_WEEKLY_URL = "https://api.eia.gov/v2/seriesid/PET.WDISTUS1.W"

JsonFetcher = Callable[..., Any]


def _as_number(value: Any) -> float | None:
    """Parse common Brazilian and US numeric representations safely."""

    if value is None:
        return None
    text = str(value).strip().replace(" ", "")
    if not text:
        return None
    try:
        if "," in text and "." in text:
            if text.rfind(",") > text.rfind("."):
                normalized = text.replace(".", "").replace(",", ".")
            else:
                normalized = text.replace(",", "")
        elif "," in text:
            normalized = text.replace(",", ".")
        else:
            normalized = text
        return float(normalized)
    except ValueError:
        return None


def latest_bcb_observation(payload: Any) -> dict[str, Any]:
    """Normalize the latest BCB OData observation without assuming its locale."""

    if not isinstance(payload, list) or not payload or not isinstance(payload[0], dict):
        raise ValueError("BCB response did not contain an observation")
    observation = payload[0]
    return {
        "date": observation.get("data"),
        "value": _as_number(observation.get("valor")),
    }


def _source_result(name: str, getter: Callable[[], Any]) -> dict[str, Any]:
    try:
        return {"source": name, "status": "ok", "data": getter()}
    except (FetchError, ValueError, KeyError, TypeError):
        return {"source": name, "status": "unavailable"}


def eia_distillate_inventory(fetcher: JsonFetcher, api_key: str) -> dict[str, Any]:
    """Fetch a single EIA weekly distillate observation with a caller-provided key."""

    payload = fetcher(
        EIA_WEEKLY_URL,
        params={
            "api_key": api_key,
            "length": 1,
            "sort[0][column]": "period",
            "sort[0][direction]": "desc",
        },
    )
    rows = payload.get("response", {}).get("data", []) if isinstance(payload, dict) else []
    if not rows or not isinstance(rows[0], dict):
        raise ValueError("EIA response did not contain a weekly observation")
    row = rows[0]
    return {"period": row.get("period"), "value": _as_number(row.get("value")), "units": row.get("units")}


def build_macro_snapshot(
    *,
    fetcher: JsonFetcher = get_json,
    include_energy: bool = False,
    eia_api_key: str | None = None,
) -> dict[str, Any]:
    """Build a resilient, output-only macro snapshot from public sources."""

    sources = [
        _source_result("bcb_usd_brl", lambda: latest_bcb_observation(fetcher(BCB_USD_BRL_URL))),
        _source_result("bcb_selic", lambda: latest_bcb_observation(fetcher(BCB_SELIC_URL))),
    ]
    if include_energy:
        if eia_api_key:
            sources.append(_source_result("eia_distillate_inventory", lambda: eia_distillate_inventory(fetcher, eia_api_key)))
        else:
            sources.append({"source": "eia_distillate_inventory", "status": "not_configured"})

    return {
        "kind": "macro_snapshot",
        "generated_at": datetime.now(UTC).isoformat(),
        "sources": sources,
        "disclaimer": "Research data only. It is not investment advice.",
    }
