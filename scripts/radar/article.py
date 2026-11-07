"""Fetch and clean the text of an article so the model writes from the source, not from memory.

Fetching is guarded: only http(s), and never to private, loopback or link-local addresses
(including after redirects), so a hostile feed item can't point the runner at internal services.
"""
from __future__ import annotations

import ipaddress
import os
import re
import socket
import sys
from pathlib import Path
from urllib.parse import urljoin, urlsplit

import requests

from .rank import normalize_url
from .sources import UA

MIN_CHARS = 500
FIXTURE_ARTICLE = Path(__file__).resolve().parent.parent / "tests" / "fixtures" / "article.txt"


def _host_is_public(host: str) -> bool:
    try:
        infos = socket.getaddrinfo(host, None)
    except socket.gaierror as e:
        raise ValueError(f"could not resolve host {host}") from e
    for info in infos:
        ip = ipaddress.ip_address(info[4][0].split("%")[0])
        if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved or ip.is_multicast or ip.is_unspecified:
            return False
    return True


def safe_get(url: str, timeout: int = 20, max_bytes: int = 2_000_000, max_hops: int = 4):
    """GET with manual redirect handling. Returns (final_url, body bytes)."""
    for _ in range(max_hops + 1):
        parts = urlsplit(url)
        if parts.scheme not in ("http", "https") or not parts.hostname:
            raise ValueError("blocked url scheme")
        if not _host_is_public(parts.hostname):
            raise ValueError("blocked non-public host")
        r = requests.get(
            url,
            headers={"User-Agent": UA, "Accept": "text/html,application/xhtml+xml;q=0.9,*/*;q=0.5"},
            timeout=timeout,
            allow_redirects=False,
            stream=True,
        )
        if 300 <= r.status_code < 400 and r.headers.get("Location"):
            url = urljoin(url, r.headers["Location"])
            r.close()
            continue
        r.raise_for_status()
        ctype = r.headers.get("Content-Type", "")
        if ctype and not re.search(r"html|xml|text", ctype, re.I):
            r.close()
            raise ValueError(f"unsupported content type {ctype}")
        body = b""
        for chunk in r.iter_content(65536):
            body += chunk
            if len(body) >= max_bytes:
                break
        r.close()
        return url, body
    raise ValueError("too many redirects")


def _fallback_text(html_text: str) -> str:
    t = re.sub(r"(?is)<(script|style|nav|header|footer|aside|form|noscript|svg)\b.*?</\1>", " ", html_text)
    t = re.sub(r"(?s)<!--.*?-->", " ", t)
    t = re.sub(r"(?i)</(p|div|li|h[1-6]|br|tr)>", "\n", t)
    t = re.sub(r"<[^>]+>", " ", t)
    import html as _html

    t = _html.unescape(t)
    lines = [re.sub(r"[ \t]+", " ", ln).strip() for ln in t.splitlines()]
    return "\n".join(ln for ln in lines if len(ln) > 40)


def extract_text(body, url: str = "") -> tuple[str, str]:
    """Return (title, main text) from an HTML document."""
    text, title = "", ""
    try:
        import trafilatura

        text = trafilatura.extract(body, include_comments=False, include_tables=False, favor_recall=True, url=url or None) or ""
        meta = trafilatura.extract_metadata(body)
        title = (meta.title if meta and meta.title else "") or ""
    except Exception:  # noqa: BLE001 - fall back to the crude extractor
        text = ""
    if len(text) < MIN_CHARS:
        s = body.decode("utf-8", "replace") if isinstance(body, bytes) else body
        text = _fallback_text(s)
        m = re.search(r"(?is)<title[^>]*>(.*?)</title>", s)
        title = title or (re.sub(r"\s+", " ", m.group(1)).strip() if m else "")
    return title, text


def cut(text: str, limit: int) -> str:
    text = re.sub(r"\n{3,}", "\n\n", text).strip()
    if len(text) <= limit:
        return text
    chunk = text[:limit]
    end = max(chunk.rfind(". "), chunk.rfind("\n"))
    return (chunk[: end + 1] if end > limit * 0.6 else chunk).strip()


def fetch_article(url: str) -> tuple[str, str]:
    if os.getenv("RADAR_OFFLINE") == "1":
        return "Fixture article", FIXTURE_ARTICLE.read_text(encoding="utf-8")
    final_url, body = safe_get(url)
    return extract_text(body, final_url)


def collect_sources(story, want: int = 2, per_chars: int = 6500) -> list[dict]:
    """Read up to `want` distinct articles about a story, most trusted source first."""
    got, seen = [], set()
    for m in sorted(story.members, key=lambda i: -i.weight):
        if len(got) >= want:
            break
        key = normalize_url(m.url)
        if key in seen or "news.ycombinator.com" in m.url:
            continue
        seen.add(key)
        try:
            title, text = fetch_article(m.url)
        except Exception as e:  # noqa: BLE001
            print(f"  could not read {m.url}: {type(e).__name__}", file=sys.stderr)
            title, text = m.title, ""
        if len(text) < MIN_CHARS and len(m.summary) >= 200:
            text = m.summary  # the feed's own summary is better than nothing
        if len(text) >= MIN_CHARS or (m.origin == "github" and len(text) >= 100):
            got.append({"title": title or m.title, "url": m.url, "publisher": m.source, "text": cut(text, per_chars)})
    return got
