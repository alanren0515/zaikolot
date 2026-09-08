from __future__ import annotations

import csv
import json
import tempfile
import unittest
from pathlib import Path

from account_store import AccountStore


class MemorySecrets:
    def __init__(self) -> None:
        self.values: dict[str, str] = {}

    def set(self, account_id: str, password: str) -> None:
        self.values[account_id] = password

    def get(self, account_id: str) -> str | None:
        return self.values.get(account_id)


class AccountStoreTests(unittest.TestCase):
    def test_import_keeps_password_out_of_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "accounts.csv"
            with source.open("w", newline="", encoding="utf-8") as handle:
                writer = csv.DictWriter(handle, fieldnames=["label", "email", "password"])
                writer.writeheader()
                writer.writerow({"label": "测试", "email": "me@example.com", "password": "secret"})
            secrets = MemorySecrets()
            store = AccountStore(root / "data", secrets)

            accounts = store.import_csv(source)
            metadata = store.metadata_path.read_text(encoding="utf-8")

            self.assertEqual(len(accounts), 1)
            self.assertNotIn("secret", metadata)
            self.assertNotIn("me@example.com", metadata)
            self.assertEqual(store.credentials_for(accounts[0]), ("me@example.com", "secret"))
            self.assertNotIn("email", json.loads(metadata)[0])

    def test_missing_label_does_not_put_email_in_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "accounts.csv"
            source.write_text("email,password\nme@example.com,secret\n", encoding="utf-8")
            store = AccountStore(root / "data", MemorySecrets())

            accounts = store.import_csv(source)

            self.assertEqual(accounts[0].label, "账号 1")
            self.assertNotIn("me@example.com", store.metadata_path.read_text(encoding="utf-8"))

    def test_legacy_keychain_payload_requires_reimport(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "accounts.csv"
            source.write_text("email,password\nme@example.com,secret\n", encoding="utf-8")
            secrets = MemorySecrets()
            store = AccountStore(root / "data", secrets)
            account = store.import_csv(source)[0]
            secrets.values[account.account_id] = "legacy-password"

            with self.assertRaisesRegex(RuntimeError, "重新导入 CSV"):
                store.credentials_for(account)

    def test_missing_password_rejects_whole_import(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "accounts.csv"
            source.write_text("email,password\nme@example.com,\n", encoding="utf-8")
            store = AccountStore(root / "data", MemorySecrets())

            with self.assertRaisesRegex(ValueError, "第 2 行"):
                store.import_csv(source)

            self.assertFalse(store.metadata_path.exists())
            self.assertEqual(store.secrets.values, {})

    def test_profile_directories_are_account_specific(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "accounts.csv"
            source.write_text(
                "email,password\na@example.com,one\nb@example.com,two\n", encoding="utf-8"
            )
            store = AccountStore(root / "data", MemorySecrets())
            accounts = store.import_csv(source)

            self.assertNotEqual(store.profile_dir(accounts[0]), store.profile_dir(accounts[1]))

    def test_imports_chinese_headers_and_numeric_labels(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "accounts.csv"
            source.write_text(
                "No,账号,密码\n1,first@example.com,one\n2,second@example.com,two\n",
                encoding="utf-8",
            )
            store = AccountStore(root / "data", MemorySecrets())

            accounts = store.import_csv(source)

            self.assertEqual([item.label for item in accounts], ["账号 1", "账号 2"])
            self.assertEqual(
                store.credentials_for(accounts[1]),
                ("second@example.com", "two"),
            )

    def test_reimport_uses_current_csv_order(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "accounts.csv"
            source.write_text(
                "No,账号,密码\n2,second@example.com,two\n",
                encoding="utf-8",
            )
            store = AccountStore(root / "data", MemorySecrets())
            store.import_csv(source)
            source.write_text(
                "No,账号,密码\n1,first@example.com,one\n2,second@example.com,two\n",
                encoding="utf-8",
            )

            store.import_csv(source)

            self.assertEqual(
                [item.label for item in store.load()],
                ["账号 1", "账号 2"],
            )


if __name__ == "__main__":
    unittest.main()
