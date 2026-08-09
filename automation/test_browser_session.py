from __future__ import annotations

import unittest

from browser_session import fill_login_fields


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


class BrowserSessionTests(unittest.TestCase):
    def test_fill_login_fields_only_fills_two_inputs(self) -> None:
        page = FakePage()

        fill_login_fields(page, "me@example.com", "secret")

        self.assertEqual(page.locators['#identifier-input'].value, "me@example.com")
        self.assertEqual(page.locators['input[type="password"]'].value, "secret")
        self.assertEqual(len(page.requested), 2)


if __name__ == "__main__":
    unittest.main()
