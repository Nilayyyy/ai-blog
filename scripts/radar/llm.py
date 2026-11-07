"""One function, complete(), in front of Gemini, Claude or a mock.

PROVIDER=gemini (default) | claude | mock
  gemini: GEMINI_API_KEY, optional GEMINI_MODEL and GEMINI_FALLBACK_MODELS (comma separated)
  claude: ANTHROPIC_API_KEY, optional CLAUDE_MODEL

Gemini calls retry on timeouts and 429/5xx, then fall back to the next model in the list.
"""
from __future__ import annotations

import json
import os
import re
import sys
import time

import requests

DEFAULT_GEMINI = "gemini-3.1-flash-lite"
GEMINI_FALLBACKS = ["gemini-3.5-flash-lite", "gemini-flash-lite-latest"]
DEFAULT_CLAUDE = "claude-sonnet-5-5"
RETRYABLE = {429, 500, 502, 503, 504, 529}


class LLMError(RuntimeError):
    def __init__(self, message, status=None):
        super().__init__(message)
        self.status = status


def provider() -> str:
    # `or` matters: an unset GitHub Actions variable arrives as an empty string.
    return (os.getenv("PROVIDER") or "gemini").strip().lower()


def _base_sleep() -> float:
    raw = os.getenv("RETRY_BASE_SECONDS")
    return float(raw) if raw not in (None, "") else 5.0


def _post(url, headers, body, tries=4, timeout=240):
    last = None
    for i in range(tries):
        try:
            r = requests.post(url, headers=headers, json=body, timeout=timeout)
        except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
            last = LLMError(f"network error: {type(e).__name__}")
        else:
            if r.status_code < 400:
                return r
            last = LLMError(f"HTTP {r.status_code}: {r.text[:300]}", status=r.status_code)
            if r.status_code not in RETRYABLE:
                raise last
        if i < tries - 1:
            time.sleep(_base_sleep() * 3**i)
    raise last


def _gemini_call(model, system, prompt, json_mode, temperature):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
    gen = {"temperature": temperature, "maxOutputTokens": 8192}
    if json_mode:
        gen["responseMimeType"] = "application/json"
    body = {
        "systemInstruction": {"parts": [{"text": system}]},
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        "generationConfig": gen,
    }
    data = _post(url, {"x-goog-api-key": os.environ["GEMINI_API_KEY"]}, body).json()
    cands = data.get("candidates") or []
    if not cands:
        raise LLMError(f"no candidates returned ({str(data.get('promptFeedback'))[:160]})")
    parts = cands[0].get("content", {}).get("parts", [])
    text = "".join(p.get("text", "") for p in parts if not p.get("thought")).strip()
    if not text:
        raise LLMError(f"empty response (finishReason={cands[0].get('finishReason')})")
    return text


def _gemini(system, prompt, json_mode, temperature):
    if not os.getenv("GEMINI_API_KEY"):
        raise LLMError("GEMINI_API_KEY is not set")
    first = os.getenv("GEMINI_MODEL") or DEFAULT_GEMINI
    extra = os.getenv("GEMINI_FALLBACK_MODELS") or ",".join(GEMINI_FALLBACKS)
    models = [first] + [m.strip() for m in extra.split(",") if m.strip() and m.strip() != first]
    last = None
    for model in models:
        try:
            return _gemini_call(model, system, prompt, json_mode, temperature)
        except LLMError as e:
            last = e
            if e.status in (None, 404, 429, 500, 502, 503, 504, 529):
                print(f"  model {model} unavailable ({e}); trying the next one", file=sys.stderr)
                continue
            raise
    raise last


def _claude(system, prompt, json_mode, temperature):
    if not os.getenv("ANTHROPIC_API_KEY"):
        raise LLMError("ANTHROPIC_API_KEY is not set")
    model = os.getenv("CLAUDE_MODEL") or DEFAULT_CLAUDE
    if json_mode:
        system += "\nReply with a single JSON object and nothing else."
    body = {
        "model": model,
        "max_tokens": 8192,
        "temperature": min(temperature, 1.0),
        "system": system,
        "messages": [{"role": "user", "content": prompt}],
    }
    headers = {"x-api-key": os.environ["ANTHROPIC_API_KEY"], "anthropic-version": "2023-06-01"}
    data = _post("https://api.anthropic.com/v1/messages", headers, body).json()
    text = "".join(b.get("text", "") for b in data.get("content", [])).strip()
    if not text:
        raise LLMError("empty response from Claude")
    return text


def complete(system: str, prompt: str, *, stage: str, json_mode: bool = False, temperature: float = 0.8) -> str:
    p = provider()
    if p == "mock":
        return _mock(stage)
    if p == "gemini":
        text = _gemini(system, prompt, json_mode, temperature)
    elif p == "claude":
        text = _claude(system, prompt, json_mode, temperature)
    else:
        raise LLMError(f"Unknown PROVIDER '{p}' (use gemini, claude or mock)")
    gap = os.getenv("CALL_GAP_SECONDS")
    time.sleep(float(gap) if gap not in (None, "") else 2.0)  # stay polite to free-tier rate limits
    return text


def extract_json(text: str) -> dict:
    t = re.sub(r"^```(?:json)?\s*|\s*```$", "", text.strip())
    start, end = t.find("{"), t.rfind("}")
    if start < 0 or end <= start:
        raise ValueError("no JSON object found")
    return json.loads(t[start : end + 1])


def complete_json(system: str, prompt: str, *, stage: str) -> dict:
    last = None
    for attempt in range(2):
        extra = "" if attempt == 0 else "\n\nReturn valid JSON only, with no commentary."
        text = complete(system, prompt + extra, stage=stage, json_mode=True, temperature=0.4)
        try:
            return extract_json(text)
        except ValueError as e:  # includes json.JSONDecodeError
            last = e
    raise LLMError(f"model did not return valid JSON for '{stage}': {last}")


# ---------------------------------------------------------------- mock (no key, for testing)

_MOCK_NEWS = """TITLE: Atlas reviews your pull request before your teammates wake up
TLDR: ExampleLab's Atlas is a code-review agent that reads the whole repository and runs the tests before it comments.
TAGS: agents, code-review, developer-tools
---
Atlas does something most review bots skip: it runs your test suite before it says a word. That one design choice changes what its comments are worth.

## Situation
Pull requests pile up faster than people can review them. Automated reviewers exist, but many only look at the diff, so their comments read like a linter with opinions. Reviewers learn to ignore them.

## Task
ExampleLab wanted a reviewer that behaves more like a colleague: one that knows the codebase, checks its own suggestions, and only speaks up when it is fairly sure.

## Action
Atlas works in four moves:

- It indexes the repository so it can see callers, tests and conventions, not just changed lines.
- It runs the existing test suite against the proposed change.
- It drafts comments, then tries each suggested fix in a sandbox to see whether it passes.
- It posts only the comments whose fixes survived that check.

The interesting part is the third step. A suggestion that breaks the build never reaches a human. That is also why the design is quiet by default: if Atlas cannot make a fix pass, it says nothing, and silence from a reviewer is easier to live with than a wrong comment.

It runs inside the customer's own CI, so the code never has to leave the build environment. That matters for teams that cannot send source code to a third party, and it explains why the setup looks more like adding a CI job than installing a plugin.

## Result
ExampleLab says early users saw a 37% drop in review round trips. That is a vendor figure and nobody has reproduced it yet. What is not known: how well it copes with huge monorepos, and what it costs per review. If you maintain a mid-sized repo, trial it on a branch and compare its comments with your own."""

_MOCK_TIPS = """TITLE: Tricks & Tips Thursday: five small habits that make LLM code easier to trust
TLDR: Five small, copy-pasteable habits for checking and steering LLM-written code.
TAGS: llm, python, productivity, git
---
Most bad LLM code is not wrong in a clever way. It is wrong in a way a ten-second check would have caught.

## Situation
You paste a prompt, get forty lines back, and skim them. They look fine. Two days later one of them fails on an empty list.

## Task
You want a cheap routine that catches the obvious failures before the code reaches a review.

## Action
### Ask for the failing test first
Request a test that fails on the current code, then the fix. If the test passes immediately, the model misunderstood the bug. Why it works: it forces a concrete definition of "broken".

### See what actually changed
```bash
git diff --stat && git diff -U0
```
Why it works: zero-context diffs show only the changed lines, which is what you must read.

### Pin the output shape
Tell the model the exact JSON keys you expect and validate them on arrival. Why it works: malformed output fails loudly instead of flowing downstream.

### Run it on the nasty input
Feed it an empty list, a unicode string and a huge number before you trust it. Why it works: models write for the happy path.

### Keep the model's explanation out of the diff
Ask for the change first and the reasoning second, in a separate message. Why it works: you review code and prose separately, and the prose cannot hide a bad edit.

### Let the type checker argue first
Run your type checker or linter before you read a single line by eye. Why it works: it finds the boring mistakes for free, so your attention goes to logic.

## Result
None of this takes more than a minute, and each habit removes a whole class of surprise. After a week the routine becomes automatic, and reviews of LLM-written code start to feel like reviews of any other code. Recap:

- Failing test first.
- Read the zero-context diff.
- Validate the output shape."""

_MOCK_SELECT = '{"picks":[{"id":"c0","angle":"An agent that verifies its own suggestions before posting them."}]}'

_MOCK_DIAGRAM = """{"type":"flow","title":"What Atlas does with a pull request","steps":[{"label":"Index repo","detail":"Callers, tests and conventions"},{"label":"Run tests","detail":"Against the proposed change"},{"label":"Try each fix","detail":"In a sandbox"},{"label":"Post survivors","detail":"Only comments that pass"}],"caption":"Suggestions that break the build never reach a human."}"""


def _mock(stage: str) -> str:
    if stage.startswith("select"):
        return _MOCK_SELECT
    if stage.startswith("diagram"):
        return _MOCK_DIAGRAM
    if stage == "write:tips":
        return _MOCK_TIPS
    return _MOCK_NEWS
