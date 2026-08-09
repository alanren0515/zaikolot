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


class StringValue:
    def __init__(self, value: str) -> None:
        self.value = value

    def get(self) -> str:
        return self.value


class BooleanValue:
    def __init__(self, value: bool) -> None:
        self.value = value

    def get(self) -> bool:
        return self.value


class StateRecorder:
    def __init__(self) -> None:
        self.states: list[str] = []

    def configure(self, *, state: str) -> None:
        self.states.append(state)


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

    @patch("desktop_app.messagebox.askokcancel", return_value=False)
    def test_cancelled_terms_confirmation_does_not_prepare(self, _askokcancel) -> None:
        sent: list[tuple] = []
        app = type(
            "FakeApp",
            (),
            {
                "url_var": StringValue("https://akb48.zaiko.io/apply/example"),
                "_send": lambda _self, *args: sent.append(args),
            },
        )()

        App._prepare(app)

        self.assertEqual(sent, [])

    @patch("desktop_app.messagebox.askokcancel", return_value=True)
    def test_confirmed_terms_prepares_exact_target(self, _askokcancel) -> None:
        sent: list[tuple] = []
        target = "https://akb48.zaiko.io/apply/example"
        app = type(
            "FakeApp",
            (),
            {
                "url_var": StringValue(target),
                "_send": lambda _self, *args: sent.append(args),
            },
        )()

        App._prepare(app)

        self.assertEqual(sent, [("prepare_target", target)])

    def test_test_mode_controls_credential_button_state(self) -> None:
        fill_button = StateRecorder()
        login_button = StateRecorder()
        app = type(
            "FakeApp",
            (),
            {
                "fill_button": fill_button,
                "login_button": login_button,
                "test_mode_var": BooleanValue(True),
            },
        )()

        App._update_test_mode(app)
        app.test_mode_var = BooleanValue(False)
        App._update_test_mode(app)

        self.assertEqual(fill_button.states, ["normal", "disabled"])
        self.assertEqual(login_button.states, ["normal", "disabled"])


if __name__ == "__main__":
    unittest.main()
