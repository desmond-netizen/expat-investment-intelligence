"""Command-line entry point for output-first research jobs."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from typing import Callable

from .http import FetchError
from .innovation import build_innovation_report
from .macro import build_macro_snapshot
from .markets import build_market_report
from .render import write_or_print
from .social import build_social_report, load_posts

APPROVED_ENVIRONMENT_VARIABLES = {"EIA_API_KEY", "SOCIAL_PROVIDER_API_KEY"}


def load_env_file(path: Path) -> None:
    """Load only documented variables from an explicitly chosen local file."""

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            raise ValueError("Environment file contains an invalid line")
        name, value = line.split("=", 1)
        name = name.strip()
        if name not in APPROVED_ENVIRONMENT_VARIABLES:
            raise ValueError("Environment file contains an unsupported variable")
        os.environ.setdefault(name, value.strip())


def _positive_int(value: str) -> int:
    parsed = int(value)
    if parsed < 1:
        raise argparse.ArgumentTypeError("must be at least 1")
    return parsed


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="investment-intelligence",
        description="Public, output-first research jobs. No messages are sent by this CLI.",
    )
    parser.add_argument(
        "--env-file",
        type=Path,
        help="Explicit local file with approved optional variables. It is never loaded automatically.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    macro = subparsers.add_parser("macro", help="Collect public macro observations")
    macro.add_argument("--include-energy", action="store_true", help="Include EIA inventory data when EIA_API_KEY is configured")
    macro.add_argument("--output", type=Path, help="Write JSON to this path instead of stdout")

    social = subparsers.add_parser("social", help="Score a local JSON social-data export")
    social.add_argument("--input", type=Path, required=True, help="JSON list of approved provider exports")
    social.add_argument("--limit", type=_positive_int, default=20)
    social.add_argument("--output", type=Path, help="Write JSON to this path instead of stdout")

    innovation = subparsers.add_parser("innovation", help="Discover recent public model metadata")
    innovation.add_argument("--limit", type=_positive_int, default=20)
    innovation.add_argument("--output", type=Path, help="Write JSON to this path instead of stdout")

    markets = subparsers.add_parser("markets", help="Collect public prediction-market metadata")
    markets.add_argument("--limit", type=_positive_int, default=100)
    markets.add_argument("--output", type=Path, help="Write JSON to this path instead of stdout")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        if args.env_file is not None:
            load_env_file(args.env_file)
        handlers: dict[str, Callable[[], tuple[dict, Path | None]]] = {
            "macro": lambda: (
                build_macro_snapshot(
                    include_energy=args.include_energy,
                    eia_api_key=os.environ.get("EIA_API_KEY"),
                ),
                args.output,
            ),
            "social": lambda: (build_social_report(load_posts(args.input), limit=args.limit), args.output),
            "innovation": lambda: (build_innovation_report(limit=args.limit), args.output),
            "markets": lambda: (build_market_report(limit=args.limit), args.output),
        }
        payload, output = handlers[args.command]()
        write_or_print(payload, output)
    except (FetchError, OSError, ValueError) as exc:
        del exc
        print("Command failed safely. Check local input, optional configuration, and source availability.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
