"""Collect fresh stories from RSS/Atom feeds, Hacker News and GitHub. Every source fails soft."""
from __future__ import annotations

import html
import json
import re
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path

import feedparser
import requests

# A generic client name. Don't put personal contact details here.
UA = "ai-dev-radar/2.0 (personal blog draft generator)"
TIMEOUT = 20

AI_RE = re.compile(
    r"\b(ai|a\.i\.|llms?|gpt\S*|claude|gemini|gemma|llama|mistral|openai|anthropic|deepmind|agents?|agentic|"
    r"models?|transformers?|neural|machine learning|copilot|chatbots?|rag|mcp|diffusion|inference|fine-?tun\w*|"
    r"embeddings?|generative|genai|deepseek|qwen|grok|perplexity|hugging ?face|nvidia|cuda|gpus?|tpus?|"
    r"reasoning|multimodal|prompt\w*|vector)\b",
    re.I,
)


@dataclass
class Item:
    title: str
    url: str
    source: str
    published: datetime | None
    summary: str = ""
    points: int = 0          # HN points, or GitHub stars for origin == "github"
    weight: float = 0.5      # trust in this source as a primary
    origin: str = "feed"     # feed | hn | github
    ai_only: bool = False    # source is AI-specific, so skip the keyword filter
    hn_url: str = ""


def clean_text(s, limit=500):
    s = re.sub(r"<[^>]+>", " ", s or "")
    s = html.unescape(s)
    return re.sub(r"\s+", " ", s).strip()[:limit]


# ---------------------------------------------------------------- individual sources

def parse_feed(content: bytes, src: dict, limit: int = 40) -> list[Item]:
    d = feedparser.parse(content)
    items = []
    for e in d.entries[:limit]:
        title = clean_text(e.get("title"), 200)
        link = (e.get("link") or "").strip()
        if not title or not link.startswith("http"):
            continue
        ts = e.get("published_parsed") or e.get("updated_parsed")
        published = datetime(*ts[:6], tzinfo=timezone.utc) if ts else None
        summary = clean_text(e.get("summary") or e.get("description"), 600)
        items.append(
            Item(
                title=title,
                url=link,
                source=src["name"],
                published=published,
                summary=summary,
                weight=float(src.get("weight", 0.5)),
                origin="feed",
                ai_only=bool(src.get("ai", False)),
            )
        )
    return items


def fetch_feed(src: dict) -> list[Item]:
    headers = {
        "User-Agent": UA,
        "Accept": "application/rss+xml, application/atom+xml, application/xml;q=0.9, */*;q=0.8",
    }
    r = requests.get(src["url"], headers=headers, timeout=TIMEOUT)
    r.raise_for_status()
    return parse_feed(r.content, src)


def fetch_hn_query(query: str, cfg: dict, hours: int, now: datetime) -> list[Item]:
    cutoff = int((now - timedelta(hours=hours)).timestamp())
    params = {
        "query": query,
        "tags": "story",
        "numericFilters": f"created_at_i>{cutoff},points>={int(cfg.get('min_points', 40))}",
        "hitsPerPage": 25,
    }
    r = requests.get("https://hn.algolia.com/api/v1/search", params=params, headers={"User-Agent": UA}, timeout=TIMEOUT)
    r.raise_for_status()
    out = []
    for h in r.json().get("hits", []):
        title = clean_text(h.get("title"), 200)
        if not title or not h.get("created_at_i"):
            continue
        hn_url = f"https://news.ycombinator.com/item?id={h.get('objectID')}"
        out.append(
            Item(
                title=title,
                url=h.get("url") or hn_url,
                source="Hacker News",
                published=datetime.fromtimestamp(h["created_at_i"], tz=timezone.utc),
                points=int(h.get("points") or 0),
                weight=float(cfg.get("weight", 0.6)),
                origin="hn",
                hn_url=hn_url,
            )
        )
    return out


def fetch_github_topic(topic: str, cfg: dict, now: datetime) -> list[Item]:
    import os

    since = (now - timedelta(days=int(cfg.get("window_days", 10)))).strftime("%Y-%m-%d")
    headers = {"Accept": "application/vnd.github+json", "User-Agent": UA}
    token = os.getenv("GITHUB_TOKEN")
    if token:  # only ever sent to api.github.com
        headers["Authorization"] = f"Bearer {token}"
    params = {
        "q": f"topic:{topic} created:>{since} stars:>={int(cfg.get('min_stars', 150))}",
        "sort": "stars",
        "order": "desc",
        "per_page": 10,
    }
    r = requests.get("https://api.github.com/search/repositories", params=params, headers=headers, timeout=TIMEOUT)
    r.raise_for_status()
    out = []
    for repo in r.json().get("items", []):
        desc = clean_text(repo.get("description"), 300)
        created = datetime.fromisoformat(repo["created_at"].replace("Z", "+00:00"))
        out.append(
            Item(
                title=f"{repo['full_name']}: {desc}" if desc else repo["full_name"],
                url=repo["html_url"],
                source="GitHub",
                published=created,
                summary=desc,
                points=int(repo.get("stargazers_count") or 0),
                weight=float(cfg.get("weight", 0.5)),
                origin="github",
                ai_only=True,
            )
        )
    return out


def load_fixture(path, now: datetime) -> list[Item]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return [
        Item(
            title=d["title"],
            url=d["url"],
            source=d["source"],
            published=now - timedelta(hours=d.get("hours_ago", 5)),
            summary=d.get("summary", ""),
            points=d.get("points", 0),
            weight=d.get("weight", 0.5),
            origin=d.get("origin", "feed"),
            ai_only=True,
        )
        for d in data
    ]


# ---------------------------------------------------------------- gathering

def _build_tasks(section: dict, hours: int, now: datetime):
    tasks = []
    for src in section.get("feeds", []):
        tasks.append((src["name"], lambda s=src: fetch_feed(s)))
    hn = section.get("hn")
    if hn:
        for q in hn.get("queries", []):
            tasks.append((f"HN: {q}", lambda q=q: fetch_hn_query(q, hn, hours, now)))
    gh = section.get("github")
    if gh:
        for t in gh.get("topics", []):
            tasks.append((f"GitHub: {t}", lambda t=t: fetch_github_topic(t, gh, now)))
    return tasks


def filter_items(items, section: dict, now: datetime, hours: int):
    require_ai = section.get("require_ai", True)
    out = []
    for it in items:
        if not it.published:
            continue
        age = now - it.published
        if age > timedelta(hours=hours) or age < timedelta(hours=-6):
            continue
        if require_ai and not it.ai_only and not AI_RE.search(f"{it.title} {it.summary}"):
            continue
        out.append(it)
    return out


def gather(section: dict, now: datetime, hours: int, fixture=None):
    """Return (fresh items, report rows). A report row is (source, ok, count, error)."""
    report, items = [], []
    if fixture:
        items = load_fixture(fixture, now)
        report.append(("fixture", True, len(items), ""))
    else:
        tasks = _build_tasks(section, hours, now)
        with ThreadPoolExecutor(max_workers=8) as pool:
            futures = [(name, pool.submit(fn)) for name, fn in tasks]
            for name, fut in futures:
                try:
                    got = fut.result(timeout=90)
                    items.extend(got)
                    report.append((name, True, len(got), ""))
                except Exception as e:  # noqa: BLE001 - one bad source must not stop the run
                    report.append((name, False, 0, f"{type(e).__name__}: {str(e)[:90]}"))
    return filter_items(items, section, now, hours), report


def format_report(report) -> str:
    ok = sum(1 for r in report if r[1])
    lines = [f"Sources: {ok}/{len(report)} reachable"]
    for name, good, n, err in report:
        lines.append(f"  {'ok  ' if good else 'FAIL'} {name:<28} {n:>3} items {err}")
    return "\n".join(lines)
