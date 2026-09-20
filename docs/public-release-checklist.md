# Public release checklist

Use this checklist before changing visibility to public.

- [ ] `python3 scripts/secret_scan.py --strict` passes.
- [ ] `python3 -m unittest discover -s tests -v` passes.
- [ ] `git status --short` has no `.env`, report, state, database, key, or credential file.
- [ ] `git diff --cached --check` passes.
- [ ] No source, example, documentation, issue template, commit message, or workflow contains a webhook, recipient identifier, account identifier, API key, or personal path.
- [ ] Delivery is still opt-in and disabled in public code.
- [ ] Provider terms, attribution, rate limits, and data-retention rules were reviewed.
- [ ] The README onboarding sequence was tested from a fresh clone.
