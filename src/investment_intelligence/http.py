"""Small HTTP helpers that avoid exposing query-string credentials in errors."""

from __future__ import annotations

import json
from typing import Any, Callable, Mapping
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlsplit, urlunsplit
from urllib.request import Request, urlopen

DEFAULT_TIMEOUT_SECONDS = 20
DEFAULT_USER_AGENT = "investment-intelligence/0.1 (+https://github.com/desmond-netizen/expat-investment-intelligence)"


class FetchError(RuntimeError):
    """A network or response error with safe, non-sensitive context."""


def _host(url: str) -> str:
    return urlsplit(url).hostname or "unknown-host"


def _with_params(url: str, params: Mapping[str, str | int | float] | None) -> str:
    if not params:
        return url
    parts = urlsplit(url)
    query = urlencode(params)
    merged = "&".join(piece for piece in (parts.query, query) if piece)
    return urlunsplit((parts.scheme, parts.netloc, parts.path, merged, ""))


def get_json(
    url: str,
    *,
    params: Mapping[str, str | int | float] | None = None,
    timeout: int = DEFAULT_TIMEOUT_SECONDS,
    opener: Callable[..., Any] = urlopen,
) -> Any:
    """Fetch a JSON response and raise a redaction-safe error when it fails."""

    request = Request(
        _with_params(url, params),
        headers={"Accept": "application/json", "User-Agent": DEFAULT_USER_AGENT},
    )
    host = _host(url)
    try:
        with opener(request, timeout=timeout) as response:
            body = response.read().decode("utf-8")
    except HTTPError as exc:
        raise FetchError(f"HTTP {exc.code} from {host}") from exc
    except URLError as exc:
        raise FetchError(f"Network error from {host}") from exc
    except TimeoutError as exc:
        raise FetchError(f"Timeout from {host}") from exc
    except OSError as exc:
        raise FetchError(f"Transport error from {host}") from exc

    try:
        return json.loads(body)
    except json.JSONDecodeError as exc:
        raise FetchError(f"Invalid JSON from {host}") from exc
