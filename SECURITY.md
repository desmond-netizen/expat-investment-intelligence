# Security policy

## Before you publish

Run this from the repository root:

```bash
python3 scripts/secret_scan.py --strict
python3 -m unittest discover -s tests -v
```

The scanner reports only file, line, and finding type. It intentionally never prints a suspected secret.

Check these items manually too:

- `.env`, token files, private keys, reports, databases, and local state are not tracked.
- No webhook URL, recipient ID, channel selector, account identifier, or machine-specific path appears in staged files.
- Output and notification adapters are disabled by default.
- Example configuration contains placeholders or empty values only.
- Social content, personal data, and generated reports are not committed.

## Reporting a vulnerability

Do not open a public issue containing a credential or exploit detail. Contact the repository maintainer privately and include:

1. A short impact statement.
2. Reproduction steps with all secrets redacted.
3. A proposed remediation if available.

Rotate any credential immediately if it may have been exposed. Git history is not a safe place for a secret, even after deletion.
