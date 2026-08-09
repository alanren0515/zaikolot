from __future__ import annotations

import argparse
import unittest

from zaiko_manual_workflow import CHECKBOX_SELECTORS
from zaiko_manual_workflow import prepare_application
from zaiko_manual_workflow import validate_target_url


class FakeLocator:
    def __init__(self, checked: bool = False, stays_checked: bool = True) -> None:
        self.checked = checked
        self.stays_checked = stays_checked
        self.click_count = 0

    def wait_for(self, **_kwargs) -> None:
        return None

    def is_checked(self) -> bool:
        return self.checked

    def click(self) -> None:
        self.click_count += 1
        self.checked = self.stays_checked


class FakePage:
    def __init__(self, locators: dict[str, FakeLocator]) -> None:
        self.locators = locators
        self.requested_selectors: list[str] = []

    def locator(self, selector: str) -> FakeLocator:
        self.requested_selectors.append(selector)
        return self.locators[selector]


class WorkflowTests(unittest.TestCase):
    def test_prepares_only_the_three_baseline_checkboxes(self) -> None:
        locators = {selector: FakeLocator() for selector in CHECKBOX_SELECTORS}
        page = FakePage(locators)

        prepare_application(page, timeout_ms=1000)

        self.assertEqual(page.requested_selectors, list(CHECKBOX_SELECTORS))
        self.assertTrue(all(locator.checked for locator in locators.values()))
        self.assertTrue(all(locator.click_count == 1 for locator in locators.values()))

    def test_does_not_click_an_already_checked_checkbox(self) -> None:
        locators = {selector: FakeLocator(checked=True) for selector in CHECKBOX_SELECTORS}
        page = FakePage(locators)

        prepare_application(page, timeout_ms=1000)

        self.assertTrue(all(locator.click_count == 0 for locator in locators.values()))

    def test_stops_if_a_checkbox_does_not_stay_checked(self) -> None:
        locators = {selector: FakeLocator() for selector in CHECKBOX_SELECTORS}
        locators[CHECKBOX_SELECTORS[0]] = FakeLocator(stays_checked=False)
        page = FakePage(locators)

        with self.assertRaisesRegex(RuntimeError, CHECKBOX_SELECTORS[0]):
            prepare_application(page, timeout_ms=1000)

        self.assertEqual(page.requested_selectors, [CHECKBOX_SELECTORS[0]])

    def test_rejects_non_zaiko_targets(self) -> None:
        with self.assertRaises(argparse.ArgumentTypeError):
            validate_target_url("https://example.com/apply/123")

    def test_rejects_non_application_paths(self) -> None:
        with self.assertRaises(argparse.ArgumentTypeError):
            validate_target_url("https://akb48.zaiko.io/login")

    def test_rejects_credentials_embedded_in_url(self) -> None:
        with self.assertRaises(argparse.ArgumentTypeError):
            validate_target_url("https://user:secret@akb48.zaiko.io/apply/example")

    def test_accepts_https_akb48_target(self) -> None:
        value = "https://akb48.zaiko.io/apply/example"
        self.assertEqual(validate_target_url(value), value)


if __name__ == "__main__":
    unittest.main()
