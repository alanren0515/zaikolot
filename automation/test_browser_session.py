from __future__ import annotations

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from browser_session import BrowserSession, fill_login_fields


class FakeLocator:
    def __init__(self, visible: bool = False) -> None:
        self.visible = visible
        self.value = None
        self.first = self

    def count(self) -> int:
        return 1 if self.visible else 0

    def is_visible(self) -> bool:
        return self.visible

    def fill(self, value: str) -> None:
        self.value = value


class FakePage:
    def __init__(self) -> None:
        self.locators = {
            '#identifier-input': FakeLocator(True),
            'input[type="password"]': FakeLocator(True),
        }
        self.requested: list[str] = []

    def locator(self, selector: str) -> FakeLocator:
        self.requested.append(selector)
        return self.locators.get(selector, FakeLocator())

    def goto(self, url: str, **_kwargs) -> None:
        self.goto_urls = getattr(self, "goto_urls", [])
        self.goto_urls.append(url)


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

    def launch_persistent_context(self, *, user_data_dir: str, headless: bool) -> FakeContext:
        self.profile_dirs.append(user_data_dir)
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

    def test_same_profile_reuses_context(self) -> None:
        with TemporaryDirectory() as directory:
            factory = PlaywrightFactory()
            session = BrowserSession(factory)
            profile = Path(directory) / "one"

            session.open_login(profile)
            first_context = factory.instances[0].chromium.contexts[0]
            session.open_login(profile)

            self.assertEqual(len(factory.instances), 1)
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
