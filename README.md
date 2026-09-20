# Investment Intelligence: Macro, Social Listening & Innovation

A public, output-first starter kit for recurring investment research. It turns a set of private automation patterns into portable modules that collect public macro data, score an approved social-data export, discover innovation metadata, and inspect public prediction-market metadata.

> **Research only.** This project does not provide investment, trading, legal, or tax advice. Verify every source, model, and claim before acting.

## What is included

| Area | Command | Default behavior |
|---|---|---|
| Macro | `investment-intelligence macro` | Public Banco Central do Brasil USD/BRL and Selic observations, with optional EIA energy data when you provide your own key |
| Social listening | `investment-intelligence social --input posts.json` | Scores an approved local JSON export. It does not scrape a social network by default. |
| Innovation | `investment-intelligence innovation` | Recent public Hugging Face Hub model metadata |
| Market metadata | `investment-intelligence markets` | Filtered public Polymarket Gamma event metadata. No trading or order placement. |

Every command writes JSON to stdout unless you explicitly pass `--output`. There is no built-in Slack, Telegram, webhook, or email sender.

## What was intentionally removed from the private automation

- Credentials, `.env` loading from personal paths, webhooks, delivery channels, recipient IDs, and local sender commands.
- Personal state directories, output archives, machine-specific imports, and alternate interpreter paths.
- Default external delivery and any code that can post a message.
- The private operational digest and its local file or service inspection.
- Unreviewed scraping or provider integrations. Add them only after you confirm terms, attribution, privacy, and rate limits.

## Onboarding

### 1. Prerequisites

- Python 3.11 or newer
- Git
- Internet access for commands that use public APIs

### 2. Clone and create an isolated environment

```bash
git clone https://github.com/desmond-netizen/investment-intelligence-macro-social-innovation.git
cd investment-intelligence-macro-social-innovation
```

Choose one environment setup:

```bash
# Option A: Python venv
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -e .
```

```bash
# Option B: uv, useful when your system Python has no bundled pip or venv module
uv venv .venv --python 3.11
uv pip install --python .venv/bin/python -e .
. .venv/bin/activate
```

### 3. Add only your optional local configuration

```bash
cp .env.example .env
```

Keep `.env` on your machine. It is ignored by Git. The starter works without a key except for optional EIA inventory data. The CLI never loads `.env` automatically. If you use EIA, set `EIA_API_KEY` in your shell or opt in explicitly with `--env-file .env`. Never paste a key into a command, issue, pull request, commit, or chat.

### 4. Run the safe local smoke test first

This uses only the included fictional example data and makes no network request:

```bash
investment-intelligence social --input examples/social-posts.example.json
```

### 5. Run public collectors

```bash
# Public macro observations
investment-intelligence macro

# Add optional energy inventory data only after EIA_API_KEY is configured locally
investment-intelligence --env-file .env macro --include-energy

# Public innovation metadata
investment-intelligence innovation --limit 10

# Public prediction-market metadata, research only
investment-intelligence markets --limit 25
```

To persist any result locally:

```bash
investment-intelligence macro --output reports/macro.json
```

`reports/` is ignored by Git so generated research is not accidentally published.

### 6. Bring your own compliant social-data export

Give the social command a JSON list with these fields:

```json
[
  {
    "source": "provider-name",
    "title": "short title",
    "text": "approved export text",
    "url": "https://example.com/post/123",
    "engagement": 12,
    "published_at": "2026-01-15T12:00:00Z"
  }
]
```

Do not commit collected posts, account handles, raw exports, or personally identifiable information. Check the source platform's terms before collecting, storing, or redistributing data.

### 7. Schedule it only after the output is correct

- Standard cron: see [`jobs/crontab.example`](jobs/crontab.example).
- Hermes cron: see [`jobs/hermes-cron-onboarding.md`](jobs/hermes-cron-onboarding.md).

Both paths write local output first. Add your own secure delivery layer only after you have reviewed the generated files and confirmed that no recipient or credential can leak.

### 8. Run the public-release checks before every push

```bash
python3 scripts/secret_scan.py --strict
python3 -m unittest discover -s tests -v
git status --short
```

Read [`SECURITY.md`](SECURITY.md) before adding a provider or publishing a fork.

## Data sources and limits

| Source | Used for | Authentication |
|---|---|---|
| Banco Central do Brasil | USD/BRL and Selic observations | Public endpoint |
| U.S. EIA | Optional weekly distillate inventory | User-provided EIA key |
| Hugging Face Hub | Recent public model metadata | Public endpoint |
| Polymarket Gamma | Public event metadata | Public endpoint |

Availability, schemas, terms, and rate limits can change. The collectors fail closed to a source status where possible and do not emit query strings or keys in error messages.

## Repository layout

```text
src/investment_intelligence/  Public collectors and CLI
examples/                     Fictional, non-sensitive input examples
jobs/                         Standard cron and Hermes onboarding templates
scripts/secret_scan.py        Pre-push scanner that never prints suspected values
tests/                        Offline unit tests
```

## Development

```bash
python3 -m unittest discover -s tests -v
python3 scripts/secret_scan.py --strict
```

See [`CONTRIBUTING.md`](CONTRIBUTING.md) for change rules and [`SECURITY.md`](SECURITY.md) for disclosure guidance.
