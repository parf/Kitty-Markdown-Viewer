from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import tempfile
from urllib.parse import urlparse

import requests


URL_SCHEMES = {"http", "https"}


@dataclass(frozen=True)
class FetchedDocument:
    text: str
    source_url: str


def is_fetch_url(value: str) -> bool:
    return urlparse(value).scheme in URL_SCHEMES


def fetch_markdown(url: str, *, timeout: float) -> FetchedDocument:
    response = requests.get(url, timeout=timeout, allow_redirects=True)
    response.raise_for_status()
    response.encoding = response.encoding or "utf-8"
    return FetchedDocument(text=response.text, source_url=response.url)


def fetch_image_to_temp(url: str, *, timeout: float) -> Path:
    response = requests.get(url, timeout=timeout, allow_redirects=True)
    response.raise_for_status()
    suffix = Path(urlparse(response.url).path).suffix or ".img"
    handle = tempfile.NamedTemporaryFile(prefix="kitty-md-image-", suffix=suffix, delete=False)
    with handle:
        handle.write(response.content)
    return Path(handle.name)

