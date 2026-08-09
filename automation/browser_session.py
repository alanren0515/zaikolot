"""One visible Playwright session owned by a single worker thread."""

from __future__ import annotations

from pathlib import Path

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


def _fill_first_visible(page, selectors: tuple[str, ...], value: str, field_name: str) -> str:
    for selector in selectors:
        locator = page.locator(selector).first
        if locator.count() and locator.is_visible():
            locator.fill(value)
            return selector
    raise RuntimeError(f"登录页面中找不到可见的{field_name}输入框")


def fill_login_fields(page, email: str, password: str) -> tuple[str, str]:
    """Fill credentials only; never click login or challenge controls."""
    email_selector = _fill_first_visible(page, EMAIL_SELECTORS, email, "账号")
    password_selector = _fill_first_visible(page, PASSWORD_SELECTORS, password, "密码")
    return email_selector, password_selector


class BrowserSession:
    def __init__(self) -> None:
        self._playwright = None
        self._context = None
        self.page = None

    @property
    def is_open(self) -> bool:
        return self._context is not None

    def open_login(self, profile_dir: Path) -> None:
        if self.is_open:
            self.close()
        from playwright.sync_api import sync_playwright

        profile_dir.mkdir(parents=True, exist_ok=True)
        self._playwright = sync_playwright().start()
        self._context = self._playwright.chromium.launch_persistent_context(
            user_data_dir=str(profile_dir),
            headless=False,
        )
        self.page = self._context.pages[0] if self._context.pages else self._context.new_page()
        self.page.goto(LOGIN_URL, wait_until="domcontentloaded")

    def fill_credentials(self, email: str, password: str) -> None:
        if not self.page:
            raise RuntimeError("请先打开登录页面")
        fill_login_fields(self.page, email, password)

    def prepare_target(self, target_url: str, timeout_ms: int = 30_000) -> None:
        if not self.page:
            raise RuntimeError("请先打开浏览器并手动完成登录")
        target_url = validate_target_url(target_url)
        self.page.goto(target_url, wait_until="domcontentloaded")
        prepare_application(self.page, timeout_ms)

    def close(self) -> None:
        try:
            if self._context:
                self._context.close()
        finally:
            self._context = None
            self.page = None
            if self._playwright:
                self._playwright.stop()
                self._playwright = None
