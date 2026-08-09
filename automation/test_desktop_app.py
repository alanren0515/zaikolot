from __future__ import annotations

import unittest

from desktop_app import is_dark_theme


class FakeTk:
    def __init__(self, value) -> None:
        self.value = value

    def call(self, *_args):
        return self.value


class FakeWindow:
    _w = "."

    def __init__(self, value) -> None:
        self.tk = FakeTk(value)


class DesktopAppTests(unittest.TestCase):
    def test_uses_native_macos_dark_mode_signal(self) -> None:
        self.assertTrue(is_dark_theme(FakeWindow(1), object()))
        self.assertFalse(is_dark_theme(FakeWindow(0), object()))


if __name__ == "__main__":
    unittest.main()
