from __future__ import annotations

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from browser_session import BrowserSession, fill_login_fields, submit_login


class FakeLocator:
    def __init__(self, visible: bool = False) -> None:
        self.visible = visible
        self.value = None
        self.first = self
        self.click_count = 0

    def count(self) -> int:
        return 1 if self.visible else 0

    def is_visible(self) -> bool:
        return self.visible

    def fill(self, value: str) -> None:
        self.value = value

    def click(self, **_kwargs) -> None:
        self.click_count += 1


class FakePage:
    def __init__(self, reveal_after_wait: bool = False) -> None:
        self.reveal_after_wait = reveal_after_wait
        self.locators = {
            '#identifier-input': FakeLocator(not reveal_after_wait),
            'input[type="password"]': FakeLocator(not reveal_after_wait),
            'button[type="submit"]': FakeLocator(True),
        }
        self.requested: list[str] = []
        self.url = "https://akb48.zaiko.io/login"

    def locator(self, selector: str) -> FakeLocator:
        self.requested.append(selector)
        return self.locators.get(selector, FakeLocator())

    def goto(self, url: str, **_kwargs) -> None:
        self.goto_urls = getattr(self, "goto_urls", [])
        self.goto_urls.append(url)

    def wait_for_timeout(self, _timeout_ms: int) -> None:
        if self.reveal_after_wait:
            self.locators['#identifier-input'].visible = True
            self.locators['input[type="password"]'].visible = True
            self.reveal_after_wait = False


class FakeContext:
    def __init__(self) -> None:
        self.pages = [FakePage()]
        self.close_count = 0

    def close(self) -> None:
        self.close_count += 1

    def new_page(self) -> FakePage:
        page = FakePage()
        self.pages.append(page)
        return page


class FakeChromium:
    def __init__(self) -> None:
        self.contexts: list[FakeContext] = []
        self.profile_dirs: list[str] = []
        self.channels: list[str | None] = []

    def launch_persistent_context(
        self, *, user_data_dir: str, headless: bool, channel: str | None = None
    ) -> FakeContext:
        self.profile_dirs.append(user_data_dir)
        self.channels.append(channel)
        context = FakeContext()
        self.contexts.append(context)
        return context


class FakePlaywright:
    def __init__(self) -> None:
        self.chromium = FakeChromium()
        self.stop_count = 0

    def stop(self) -> None:
        self.stop_count += 1


class PlaywrightFactory:
    def __init__(self) -> None:
        self.instances: list[FakePlaywright] = []

    def __call__(self) -> FakePlaywright:
        instance = FakePlaywright()
        self.instances.append(instance)
        return instance


class BrowserSessionTests(unittest.TestCase):
    def test_fill_login_fields_only_fills_two_inputs(self) -> None:
        page = FakePage()

        fill_login_fields(page, "me@example.com", "secret")

        self.assertEqual(page.locators['#identifier-input'].value, "me@example.com")
        self.assertEqual(page.locators['input[type="password"]'].value, "secret")
        self.assertEqual(len(page.requested), 2)

    def test_fill_login_fields_waits_for_delayed_form(self) -> None:
        page = FakePage(reveal_after_wait=True)

        fill_login_fields(page, "me@example.com", "secret", timeout_ms=500)

        self.assertEqual(page.locators['#identifier-input'].value, "me@example.com")
        self.assertEqual(page.locators['input[type="password"]'].value, "secret")

    def test_submit_login_clicks_only_submit_and_reports_pending(self) -> None:
        page = FakePage()

        result = submit_login(page, "me@example.com", "secret")

        self.assertEqual(result, "login_not_completed")
        self.assertEqual(page.locators['button[type="submit"]'].click_count, 1)

    def test_submit_login_reports_success_after_navigation(self) -> None:
        page = FakePage()
        page.url = "https://akb48.zaiko.io/account"

        self.assertEqual(submit_login(page, "me@example.com", "secret"), "logged_in")

    @patch("browser_session.find_frame_application_url", return_value="https://akb48.zaiko.io/buy/example")
    def test_event_frame_reports_login_required(self, _find_url) -> None:
        session = BrowserSession()
        session.page = FakePage()
        session._profile_dir = Path("/profiles/one")

        result = session.prepare_event_frame(
            "one",
            "https://akb48.zaiko.io/ja/e/example",
            "映像倉庫会員枠",
            timeout_ms=500,
        )

        self.assertEqual(result, "login_required")
        self.assertEqual(
            session.page.goto_urls,
            [
                "https://akb48.zaiko.io/ja/e/example",
                "https://akb48.zaiko.io/buy/example",
            ],
        )

    def test_rejects_queued_action_after_profile_switch(self) -> None:
        session = BrowserSession()
        session.page = FakePage()
        session._profile_dir = Path("/profiles/two")

        with self.assertRaisesRegex(RuntimeError, "会话已变化"):
            session.fill_credentials("one", "me@example.com", "secret")

    def test_same_profile_reuses_context(self) -> None:
        with TemporaryDirectory() as directory:
            factory = PlaywrightFactory()
            session = BrowserSession(factory)
            profile = Path(directory) / "one"

            opened_profile = session.open_login(profile)
            first_context = factory.instances[0].chromium.contexts[0]
            session.open_login(profile)

            self.assertEqual(len(factory.instances), 1)
            self.assertEqual(opened_profile, "one")
            self.assertEqual(factory.instances[0].chromium.channels, ["chrome"])
            self.assertEqual(first_context.close_count, 0)
            self.assertEqual(len(first_context.pages[0].goto_urls), 2)
            session.close()

    def test_different_profile_closes_old_context(self) -> None:
        with TemporaryDirectory() as directory:
            factory = PlaywrightFactory()
            session = BrowserSession(factory)

            session.open_login(Path(directory) / "one")
            first_playwright = factory.instances[0]
            first_context = first_playwright.chromium.contexts[0]
            session.open_login(Path(directory) / "two")

            self.assertEqual(first_context.close_count, 1)
            self.assertEqual(first_playwright.stop_count, 1)
            self.assertEqual(len(factory.instances), 2)
            session.close()


if __name__ == "__main__":
    unittest.main()
