# Hermes cron onboarding

Use this only after the local quick start in the README works. The public package is output-first. It does not include a webhook, channel, recipient, or messaging token.

Hermes runs `--script` files from `~/.hermes/scripts/`, not directly from a cloned repository. Keep secrets in your local Hermes environment, never in this repository.

## 1. Create a local wrapper

Copy `jobs/hermes/macro.sh.template` to `~/.hermes/scripts/investment-intelligence-macro.sh`. Replace the `REPO_DIR` placeholder with your absolute clone path. Then make it executable:

```bash
chmod 700 ~/.hermes/scripts/investment-intelligence-macro.sh
```

Repeat with the provided market or innovation template if needed. Review the wrapper before enabling it.

## 2. Test without scheduling

```bash
~/.hermes/scripts/investment-intelligence-macro.sh
```

It should produce a local JSON file under your ignored `reports/` directory. If it does not, fix the local setup before creating a scheduled job.

## 3. Create a local-only Hermes job

In Hermes, `--deliver local` means save output locally under the active Hermes home. It does **not** mean Bot Chat delivery. Bot Chat delivery is explicitly spelled `bot-chat` or `bot-chat:<profile>` and is intentionally not used here.

The supplied wrapper writes its research JSON to your ignored `reports/` directory and emits no stdout on success. `--failure-deliver local` suppresses failure notices outside the local scheduler state. Inspect run state and diagnostics with `hermes cron list` and `hermes cron runs <job-id>`.

```bash
hermes cron create "0 8 * * 1-5" \
  --name investment-intelligence-macro \
  --script investment-intelligence-macro.sh \
  --no-agent \
  --deliver local \
  --failure-deliver local
```

Verify it with:

```bash
hermes cron list
hermes cron run <job-id>
```

## 4. Add delivery separately

Only after the output is correct, add a delivery integration you own. Use the platform's secure credential store or local environment variables. Do not substitute `bot-chat`, a webhook, a recipient identifier, or a messaging target into a public wrapper, config file, issue, or commit.

## 5. Keep it healthy

- Rotate provider keys separately from source control.
- Run `python3 scripts/secret_scan.py --strict` before every push.
- Revisit source terms and rate limits when adding a new collector.
- Review job schedules after daylight-saving or timezone changes.
