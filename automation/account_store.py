"""Local account metadata and macOS Keychain-backed secret storage."""

from __future__ import annotations

import csv
import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Protocol


SERVICE_NAME = "Zaiko Lottery Assistant"
EMAIL_FIELDS = ("email", "account", "username")
PASSWORD_FIELDS = ("password", "pass")
LABEL_FIELDS = ("label", "name")


class SecretStore(Protocol):
    def set(self, account_id: str, password: str) -> None: ...

    def get(self, account_id: str) -> str | None: ...


class KeyringSecretStore:
    def set(self, account_id: str, password: str) -> None:
        import keyring

        keyring.set_password(SERVICE_NAME, account_id, password)

    def get(self, account_id: str) -> str | None:
        import keyring

        return keyring.get_password(SERVICE_NAME, account_id)


@dataclass(frozen=True)
class Account:
    account_id: str
    label: str


def _first(row: dict[str, str], names: tuple[str, ...]) -> str:
    normalized = {key.strip().lower(): (value or "").strip() for key, value in row.items()}
    return next((normalized[name] for name in names if normalized.get(name)), "")


def _account_id(email: str) -> str:
    return hashlib.sha256(email.strip().lower().encode("utf-8")).hexdigest()[:20]


class AccountStore:
    def __init__(self, data_dir: Path, secrets: SecretStore | None = None) -> None:
        self.data_dir = data_dir.expanduser()
        self.metadata_path = self.data_dir / "accounts.json"
        self.profiles_dir = self.data_dir / "profiles"
        self.secrets = secrets or KeyringSecretStore()

    def load(self) -> list[Account]:
        if not self.metadata_path.exists():
            return []
        data = json.loads(self.metadata_path.read_text(encoding="utf-8"))
        return [Account(account_id=item["account_id"], label=item["label"]) for item in data]

    def import_csv(self, csv_path: Path) -> list[Account]:
        with csv_path.open(newline="", encoding="utf-8-sig") as handle:
            reader = csv.DictReader(handle)
            if not reader.fieldnames:
                raise ValueError("CSV 必须包含表头")
            rows = list(reader)

        parsed_rows: list[tuple[Account, str]] = []
        for number, row in enumerate(rows, start=2):
            email = _first(row, EMAIL_FIELDS)
            password = _first(row, PASSWORD_FIELDS)
            if not email or not password:
                raise ValueError(f"CSV 第 {number} 行缺少 email/account 或 password")
            account_id = _account_id(email)
            account = Account(
                account_id=account_id,
                label=_first(row, LABEL_FIELDS) or f"账号 {number - 1}",
            )
            credentials = json.dumps(
                {"email": email, "password": password},
                ensure_ascii=False,
            )
            parsed_rows.append((account, credentials))

        accounts: dict[str, Account] = {item.account_id: item for item in self.load()}
        imported: list[Account] = []
        for account, credentials in parsed_rows:
            self.secrets.set(account.account_id, credentials)
            accounts[account.account_id] = account
            imported.append(account)

        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.metadata_path.write_text(
            json.dumps([asdict(item) for item in accounts.values()], ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return imported

    def credentials_for(self, account: Account) -> tuple[str, str]:
        payload = self.secrets.get(account.account_id)
        if payload is None:
            raise RuntimeError(f"Keychain 中没有 {account.label} 的凭据")
        try:
            data = json.loads(payload)
            email = data["email"]
            password = data["password"]
        except (json.JSONDecodeError, KeyError, TypeError):
            raise RuntimeError(f"{account.label} 使用旧凭据格式，请重新导入 CSV") from None
        if not isinstance(email, str) or not email or not isinstance(password, str) or not password:
            raise RuntimeError(f"Keychain 中的 {account.label} 凭据无效")
        return email, password

    def profile_dir(self, account: Account) -> Path:
        return self.profiles_dir / account.account_id
