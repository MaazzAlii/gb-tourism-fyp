import html
from urllib.parse import urlparse


def sanitize_text(value: str | None) -> str:
    if not value:
        return ""
    cleaned = html.unescape(value).replace("\n", " ").strip()
    return " ".join(cleaned.split())


def is_safe_url(url: str | None) -> bool:
    if not url:
        return False
    parsed = urlparse(url)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)

