#!/usr/bin/env python3
"""Draft one blog post and save it as Markdown in src/content/posts.

Provider is picked with the PROVIDER env var: gemini (default), claude, or mock.
  gemini: needs GEMINI_API_KEY   (optional GEMINI_MODEL)
  claude: needs ANTHROPIC_API_KEY (optional CLAUDE_MODEL)
  mock:   no key, canned text, for testing the pipeline

Usage: python scripts/generate.py [--dry-run]
"""
import argparse
import datetime as dt
import os
import pathlib
import re
import sys
import time

import requests
import yaml

ROOT = pathlib.Path(__file__).resolve().parent.parent
TOPICS_FILE = ROOT / "scripts" / "topics.yaml"
POSTS_DIR = ROOT / "src" / "content" / "posts"
PROVIDER = os.getenv("PROVIDER", "gemini").lower()

SYSTEM = """You are drafting a technical blog post for a junior software developer who works on AI and cloud engineering.
Voice: first person where natural, plain and direct, like a human first draft. Short and medium sentences, concrete examples.
Avoid: hype, filler openers ("In today's fast-paced world"), buzzword stacking, listicle padding, emojis.
Hard rules:
- Never invent personal experiences, employers' internal details, benchmarks, statistics, quotes or version numbers.
- Where you are not sure a technical claim is current or correct, add an HTML comment right after it: <!-- VERIFY: what to check -->
- Only include code if you are confident it is correct and runnable.
- Do not use an H1 heading. Start with an intro paragraph, then ## sections."""


# ---------- providers ----------

def post_with_retry(url, headers, body, tries=4):
    for i in range(tries):
        r = requests.post(url, headers=headers, json=body, timeout=120)
        if r.status_code < 400:
            return r
        if r.status_code in (429, 500, 502, 503, 529) and i < tries - 1:
            time.sleep(5 * 2**i)
            continue
        raise RuntimeError(f"{PROVIDER} API error {r.status_code}: {r.text[:300]}")


def call_gemini(prompt, system):
    key = os.environ["GEMINI_API_KEY"]
    model = os.getenv("GEMINI_MODEL", "gemini-3.1-flash-lite")
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
    body = {
        "systemInstruction": {"parts": [{"text": system}]},
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.8},
    }
    data = post_with_retry(url, {"x-goog-api-key": key}, body).json()
    parts = data["candidates"][0]["content"]["parts"]
    return "".join(p.get("text", "") for p in parts).strip()


def call_claude(prompt, system):
    key = os.environ["ANTHROPIC_API_KEY"]
    model = os.getenv("CLAUDE_MODEL", "claude-sonnet-5-5")
    body = {
        "model": model,
        "max_tokens": 4096,
        "system": system,
        "messages": [{"role": "user", "content": prompt}],
    }
    headers = {"x-api-key": key, "anthropic-version": "2023-06-01"}
    data = post_with_retry("https://api.anthropic.com/v1/messages", headers, body).json()
    return "".join(b.get("text", "") for b in data["content"]).strip()


def call_mock(prompt, stage):
    if stage == "outline":
        return "DESCRIPTION: A mock description for pipeline testing.\nTAGS: test, mock\n- Intro\n- Main idea\n- Pitfalls"
    if stage == "topics":
        return "Mock topic one | A mock angle\nMock topic two | Another mock angle"
    return ("This is a mock intro paragraph used to test the pipeline.\n\n"
            "## Main idea\n\nSome mock body text. <!-- VERIFY: this is mock content -->\n\n"
            "## Pitfalls\n\nMore mock text.")


def generate(prompt, stage):
    if PROVIDER == "mock":
        return call_mock(prompt, stage)
    if PROVIDER == "gemini":
        return call_gemini(prompt, SYSTEM)
    if PROVIDER == "claude":
        return call_claude(prompt, SYSTEM)
    sys.exit(f"Unknown PROVIDER '{PROVIDER}' (use gemini, claude or mock)")


# ---------- topic queue ----------

def load_topics():
    return yaml.safe_load(TOPICS_FILE.read_text(encoding="utf-8"))


def save_topics(data):
    TOPICS_FILE.write_text(
        yaml.safe_dump(data, sort_keys=False, allow_unicode=True, width=100), encoding="utf-8"
    )


def existing_titles():
    titles = []
    for f in POSTS_DIR.glob("*.md"):
        m = re.search(r'^title:\s*"?(.*?)"?\s*$', f.read_text(encoding="utf-8"), re.M)
        if m:
            titles.append(m.group(1))
    return titles


def refill_topics(data):
    prompt = (
        "Suggest 8 new blog post topics, one per line, formatted as: Title | one-sentence angle.\n"
        "Themes: " + "; ".join(data["themes"]) + "\n"
        "Already covered or queued (do not repeat): "
        + "; ".join(existing_titles() + [t["title"] for t in data["topics"]])
        + "\nPrefer explanatory topics that do not need first-hand benchmarks. Output only the lines."
    )
    for line in generate(prompt, "topics").splitlines():
        if "|" in line:
            title, angle = (s.strip(" -*\t\"") for s in line.split("|", 1))
            if title:
                data["topics"].append({"title": title, "angle": angle, "status": "pending"})


def next_topic(data):
    for t in data["topics"]:
        if t.get("status") == "pending":
            return t
    refill_topics(data)
    for t in data["topics"]:
        if t.get("status") == "pending":
            return t
    sys.exit("No pending topics and refill produced none.")


# ---------- writing ----------

def parse_outline(text):
    desc = re.search(r"^DESCRIPTION:\s*(.+)$", text, re.M)
    tags = re.search(r"^TAGS:\s*(.+)$", text, re.M)
    outline = "\n".join(l for l in text.splitlines() if not re.match(r"^(DESCRIPTION|TAGS):", l)).strip()
    tag_list = [t.strip().lower() for t in tags.group(1).split(",")][:5] if tags else []
    return (desc.group(1).strip() if desc else ""), tag_list, outline


def strip_fences(text):
    text = text.strip()
    m = re.match(r"^```(?:markdown|md)?\n(.*)\n```$", text, re.S)
    return m.group(1).strip() if m else text


def slugify(s):
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")[:70]


def yaml_str(s):
    return '"' + s.replace("\\", "\\\\").replace('"', '\\"') + '"'


def write_post(topic):
    title, angle = topic["title"], topic.get("angle", "")

    outline_prompt = (
        f"Plan a blog post titled: {title}\nAngle: {angle}\n"
        "Reply in exactly this format:\n"
        "DESCRIPTION: one sentence (max 160 chars) for search results\n"
        "TAGS: three to five lowercase tags, comma separated\n"
        "then a bullet outline of 4-6 sections."
    )
    description, tags, outline = parse_outline(generate(outline_prompt, "outline"))

    draft_prompt = (
        f"Write the full post (800-1200 words) in Markdown.\nTitle: {title}\nAngle: {angle}\nOutline:\n{outline}\n"
        "Do not include a section about the author's personal take; that is added separately. Output only the post body."
    )
    draft = strip_fences(generate(draft_prompt, "draft"))

    edit_prompt = (
        "Edit this draft. Cut filler and repetition, fix anything technically doubtful or mark it with "
        "<!-- VERIFY: ... --> (keep existing VERIFY markers), make the tone plain and human, keep it under 1200 words. "
        "Return only the final Markdown body.\n\n" + draft
    )
    body = strip_fences(generate(edit_prompt, "edit"))

    body += (
        "\n\n## My take\n\n"
        "TODO(nilay): add 2-4 sentences from your own experience or opinion, then delete this line.\n"
    )

    today = dt.date.today().isoformat()
    front = (
        "---\n"
        f"title: {yaml_str(title)}\n"
        f"description: {yaml_str(description or title)}\n"
        f"pubDate: {today}\n"
        f"tags: [{', '.join(tags)}]\n"
        "canonical:\n"
        "---\n\n"
    )
    path = POSTS_DIR / f"{today}-{slugify(title)}.md"
    return path, front + body + "\n"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true", help="print the post, don't write files")
    args = ap.parse_args()

    POSTS_DIR.mkdir(parents=True, exist_ok=True)
    data = load_topics()
    topic = next_topic(data)
    path, content = write_post(topic)

    if args.dry_run:
        print(f"[dry-run] would write {path.relative_to(ROOT)}\n")
        print(content)
        return

    path.write_text(content, encoding="utf-8")
    topic["status"] = "done"
    save_topics(data)
    print(f"Wrote {path.relative_to(ROOT)}")

    out = os.getenv("GITHUB_OUTPUT")
    if out:
        with open(out, "a", encoding="utf-8") as fh:
            fh.write(f"title={topic['title']}\npath={path.relative_to(ROOT)}\n")


if __name__ == "__main__":
    main()
