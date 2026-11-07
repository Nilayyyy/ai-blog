"""Group items about the same story, score them, and drop anything already covered."""
from __future__ import annotations

import math
import re
from dataclasses import dataclass, field
from datetime import datetime
from urllib.parse import parse_qsl, urlencode, urlsplit

from .sources import Item

STOP = set(
    "the and for with from that this your you our new how why what are its into over about more using use "
    "can will has have was were been but not all any out one two".split()
)


def normalize_url(u: str) -> str:
    p = urlsplit(u.strip())
    host = p.netloc.lower()
    if host.startswith("www."):
        host = host[4:]
    q = [
        (k, v)
        for k, v in parse_qsl(p.query)
        if not k.lower().startswith(("utm_", "mc_")) and k.lower() not in {"ref", "source", "fbclid", "gclid", "cmpid"}
    ]
    path = p.path.rstrip("/")
    return f"{host}{path}" + (("?" + urlencode(q)) if q else "")


def tokens(title: str) -> set[str]:
    return {w for w in re.findall(r"[a-z0-9]+", title.lower()) if len(w) >= 3 and w not in STOP}


def similar_titles(a: str, b: str) -> bool:
    ta, tb = tokens(a), tokens(b)
    inter = ta & tb
    return len(inter) >= 3 and len(inter) / len(ta | tb) >= 0.5


def same_story(a: Item, b: Item) -> bool:
    return normalize_url(a.url) == normalize_url(b.url) or similar_titles(a.title, b.title)


@dataclass
class Story:
    rep: Item
    members: list = field(default_factory=list)
    score: float = 0.0

    @property
    def sources(self) -> list[str]:
        return sorted({m.source for m in self.members})

    @property
    def points(self) -> int:
        return sum(m.points for m in self.members if m.origin == "hn")

    @property
    def stars(self) -> int:
        return max([m.points for m in self.members if m.origin == "github"] or [0])

    @property
    def latest(self) -> datetime:
        return max(m.published for m in self.members)


def cluster(items: list[Item]) -> list[Story]:
    stories: list[Story] = []
    for it in sorted(items, key=lambda i: -i.weight):
        for s in stories:
            if any(same_story(it, m) for m in s.members):
                s.members.append(it)
                break
        else:
            stories.append(Story(rep=it, members=[it]))
    return stories


def score_story(s: Story, now: datetime, max_age_hours: float, keywords: dict) -> float:
    age_h = max(0.0, (now - s.latest).total_seconds() / 3600)
    recency = 20 * max(0.0, 1 - age_h / max_age_hours)
    hn = 8 * math.log10(1 + s.points)
    stars = 6 * math.log10(1 + s.stars)
    buzz = 12 * (len(s.sources) - 1)  # the same story on several sites is a strong signal
    official = 10 * max(m.weight for m in s.members)
    text = " ".join(f"{m.title} {m.summary}" for m in s.members).lower()
    kw = min(15.0, sum(w for k, w in (keywords or {}).items() if k in text))
    return recency + hn + stars + buzz + official + kw


def is_seen(s: Story, seen_urls: set[str], seen_titles: list[str]) -> bool:
    for m in s.members:
        if normalize_url(m.url) in seen_urls:
            return True
        if any(similar_titles(m.title, t) for t in seen_titles):
            return True
    return False


def rank_stories(items, now, max_age_hours, keywords, seen_urls=frozenset(), seen_titles=()) -> list[Story]:
    stories = [s for s in cluster(items) if not is_seen(s, set(seen_urls), list(seen_titles))]
    for s in stories:
        s.score = score_story(s, now, max_age_hours, keywords)
    return sorted(stories, key=lambda s: -s.score)
