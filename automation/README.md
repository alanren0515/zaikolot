# Playwright manual-session prototype

This prototype uses one visible Chromium context and a local persistent profile.
It does not accept credentials, read account CSV files, run headless, use stealth
plugins, bypass Cloudflare, touch registered-card controls, or submit an
application.

## Workflow

1. Open the ZAIKO login page in a visible browser.
2. Complete login, Cloudflare, CAPTCHA, or OTP checks manually.
3. Open one explicitly supplied `akb48.zaiko.io` application URL.
4. Check only the three selectors already used by the stable extension:
   `#pay-later`, `#checkboxZaikoTos`, and `#checkboxProfileTos`.
5. Stop before the application submit button.

The persistent profile contains session cookies. It is ignored by Git and must
not be copied, shared, or committed.

## Install

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r automation/requirements.txt
python -m playwright install chromium
```

## Run

```bash
python automation/zaiko_manual_workflow.py \
  --target-url "https://akb48.zaiko.io/apply/your-target"
```

## Test

```bash
python -m unittest discover -s automation -p "test_*.py"
```
