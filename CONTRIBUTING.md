# Contributing

## Ground rules

- Do not commit keys, webhooks, recipient identifiers, raw social posts, downloaded data, or generated reports.
- Keep collection, analysis, and delivery separate. Output must default to stdout or a user-selected file.
- New remote providers need documented terms, attribution, rate limits, and a test fixture that does not contain real user data.
- This project produces research data, not investment advice or trading instructions.

## Local checks

```bash
python3 -m unittest discover -s tests -v
python3 scripts/secret_scan.py --strict
```

## Pull requests

Describe the source, method, limitations, and test coverage. If a change adds configuration, add an empty placeholder to `.env.example` and document it in the README. Never add a real credential to a test, fixture, commit message, issue, or pull request description.
