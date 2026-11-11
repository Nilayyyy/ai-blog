#!/usr/bin/env python3
"""AI Dev Radar generator: find today's story, write a STAR post with a diagram, save it as Markdown.

  python scripts/generate.py                  # auto: Thursday (IST) = tips, other days = news
  python scripts/generate.py --mode news --dry-run
  python scripts/generate.py --check-sources  # which feeds are reachable from this machine
  python scripts/generate.py --check-model    # one tiny call through the model chain, to test the login/token

Environment: PROVIDER (comma-separated chain, default "claude-code,gemini"; also claude-api, mock; see
radar/llm.py), CLAUDE_CODE_OAUTH_TOKEN / GEMINI_API_KEY / ANTHROPIC_API_KEY, GITHUB_TOKEN (optional, for the
GitHub search), OPEN_PRS_FILE (JSON from `gh pr list`, used to skip stories already in an open draft),
PR_BODY_FILE (where to write the PR description), RADAR_OFFLINE=1 (use test fixtures, no network).
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from radar import article, llm, rank, sources, writer  # noqa: E402

POSTS_DIR = ROOT / "src" / "content" / "posts"
IST = timezone(timedelta(hours=5, minutes=30))  # India has no daylight saving


def resolve_mode(arg: str | None, now_utc: datetime) -> str:
    mode = (arg or os.getenv("MODE") or "auto").lower()
    if mode in ("news", "tips"):
        return mode
    return "tips" if now_utc.astimezone(IST).weekday() == 3 else "news"  # Thursday


def load_seen(posts_dir: Path, open_prs_file: str | None):
    """URLs and titles we must not write about again: published posts plus open draft PRs."""
    urls, titles = set(), []
    for f in sorted(posts_dir.glob("*.md")):
        fm = writer.read_front_matter(f.read_text(encoding="utf-8"))
        if fm.get("title"):
            titles.append(str(fm["title"]))
        for u in fm.get("sources") or []:
            urls.add(rank.normalize_url(str(u)))
    if open_prs_file and Path(open_prs_file).exists():
        try:
            prs = json.loads(Path(open_prs_file).read_text(encoding="utf-8") or "[]")
        except json.JSONDecodeError:
            prs = []
        for pr in prs:
            if str(pr.get("headRefName", "")).startswith("draft/"):
                titles.append(re.sub(r"^Draft:\s*", "", str(pr.get("title", ""))))
                for u in re.findall(r"https?://[^\s)>\]]+", str(pr.get("body", ""))):
                    urls.add(rank.normalize_url(u))
    return urls, titles


def write_outputs(**kv):
    out = os.getenv("GITHUB_OUTPUT")
    if out:
        with open(out, "a", encoding="utf-8") as fh:
            for k, v in kv.items():
                fh.write(f"{k}={v}\n")


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):  # Windows consoles default to a legacy encoding
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")

    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--mode", choices=["auto", "news", "tips"], default=None)
    ap.add_argument("--dry-run", action="store_true", help="print the post, write nothing")
    ap.add_argument("--check-sources", action="store_true", help="test every source and exit")
    ap.add_argument("--check-model", action="store_true", help="make one tiny model call through the provider chain and exit")
    ap.add_argument("--offline", action="store_true", help="use bundled test fixtures instead of the network")
    args = ap.parse_args()

    if args.check_model:
        print(f"Provider chain: {' -> '.join(llm.providers())}")
        reply = llm.complete("You are a health check.", "Reply with the single word OK.", stage="check", temperature=0)
        print(f"Answered by {llm.used_summary()}: {reply[:80]}")
        return 0

    now = datetime.now(timezone.utc)
    cfg = yaml.safe_load((ROOT / "scripts" / "radar.yaml").read_text(encoding="utf-8"))
    offline = args.offline or os.getenv("RADAR_OFFLINE") == "1"
    if offline:
        os.environ["RADAR_OFFLINE"] = "1"

    if args.check_sources:
        for name in ("news", "tips"):
            sec = cfg[name]
            _, report = sources.gather(sec, now, sec["max_age_hours"])
            print(f"\n[{name}]\n{sources.format_report(report)}")
        return 0

    mode = resolve_mode(args.mode, now)
    section = cfg[mode]
    fixture = ROOT / "scripts" / "tests" / "fixtures" / f"candidates_{mode}.json" if offline else None
    print(f"Mode: {mode} ({now.astimezone(IST):%A %d %b %Y}, IST)")

    seen_urls, seen_titles = load_seen(POSTS_DIR, os.getenv("OPEN_PRS_FILE"))
    recent = seen_titles[-8:]

    hours = section["max_age_hours"]
    stories = []
    for window in (hours, 168 if mode == "news" else 720):
        items, report = sources.gather(section, now, window, fixture)
        print(sources.format_report(report))
        if not any(r[1] for r in report):
            # Silence would look like a quiet news day; a red run tells you something is wrong.
            print("Every source failed, so nothing could be checked. Check the network or run --check-sources.", file=sys.stderr)
            write_outputs(skipped="true", path="")
            return 1
        stories = rank.rank_stories(items, now, window, cfg.get("keywords", {}), seen_urls, seen_titles)[:40]
        print(f"{len(items)} fresh items in the last {window}h, {len(stories)} distinct unseen stories")
        if stories:
            break
        print("Nothing new enough; widening the window.")
    if not stories:
        print("No new stories found. Skipping today rather than repeating something.")
        write_outputs(skipped="true", path="")
        return 0

    picks = writer.select(mode, stories, recent, now)

    if mode == "news":
        chosen = None
        for story, angle in picks:
            srcs = article.collect_sources(story, want=2, per_chars=6500)
            if srcs:
                chosen = (story.rep.title, angle, srcs)
                break
        if not chosen:
            print("Could not read the article text for any pick. Nothing written.", file=sys.stderr)
            write_outputs(skipped="true", path="")
            return 1
        headline, angle, srcs = chosen
    else:
        srcs, angles = [], []
        for story, angle in picks:
            got = article.collect_sources(story, want=1, per_chars=4000)
            if got:
                srcs += got
                angles.append(angle)
        if not srcs:
            print("Could not read any tip sources. Nothing written.", file=sys.stderr)
            write_outputs(skipped="true", path="")
            return 1
        headline, angle = "practical tricks for developers and AI engineers", " ".join(a for a in angles if a)

    today_iso = now.astimezone(IST).strftime("%Y-%m-%d")
    print(f"Writing from {len(srcs)} source(s): {', '.join(s['publisher'] for s in srcs)}")
    post = writer.write_post(mode, headline, angle, srcs, recent, today_iso)
    diagram = writer.make_diagram(mode, post)
    title, content = writer.finalize(post, mode, today_iso=today_iso, srcs=srcs, diagram=diagram)

    path = POSTS_DIR / f"{today_iso}-{writer.slugify(title)}.md"
    n = 2
    while path.exists() and not args.dry_run:
        path = POSTS_DIR / f"{today_iso}-{writer.slugify(title)}-{n}.md"
        n += 1

    if args.dry_run:
        print(f"\n[dry-run] would write {path.relative_to(ROOT)}\n")
        print(content)
        return 0

    POSTS_DIR.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    body_file = Path(os.getenv("PR_BODY_FILE") or ROOT / ".draft" / "pr_body.md")
    body_file.parent.mkdir(parents=True, exist_ok=True)
    body_file.write_text(writer.pr_body(mode, srcs, model=llm.used_summary()), encoding="utf-8")
    print(f"Wrote {path.relative_to(ROOT)} (model: {llm.used_summary()})")
    write_outputs(title=title, path=path.relative_to(ROOT).as_posix(), mode=mode, skipped="false")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except llm.LLMError as e:
        print(f"Model error: {e}", file=sys.stderr)
        sys.exit(2)
