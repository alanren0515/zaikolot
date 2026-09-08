"""One visible Playwright session owned by a single worker thread."""

from __future__ import annotations

from pathlib import Path
from time import monotonic

from zaiko_event_workflow import find_frame_application_url, validate_event_url
from zaiko_manual_workflow import LOGIN_URL, prepare_application, validate_target_url


EMAIL_SELECTORS = (
    '#identifier-input',
    'input[name="identifier"]',
    'input[type="email"]',
    'input[name="email"]',
    '#email',
)
PASSWORD_SELECTORS = (
    'input[type="password"]',
    'input[name="password"]',
    '#password',
)
LOGIN_SUBMIT_SELECTORS = (
    'button[type="submit"]',
    'input[type="submit"]',
)
CLOUDFLARE_SELECTORS = (
    'iframe[src*="challenges.cloudflare.com"]',
    '.cf-turnstile',
    'input[name="cf-turnstile-response"]',
)


def _fill_first_visible(
    page,
    selectors: tuple[str, ...],
    value: str,
    field_name: str,
    timeout_ms: int,
) -> str:
    deadline = monotonic() + timeout_ms / 1000
    while True:
        for selector in selectors:
            locator = page.locator(selector).first
            if locator.count() and locator.is_visible():
                locator.fill(value)
                return selector
        remaining_ms = int((deadline - monotonic()) * 1000)
        if remaining_ms <= 0:
            break
        page.wait_for_timeout(min(100, remaining_ms))
    raise RuntimeError(f"登录页面中找不到可见的{field_name}输入框")


def fill_login_fields(
    page, email: str, password: str, timeout_ms: int = 15_000
) -> tuple[str, str]:
    """Fill credentials only; never click login or challenge controls."""
    email_selector = _fill_first_visible(
        page, EMAIL_SELECTORS, email, "账号", timeout_ms
    )
    password_selector = _fill_first_visible(
        page, PASSWORD_SELECTORS, password, "密码", timeout_ms
    )
    return email_selector, password_selector


def _first_visible(page, selectors: tuple[str, ...]):
    for selector in selectors:
        locator = page.locator(selector).first
        if locator.count() and locator.is_visible():
            return locator
    return None


def submit_login(page, email: str, password: str, timeout_ms: int = 15_000) -> str:
    """Fill and submit login once without interacting with bot challenges."""
    fill_login_fields(page, email, password, timeout_ms)
    submit = _first_visible(page, LOGIN_SUBMIT_SELECTORS)
    if submit is None:
        raise RuntimeError("登录页面中找不到可见的登录按钮")

    try:
        submit.click(timeout=min(timeout_ms, 5_000))
    except Exception as exc:
        if _first_visible(page, CLOUDFLARE_SELECTORS) is not None:
            return "manual_verification_required"
        raise RuntimeError("登录按钮未能完成点击") from exc

    page.wait_for_timeout(min(timeout_ms, 3_000))
    if "/login" not in page.url:
        return "logged_in"
    if _first_visible(page, CLOUDFLARE_SELECTORS) is not None:
        return "manual_verification_required"
    return "login_not_completed"


class BrowserSession:
    def __init__(self, playwright_factory=None, browser_channel: str | None = "chrome") -> None:
        self._playwright_factory = playwright_factory
        self._browser_channel = browser_channel
        self._playwright = None
        self._context = None
        self._profile_dir: Path | None = None
        self.page = None

    @property
    def is_open(self) -> bool:
        return self._context is not None

    def _ensure_active_profile(self, expected_account_id: str) -> None:
        if (
            not self.page
            or self._profile_dir is None
            or self._profile_dir.name != expected_account_id
        ):
            raise RuntimeError("浏览器账号会话已变化，请重新打开所选账号")

    def open_login(self, profile_dir: Path) -> str:
        profile_dir = profile_dir.expanduser().resolve()
        if self.is_open and profile_dir == self._profile_dir:
            self.page.goto(LOGIN_URL, wait_until="domcontentloaded")
            return profile_dir.name
        if self.is_open:
            self.close()

        profile_dir.mkdir(parents=True, exist_ok=True)
        if self._playwright_factory is None:
            from playwright.sync_api import sync_playwright

            self._playwright = sync_playwright().start()
        else:
            self._playwright = self._playwright_factory()
        try:
            launch_options = {
                "user_data_dir": str(profile_dir),
                "headless": False,
            }
            if self._browser_channel:
                launch_options["channel"] = self._browser_channel
            self._context = self._playwright.chromium.launch_persistent_context(
                **launch_options
            )
        except Exception:
            self.close()
            raise
        self._profile_dir = profile_dir
        self.page = self._context.pages[0] if self._context.pages else self._context.new_page()
        self.page.goto(LOGIN_URL, wait_until="domcontentloaded")
        return profile_dir.name

    def fill_credentials(
        self, expected_account_id: str, email: str, password: str
    ) -> None:
        self._ensure_active_profile(expected_account_id)
        fill_login_fields(self.page, email, password)

    def attempt_login(
        self, expected_account_id: str, email: str, password: str
    ) -> str:
        self._ensure_active_profile(expected_account_id)
        return submit_login(self.page, email, password)

    def prepare_event_frame(
        self,
        expected_account_id: str,
        event_url: str,
        frame_name: str,
        timeout_ms: int = 30_000,
    ) -> str:
        self._ensure_active_profile(expected_account_id)
        event_url = validate_event_url(event_url)
        self.page.goto(event_url, wait_until="domcontentloaded")
        target = find_frame_application_url(self.page, frame_name, timeout_ms)
        self.page.goto(target, wait_until="domcontentloaded")

        deadline = monotonic() + timeout_ms / 1000
        while monotonic() < deadline:
            if self.page.locator("#pay-later").count():
                prepare_application(self.page, timeout_ms)
                return "prepared"
            if _first_visible(self.page, EMAIL_SELECTORS) is not None:
                return "login_required"
            self.page.wait_for_timeout(200)
        return "manual_step_required"

    def prepare_target(
        self,
        expected_account_id: str,
        target_url: str,
        timeout_ms: int = 30_000,
    ) -> None:
        self._ensure_active_profile(expected_account_id)
        target_url = validate_target_url(target_url)
        self.page.goto(target_url, wait_until="domcontentloaded")
        prepare_application(self.page, timeout_ms)

    def close(self) -> None:
        try:
            if self._context:
                self._context.close()
        finally:
            self._context = None
            self._profile_dir = None
            self.page = None
            if self._playwright:
                self._playwright.stop()
                self._playwright = None
