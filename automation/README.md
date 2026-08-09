# Zaiko Lottery Assistant desktop prototype

This prototype provides a lightweight Tkinter UI backed by one visible Playwright
Chromium session. Each account gets a separate persistent browser profile.

CSV columns are `label,email,password` (`label` is optional). Import writes each
password to the operating-system Keychain and stores only account labels, email
addresses, and opaque account IDs in local application data. The CSV is never
copied into the repository. For best security, delete or encrypt the plaintext
CSV after confirming the Keychain import.

The program does not click login, interact with Cloudflare/CAPTCHA/OTP, run
headless, use stealth plugins, touch registered-card controls, or submit an
application. Credential filling is disabled by default; enabling test mode lets
the credential button fill the two login fields and then stop for manual
verification and login. Preparing a target requires an explicit confirmation
before the two terms-agreement checkboxes are selected.

## Workflow

1. Import local account metadata and secrets from a CSV into Keychain.
2. Select an account and open its isolated login profile.
3. Optionally fill credentials during testing, then complete login and all
   Cloudflare, CAPTCHA, or OTP checks manually.
4. Open one explicitly supplied `akb48.zaiko.io` application URL.
5. Check only the three selectors already used by the stable extension:
   `#pay-later`, `#checkboxZaikoTos`, and `#checkboxProfileTos`.
6. Stop before the application submit button.

The persistent profile contains session cookies. It is ignored by Git and must
not be copied, shared, or committed.

## Install

On macOS, use the supported Homebrew Python/Tk build instead of the deprecated
system Tk 8.5:

```bash
brew install python@3.14 python-tk@3.14
```

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r automation/requirements.txt
python -m playwright install chromium
```

## Run the desktop UI

```bash
python automation/desktop_app.py
```

The older command-line manual workflow remains available as
`automation/zaiko_manual_workflow.py`.

## Test

```bash
python -m unittest discover -s automation -p "test_*.py"
```
