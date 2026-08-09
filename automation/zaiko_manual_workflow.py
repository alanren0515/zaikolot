#!/usr/bin/env python3
"""Prepare a ZAIKO lottery form after the user completes login manually.

This workflow intentionally does not read credentials, bypass bot checks, run
headless, touch registered-card controls, or submit the lottery application.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from urllib.parse import urlparse


LOGIN_URL = "https://akb48.zaiko.io/login"
ALLOWED_HOST = "akb48.zaiko.io"
CHECKBOX_SELECTORS = (
    "#pay-later",
    "#checkboxZaikoTos",
    "#checkboxProfileTos",
)


def validate_target_url(value: str) -> str:
    parsed = urlparse(value)
    if (
        parsed.scheme != "https"
        or parsed.hostname != ALLOWED_HOST
        or parsed.username is not None
        or parsed.password is not None
        or not parsed.path.startswith("/apply/")
    ):
        raise argparse.ArgumentTypeError(
            f"target URL must use https://{ALLOWED_HOST}/apply/ without credentials"
        )
    return value


def ensure_checked(page, selector: str, timeout_ms: int) -> None:
    checkbox = page.locator(selector)
    checkbox.wait_for(state="attached", timeout=timeout_ms)

    if checkbox.is_checked():
        return

    checkbox.click()
    if not checkbox.is_checked():
        raise RuntimeError(f"checkbox did not remain checked: {selector}")


def prepare_application(page, timeout_ms: int) -> None:
    for selector in CHECKBOX_SELECTORS:
        ensure_checked(page, selector, timeout_ms)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Open a visible browser, wait for manual ZAIKO login, and prepare "
            "the three known lottery checkboxes without submitting."
        )
    )
    parser.add_argument(
        "--target-url",
        required=True,
        type=validate_target_url,
        help="Exact akb48.zaiko.io lottery application URL",
    )
    parser.add_argument(
        "--profile-dir",
        type=Path,
        default=Path(__file__).resolve().parent / ".playwright-profile",
        help="Local persistent browser profile directory",
    )
    parser.add_argument(
        "--timeout-seconds",
        type=int,
        default=30,
        help="Maximum wait for each known checkbox (default: 30)",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    if args.timeout_seconds < 1:
        print("--timeout-seconds must be at least 1", file=sys.stderr)
        return 2

    try:
        from playwright.sync_api import sync_playwright
    except ModuleNotFoundError:
        print(
            "Python Playwright is not installed. Install automation/requirements.txt "
            "and the Chromium browser before running this workflow.",
            file=sys.stderr,
        )
        return 2

    profile_dir = args.profile_dir.expanduser().resolve()
    profile_dir.mkdir(parents=True, exist_ok=True)
    timeout_ms = args.timeout_seconds * 1000

    with sync_playwright() as playwright:
        context = playwright.chromium.launch_persistent_context(
            user_data_dir=str(profile_dir),
            headless=False,
        )
        page = context.pages[0] if context.pages else context.new_page()

        page.goto(LOGIN_URL, wait_until="domcontentloaded")
        input(
            "Complete login and any Cloudflare/OTP checks manually in the browser, "
            "then press Enter here to continue... "
        )

        page.goto(args.target_url, wait_until="domcontentloaded")
        prepare_application(page, timeout_ms)

        print("Prepared the three known checkboxes.")
        print("No submit or confirmation button was clicked.")
        input("Review the page, then press Enter to close the browser... ")
        context.close()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
