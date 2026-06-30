from __future__ import annotations

import hashlib
import re
from datetime import datetime
from urllib.parse import urlparse


def safe_slug(text: str, fallback: str = "artifact") -> str:
    text = re.sub(r"https?://", "", text.strip(), flags=re.I)
    text = re.sub(r"[^A-Za-z0-9\u4e00-\u9fff._-]+", "-", text)
    return text.strip("-._")[:80] or fallback


def url_slug(url: str, title: str = "") -> str:
    parsed = urlparse(url)
    base = title.strip() or parsed.netloc + parsed.path
    digest = hashlib.sha1(url.encode("utf-8")).hexdigest()[:10]
    return f"{safe_slug(base, 'web-read')}-{digest}"


def bundle_slug(name: str, urls: list[str]) -> str:
    digest = hashlib.sha1("\n".join(urls).encode("utf-8")).hexdigest()[:10]
    return f"{safe_slug(name, 'source-bundle')}-{digest}"


def make_run_id(moment: datetime) -> str:
    return moment.strftime("%Y%m%dT%H%M%SZ")
