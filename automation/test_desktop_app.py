from __future__ import annotations

import unittest
from unittest.mock import patch

from desktop_app import App, is_dark_theme


class FakeTk:
    def __init__(self, value) -> None:
        self.value = value

    def call(self, *_args):
        return self.value


class FakeWindow:
    _w = "."

    def __init__(self, value) -> None:
        self.tk = FakeTk(value)


class EmptyAccountBox:
    def current(self) -> int:
        return -1


class DesktopAppTests(unittest.TestCase):
    def test_uses_native_macos_dark_mode_signal(self) -> None:
        self.assertTrue(is_dark_theme(FakeWindow(1), object()))
        self.assertFalse(is_dark_theme(FakeWindow(0), object()))

    @patch("desktop_app.messagebox.showwarning")
    def test_missing_account_shows_warning(self, showwarning) -> None:
        app = type("FakeApp", (), {"account_box": EmptyAccountBox(), "accounts": []})()

        selected = App._selected_account(app)

        self.assertIsNone(selected)
        showwarning.assert_called_once_with("需要账号", "请先导入并选择一个账号。")


if __name__ == "__main__":
    unittest.main()
