"""Locate the two explicitly supported lottery frames on a ZAIKO event page."""

from __future__ import annotations

import argparse
from urllib.parse import urljoin, urlparse


ALLOWED_HOST = "akb48.zaiko.io"
SUPPORTED_FRAMES = (
    "映像倉庫会員枠",
    "柱の会 会員枠",
)


def validate_event_url(value: str) -> str:
    parsed = urlparse(value)
    path_parts = [part for part in parsed.path.split("/") if part]
    is_event_path = (
        len(path_parts) == 2 and path_parts[0] == "e"
    ) or (
        len(path_parts) == 3 and path_parts[0] in {"ja", "en"} and path_parts[1] == "e"
    )
    if (
        parsed.scheme != "https"
        or parsed.hostname != ALLOWED_HOST
        or parsed.username is not None
        or parsed.password is not None
        or not is_event_path
    ):
        raise argparse.ArgumentTypeError(
            f"event URL must use https://{ALLOWED_HOST}/ja/e/..."
        )
    return value


def validate_frame_name(frame_name: str) -> str:
    if frame_name not in SUPPORTED_FRAMES:
        raise ValueError("只支持映像倉庫会員枠和柱の会 会員枠")
    return frame_name


def find_frame_application_url(page, frame_name: str, timeout_ms: int) -> str:
    """Return the exact /buy/ link belonging to one supported frame."""
    frame_name = validate_frame_name(frame_name)
    label = page.get_by_text(frame_name, exact=True).first
    label.wait_for(state="visible", timeout=timeout_ms)
    card = label.locator(
        "xpath=ancestor::*[.//a[normalize-space()='抽選応募']][1]"
    )
    link = card.get_by_role("link", name="抽選応募", exact=True).first
    link.wait_for(state="visible", timeout=timeout_ms)
    href = link.get_attribute("href")
    if not href:
        raise RuntimeError(f"{frame_name} 没有可用的抽选入口")

    target = urljoin(page.url, href)
    parsed = urlparse(target)
    if (
        parsed.scheme != "https"
        or parsed.hostname != ALLOWED_HOST
        or parsed.username is not None
        or parsed.password is not None
        or not parsed.path.startswith("/buy/")
    ):
        raise RuntimeError(f"{frame_name} 的抽选入口不属于允许的 ZAIKO /buy/ 页面")
    return target
