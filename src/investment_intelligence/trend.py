"""Trend-turn research alert computed from a local file of completed daily closes.

The rule checks whether a beaten-down stock has stopped falling relative to a
benchmark before anyone considers it:

1. The last completed close is above its ``sma``-session simple average.
2. The symbol/benchmark price ratio has not made a new ``rs_window``-session low
   in the last ``rs_quiet`` sessions.

Both must hold for ``trend_turn_confirmed`` to be true. The module reads a local
CSV you supply. It makes no network request and sends no message.
"""

from __future__ import annotations

import csv
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any

REQUIRED_COLUMNS = {"date", "symbol", "close"}


def load_closes(path: Path) -> dict[str, list[tuple[str, float]]]:
    """Read ``date,symbol,close`` rows into symbol -> [(ISO date, close), ...] in date order."""

    closes: dict[str, dict[str, float]] = {}
    with path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames or not REQUIRED_COLUMNS.issubset(name.strip().lower() for name in reader.fieldnames):
            raise ValueError("Closes file must have date, symbol, and close columns")
        for raw in reader:
            row = {key.strip().lower(): (value or "").strip() for key, value in raw.items() if key}
            day = date.fromisoformat(row["date"]).isoformat()
            symbol = row["symbol"].upper()
            close = float(row["close"])
            if not symbol or close <= 0:
                raise ValueError("Closes file contains an empty symbol or non-positive close")
            closes.setdefault(symbol, {})[day] = close
    return {symbol: sorted(series.items()) for symbol, series in closes.items()}


def trend_signal(
    closes: dict[str, list[tuple[str, float]]],
    *,
    symbol: str,
    benchmark: str,
    sma: int = 50,
    rs_window: int = 60,
    rs_quiet: int = 10,
) -> dict[str, Any]:
    """Compute the trend-turn inputs. Only dates present for both series enter the ratio."""

    symbol, benchmark = symbol.upper(), benchmark.upper()
    own = dict(closes.get(symbol) or [])
    bench = dict(closes.get(benchmark) or [])
    dates = sorted(set(own) & set(bench))
    needed = max(sma, rs_window + rs_quiet)
    if len(dates) < needed:
        raise ValueError(f"Only {len(dates)} shared daily closes; {needed} needed")
    series = [own[day] for day in dates]
    ratio = [own[day] / bench[day] for day in dates]
    average = sum(series[-sma:]) / sma
    recent_low = min(ratio[-rs_quiet:])
    prior_low = min(ratio[-(rs_window + rs_quiet):-rs_quiet])
    above_sma = series[-1] > average
    rs_new_low = recent_low < prior_low
    return {
        "symbol": symbol,
        "benchmark": benchmark,
        "date": dates[-1],
        "close": round(series[-1], 4),
        "sma": round(average, 4),
        "sma_sessions": sma,
        "close_vs_sma": round(series[-1] / average - 1, 4),
        "above_sma": above_sma,
        "rs_window": rs_window,
        "rs_quiet": rs_quiet,
        "rs_new_low": rs_new_low,
        "rs_recent_vs_prior_low": round(recent_low / prior_low - 1, 4),
        "trend_turn_confirmed": above_sma and not rs_new_low,
    }


def build_trend_report(
    closes: dict[str, list[tuple[str, float]]],
    *,
    symbols: list[str],
    benchmark: str,
    sma: int = 50,
    rs_window: int = 60,
    rs_quiet: int = 10,
) -> dict[str, Any]:
    signals = [
        trend_signal(closes, symbol=symbol, benchmark=benchmark, sma=sma, rs_window=rs_window, rs_quiet=rs_quiet)
        for symbol in symbols
    ]
    return {
        "kind": "trend_turn_report",
        "generated_at": datetime.now(UTC).isoformat(),
        "rule": (
            f"Close above its {sma}-session average and no new {rs_window}-session low in the "
            f"symbol/{benchmark.upper()} ratio over the last {rs_quiet} sessions"
        ),
        "signals": signals,
        "confirmed": [signal["symbol"] for signal in signals if signal["trend_turn_confirmed"]],
        "disclaimer": (
            "Research trigger only. A confirmed trend turn is a prompt to re-check fundamentals "
            "and size risk, not a recommendation to transact."
        ),
    }
