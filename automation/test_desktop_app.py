from __future__ import annotations

import unittest
from unittest.mock import patch

from account_store import Account
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


class TextRecorder:
    def __init__(self) -> None:
        self.value = ""

    def set(self, value: str) -> None:
        self.value = value


class DesktopAppTests(unittest.TestCase):
    def _active_account_methods(self, account: Account) -> dict:
        return {
            "_selected_account": lambda _self: account,
            "_require_active_account": lambda _self, _account: True,
        }

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
                **self._active_account_methods(Account("one", "测试")),
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
                **self._active_account_methods(Account("one", "测试")),
            },
        )()

        App._prepare(app)

        self.assertEqual(sent, [("prepare_target", "one", target)])

    @patch("desktop_app.messagebox.askokcancel", return_value=True)
    def test_confirmed_event_frame_uses_exact_name(self, _askokcancel) -> None:
        sent: list[tuple] = []
        event_url = "https://akb48.zaiko.io/ja/e/example"
        app = type(
            "FakeApp",
            (),
            {
                "url_var": StringValue(event_url),
                "_send": lambda _self, *args: sent.append(args),
                **self._active_account_methods(Account("one", "测试")),
            },
        )()

        App._prepare_frame(app, "柱の会 会員枠")

        self.assertEqual(
            sent,
            [("prepare_event_frame", "one", event_url, "柱の会 会員枠")],
        )

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

    @patch("desktop_app.messagebox.showwarning")
    def test_rejects_actions_for_non_active_account(self, showwarning) -> None:
        account = Account("two", "账号 B")
        app = type("FakeApp", (), {"active_account_id": "one"})()

        self.assertFalse(App._require_active_account(app, account))

        showwarning.assert_called_once()
        self.assertIn("账号 B", showwarning.call_args.args[1])

    def test_open_result_records_active_account(self) -> None:
        status = TextRecorder()
        app = type(
            "FakeApp",
            (),
            {
                "active_account_id": None,
                "accounts": [Account("one", "账号 A")],
                "status_var": status,
            },
        )()

        App._show_worker_result(app, True, "open_login", "one")

        self.assertEqual(app.active_account_id, "one")
        self.assertIn("账号 A", status.value)

    def test_close_result_clears_active_account(self) -> None:
        status = TextRecorder()
        app = type(
            "FakeApp",
            (),
            {"active_account_id": "one", "status_var": status},
        )()

        App._show_worker_result(app, True, "close", "")

        self.assertIsNone(app.active_account_id)
        self.assertEqual(status.value, "浏览器已关闭。")


if __name__ == "__main__":
    unittest.main()
