from __future__ import annotations

import argparse
import unittest

from zaiko_event_workflow import (
    SUPPORTED_FRAMES,
    find_frame_application_url,
    validate_event_url,
    validate_frame_name,
)


class FakeLink:
    def __init__(self, href: str | None) -> None:
        self.href = href
        self.first = self

    def wait_for(self, **_kwargs) -> None:
        pass

    def get_attribute(self, name: str) -> str | None:
        return self.href if name == "href" else None


class FakeCard:
    def __init__(self, href: str | None) -> None:
        self.link = FakeLink(href)

    def get_by_role(self, role: str, **kwargs) -> FakeLink:
        if role != "link" or kwargs != {"name": "抽選応募", "exact": True}:
            raise AssertionError("unexpected role lookup")
        return self.link


class FakeLabel:
    def __init__(self, href: str | None) -> None:
        self.card = FakeCard(href)
        self.first = self

    def wait_for(self, **_kwargs) -> None:
        pass

    def locator(self, selector: str) -> FakeCard:
        if "抽選応募" not in selector:
            raise AssertionError("unexpected ancestor selector")
        return self.card


class FakePage:
    url = "https://akb48.zaiko.io/ja/e/example"

    def __init__(self, href: str | None) -> None:
        self.href = href
        self.requested_text: str | None = None

    def get_by_text(self, text: str, *, exact: bool) -> FakeLabel:
        if not exact:
            raise AssertionError("frame lookup must be exact")
        self.requested_text = text
        return FakeLabel(self.href)


class EventWorkflowTests(unittest.TestCase):
    def test_accepts_localized_event_url(self) -> None:
        value = "https://akb48.zaiko.io/ja/e/reset-aug17-1830"
        self.assertEqual(validate_event_url(value), value)

    def test_rejects_non_event_and_external_urls(self) -> None:
        for value in (
            "https://akb48.zaiko.io/apply/example",
            "https://example.com/ja/e/example",
        ):
            with self.subTest(value=value), self.assertRaises(argparse.ArgumentTypeError):
                validate_event_url(value)

    def test_allows_only_two_explicit_frames(self) -> None:
        self.assertEqual(validate_frame_name(SUPPORTED_FRAMES[0]), SUPPORTED_FRAMES[0])
        with self.assertRaises(ValueError):
            validate_frame_name("一般枠")

    def test_finds_buy_link_inside_exact_frame_card(self) -> None:
        page = FakePage("/buy/example")

        result = find_frame_application_url(page, SUPPORTED_FRAMES[1], 1_000)

        self.assertEqual(result, "https://akb48.zaiko.io/buy/example")
        self.assertEqual(page.requested_text, SUPPORTED_FRAMES[1])

    def test_rejects_frame_link_outside_allowed_buy_path(self) -> None:
        page = FakePage("https://example.com/buy/example")
        with self.assertRaises(RuntimeError):
            find_frame_application_url(page, SUPPORTED_FRAMES[0], 1_000)


if __name__ == "__main__":
    unittest.main()
