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
            self.assertEqual(store.password_for(accounts[0]), "secret")
            self.assertEqual(json.loads(metadata)[0]["email"], "me@example.com")

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


if __name__ == "__main__":
    unittest.main()
