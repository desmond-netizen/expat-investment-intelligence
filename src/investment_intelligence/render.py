"""Output helpers. Commands only write when the caller explicitly requests it."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def render_json(payload: Any) -> str:
    return json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def write_or_print(payload: Any, output: Path | None) -> None:
    rendered = render_json(payload)
    if output is None:
        print(rendered, end="")
        return
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(rendered, encoding="utf-8")
