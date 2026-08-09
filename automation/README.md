# Zaiko Lottery Assistant desktop prototype

This prototype provides a lightweight Tkinter UI backed by one visible Playwright
Chromium session. Each account gets a separate persistent browser profile.

CSV columns are `label,email,password` (`label` is optional). Import writes each
email/password pair to the operating-system Keychain and stores only account
labels and opaque account IDs in local application data. The CSV is never
copied into the repository. For best security, delete or encrypt the plaintext
CSV after confirming the Keychain import.

The program does not interact with Cloudflare/CAPTCHA/OTP, run headless, use
stealth plugins, touch registered-card controls, or submit an application.
Credential use is disabled by default. Enabling test mode provides one action
that only fills the two login fields and another explicitly confirmed action
that fills them and clicks the site's login button once. Both stop for manual
verification when the site requires it. Preparing a target requires an explicit
confirmation before the two terms-agreement checkboxes are selected.

## Workflow

1. Import local account metadata and secrets from a CSV into Keychain.
2. Select an account and open its isolated login profile.
3. Optionally fill credentials during testing or explicitly attempt one login,
   then complete all Cloudflare, CAPTCHA, or OTP checks manually.
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

## Build a double-clickable macOS app

The app bundle uses the separately installed Playwright Chromium from
`~/Library/Caches/ms-playwright`, so the browser is not copied into Git or the
application bundle. The application sets `PLAYWRIGHT_BROWSERS_PATH` to that
shared macOS cache unless the environment already provides an explicit value.

```bash
.venv/bin/python -m pip install -r automation/requirements-dev.txt
automation/build_macos_app.sh
```

The generated application is `dist/Zaiko Lottery Assistant.app`. Both `build/`
and `dist/` are ignored by Git.

A provider-free packaged-runtime check is available for release verification:

```bash
'dist/Zaiko Lottery Assistant.app/Contents/MacOS/Zaiko Lottery Assistant' \
  --package-smoke-test
```

The older command-line manual workflow remains available as
`automation/zaiko_manual_workflow.py`.

## Test

```bash
python -m unittest discover -s automation -p "test_*.py"
```
