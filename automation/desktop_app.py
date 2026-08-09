#!/usr/bin/env python3
"""Lightweight local UI for a manual ZAIKO lottery preparation workflow."""

from __future__ import annotations

import os
import queue
import sys
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from account_store import Account, AccountStore
from browser_session import BrowserSession
from browser_session import fill_login_fields
from zaiko_manual_workflow import CHECKBOX_SELECTORS, prepare_application


APP_DATA_DIR = Path.home() / "Library" / "Application Support" / "Zaiko Lottery Assistant"
PLAYWRIGHT_CACHE_DIR = Path.home() / "Library" / "Caches" / "ms-playwright"
os.environ.setdefault("PLAYWRIGHT_BROWSERS_PATH", str(PLAYWRIGHT_CACHE_DIR))


def run_package_smoke_test() -> int:
    """Verify packaged Playwright assets without network or persistent data."""
    from playwright.sync_api import sync_playwright

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        page = browser.new_page()
        controls = "".join(f'<input type="checkbox" id="{selector[1:]}">' for selector in CHECKBOX_SELECTORS)
        page.set_content(f'<input type="email"><input type="password">{controls}')
        fill_login_fields(page, "smoke@example.invalid", "not-a-real-password")
        prepare_application(page, 3_000)
        if not all(page.locator(selector).is_checked() for selector in CHECKBOX_SELECTORS):
            browser.close()
            return 1
        browser.close()
    return 0


def is_dark_theme(window, style: ttk.Style) -> bool:
    try:
        return bool(int(window.tk.call("tk::unsupported::MacWindowStyle", "isdark", window._w)))
    except (tk.TclError, TypeError, ValueError):
        background = style.lookup("TFrame", "background") or window.cget("background")
        red, green, blue = window.winfo_rgb(background)
        return (red * 299 + green * 587 + blue * 114) / 1000 < 32768


class BrowserWorker:
    def __init__(self) -> None:
        self.commands: queue.Queue = queue.Queue()
        self.results: queue.Queue = queue.Queue()
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()

    def submit(self, name: str, *args) -> None:
        self.commands.put((name, args))

    def _run(self) -> None:
        session = BrowserSession()
        while True:
            name, args = self.commands.get()
            try:
                if name == "quit":
                    session.close()
                    return
                getattr(session, name)(*args)
                self.results.put((True, name, ""))
            except Exception as exc:
                self.results.put((False, name, str(exc)))


class App(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Zaiko Lottery Assistant")
        self.geometry("620x430")
        self.minsize(560, 400)
        self.store = AccountStore(APP_DATA_DIR)
        self.accounts: list[Account] = []
        self.worker = BrowserWorker()
        self._build()
        self._reload_accounts()
        self.after(100, self._poll_worker)
        self.protocol("WM_DELETE_WINDOW", self._close)

    def _build(self) -> None:
        style = ttk.Style(self)
        is_dark = is_dark_theme(self, style)
        primary = "#f2f2f2" if is_dark else "#202020"
        secondary = "#c7c7c7" if is_dark else "#555555"
        surface = "#1c1c1e" if is_dark else "#f2f2f2"
        border = "#444446" if is_dark else "#c8c8c8"

        root = tk.Frame(self, padx=24, pady=24, background=surface)
        root.pack(fill="both", expand=True)
        root.columnconfigure(0, weight=1)

        tk.Label(
            root,
            text="Zaiko Lottery Assistant",
            font=("TkDefaultFont", 18, "bold"),
            foreground=primary,
            background=surface,
        ).grid(
            row=0, column=0, sticky="w"
        )
        tk.Label(
            root,
            text="登录与验证由你完成；程序只准备指定的三个选项。",
            foreground=secondary,
            background=surface,
        ).grid(
            row=1, column=0, sticky="w", pady=(4, 20)
        )

        account_frame = tk.LabelFrame(
            root,
            text="账号会话",
            padx=12,
            pady=12,
            foreground=primary,
            background=surface,
            highlightbackground=border,
            highlightcolor=border,
            highlightthickness=1,
            borderwidth=0,
        )
        account_frame.grid(row=2, column=0, sticky="ew")
        account_frame.columnconfigure(0, weight=1)
        self.account_box = ttk.Combobox(account_frame, state="readonly")
        self.account_box.grid(row=0, column=0, sticky="ew", padx=(0, 8))
        ttk.Button(account_frame, text="导入 CSV", command=self._import_csv).grid(row=0, column=1)
        ttk.Button(account_frame, text="打开/切换账号登录", command=self._open_login).grid(
            row=1, column=0, sticky="ew", pady=(10, 0), padx=(0, 8)
        )
        self.fill_button = ttk.Button(
            account_frame,
            text="仅填入账号密码",
            command=self._fill_credentials,
            state="disabled",
        )
        self.fill_button.grid(
            row=1, column=1, sticky="ew", pady=(10, 0)
        )
        self.test_mode_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            account_frame,
            text="测试模式：允许填入凭据",
            variable=self.test_mode_var,
            command=self._update_test_mode,
        ).grid(row=2, column=0, columnspan=2, sticky="w", pady=(10, 0))

        target_frame = tk.LabelFrame(
            root,
            text="抽选页面",
            padx=12,
            pady=12,
            foreground=primary,
            background=surface,
            highlightbackground=border,
            highlightcolor=border,
            highlightthickness=1,
            borderwidth=0,
        )
        target_frame.grid(row=3, column=0, sticky="ew", pady=16)
        target_frame.columnconfigure(0, weight=1)
        self.url_var = tk.StringVar()
        ttk.Entry(target_frame, textvariable=self.url_var).grid(row=0, column=0, sticky="ew", padx=(0, 8))
        ttk.Button(target_frame, text="打开并勾选", command=self._prepare).grid(row=0, column=1)

        controls = tk.Frame(root, background=surface)
        controls.grid(row=4, column=0, sticky="ew")
        ttk.Button(controls, text="关闭浏览器", command=lambda: self._send("close")).pack(side="right")
        self.status_var = tk.StringVar(value="就绪")
        tk.Label(
            root,
            textvariable=self.status_var,
            wraplength=560,
            foreground=secondary,
            background=surface,
        ).grid(
            row=5, column=0, sticky="w", pady=(22, 0)
        )

    def _reload_accounts(self) -> None:
        self.accounts = self.store.load()
        self.account_box["values"] = [item.label for item in self.accounts]
        if self.accounts and self.account_box.current() < 0:
            self.account_box.current(0)

    def _update_test_mode(self) -> None:
        self.fill_button.configure(state="normal" if self.test_mode_var.get() else "disabled")

    def _selected_account(self) -> Account | None:
        index = self.account_box.current()
        if index < 0:
            messagebox.showwarning("需要账号", "请先导入并选择一个账号。")
            return None
        return self.accounts[index]

    def _import_csv(self) -> None:
        path = filedialog.askopenfilename(filetypes=[("CSV", "*.csv")])
        if not path:
            return
        try:
            imported = self.store.import_csv(Path(path))
            self._reload_accounts()
            messagebox.showinfo(
                "导入完成",
                f"已导入 {len(imported)} 个账号。密码已写入系统 Keychain；CSV 不会复制进项目。",
            )
        except Exception as exc:
            messagebox.showerror("导入失败", str(exc))

    def _open_login(self) -> None:
        account = self._selected_account()
        if account:
            self._send("open_login", self.store.profile_dir(account))

    def _fill_credentials(self) -> None:
        account = self._selected_account()
        if not account:
            return
        try:
            email, password = self.store.credentials_for(account)
        except Exception as exc:
            messagebox.showerror("无法读取密码", str(exc))
            return
        self._send("fill_credentials", email, password)

    def _prepare(self) -> None:
        target = self.url_var.get().strip()
        if not target:
            messagebox.showwarning("需要 URL", "请输入具体的抽选申请 URL。")
            return
        confirmed = messagebox.askokcancel(
            "确认勾选",
            "程序将勾选“当选后以其他方式支付”以及两项使用条款同意框。\n\n"
            "不会点击最终抽选提交。是否继续？",
        )
        if not confirmed:
            return
        self._send("prepare_target", target)

    def _send(self, name: str, *args) -> None:
        labels = {
            "open_login": "正在打开独立账号会话…",
            "fill_credentials": "正在填入账号密码（不会点击登录）…",
            "prepare_target": "正在打开目标页面并勾选指定选项…",
            "close": "正在关闭浏览器…",
        }
        self.status_var.set(labels.get(name, "处理中…"))
        self.worker.submit(name, *args)

    def _poll_worker(self) -> None:
        try:
            while True:
                self._show_worker_result(*self.worker.results.get_nowait())
        except queue.Empty:
            pass
        self.after(100, self._poll_worker)

    def _show_worker_result(self, ok: bool, name: str, detail: str) -> None:
        if not ok:
            self.status_var.set(f"失败：{detail}")
            messagebox.showerror("操作失败", detail)
            return
        messages = {
            "open_login": "登录页面已打开。请手动完成登录和 Cloudflare 验证。",
            "fill_credentials": "账号密码已填入；请手动完成验证并点击登录。",
            "prepare_target": "三个指定选项已勾选；程序没有点击抽选提交。",
            "close": "浏览器已关闭。",
        }
        self.status_var.set(messages.get(name, "完成"))

    def _close(self) -> None:
        self.worker.submit("quit")
        self.destroy()


if __name__ == "__main__":
    if "--package-smoke-test" in sys.argv:
        raise SystemExit(run_package_smoke_test())
    App().mainloop()
