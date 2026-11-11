"""One function, complete(), in front of Claude Code, the Claude API, Gemini or a mock.

PROVIDER is a comma-separated list tried in order. Default: "claude-code,gemini".
  claude-code  The Claude Code CLI in print mode. Uses your Claude subscription (Pro/Max) instead of API billing.
               Auth: CLAUDE_CODE_OAUTH_TOKEN (from `claude setup-token`) or an existing `claude` login.
               Optional: CLAUDE_CODE_MODEL (default "sonnet"), CLAUDE_CODE_EFFORT, CLAUDE_CODE_BIN, CLAUDE_CODE_TIMEOUT.
  claude-api   The Claude API, billed separately. ANTHROPIC_API_KEY, optional CLAUDE_MODEL. ("claude" also works.)
  gemini       GEMINI_API_KEY, optional GEMINI_MODEL and GEMINI_FALLBACK_MODELS (comma separated).
  mock         Canned output for tests, no network.

If a provider fails, the next one in the list takes over and the failed one is skipped for the rest of the run,
so a used-up subscription limit costs one failed call, not one per stage. used_summary() says who wrote what.
"""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import requests

DEFAULT_PROVIDERS = "claude-code,gemini"
ALIASES = {"claude": "claude-api", "anthropic": "claude-api", "claudecode": "claude-code", "claude_code": "claude-code"}
KNOWN = ("claude-code", "claude-api", "gemini", "mock")
LABELS = {"claude-code": "Claude Code", "claude-api": "Claude API", "gemini": "Gemini", "mock": "mock"}

DEFAULT_GEMINI = "gemini-3.1-flash-lite"
GEMINI_FALLBACKS = ["gemini-3.5-flash-lite", "gemini-flash-lite-latest"]
DEFAULT_CLAUDE = "claude-sonnet-5-5"
DEFAULT_CLAUDE_CODE = "sonnet"  # alias that tracks the newest Sonnet
RETRYABLE = {429, 500, 502, 503, 504, 529}
JSON_NOTE = "\nReply with a single JSON object and nothing else: no code fences, no commentary."
# Failures where calling the same provider again cannot help.
_PERMANENT = re.compile(
    r"usage limit|rate limit|limit reached|not logged in|log in|login|authenticat|oauth|credit|"
    r"invalid api key|unauthori[sz]ed|forbidden",
    re.I,
)


class LLMError(RuntimeError):
    def __init__(self, message, status=None):
        super().__init__(message)
        self.status = status


# Per-run state: providers that already failed, and which provider/model served each stage.
_down: set[str] = set()
_used: list[tuple[str, str, str]] = []  # (stage, provider, model)


def reset() -> None:
    _down.clear()
    _used.clear()


def providers() -> list[str]:
    # `or` matters: an unset GitHub Actions variable arrives as an empty string.
    raw = os.getenv("PROVIDER") or DEFAULT_PROVIDERS
    out = []
    for name in raw.split(","):
        name = name.strip().lower()
        name = ALIASES.get(name, name)
        if not name:
            continue
        if name not in KNOWN:
            raise LLMError(f"Unknown PROVIDER '{name}' (use {', '.join(KNOWN)}, comma separated)")
        if name not in out:
            out.append(name)
    return out


def provider() -> str:
    return providers()[0]


def _label(p: str, model: str) -> str:
    return f"{LABELS[p]} ({model})" if model else LABELS[p]


def used_summary() -> str:
    """One line for the PR body, e.g. 'Claude Code (sonnet)' or 'Claude Code (sonnet); Gemini (x) for write:news'."""
    if not _used:
        return ""
    first = _used[0][1:]
    text = _label(*first)
    others: dict[str, list[str]] = {}
    for stage, p, m in _used:
        if (p, m) != first:
            others.setdefault(_label(p, m), []).append(stage)
    if others:
        text += "; " + "; ".join(f"{k} for {', '.join(v)}" for k, v in others.items())
    return text


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


# ---------------------------------------------------------------- Claude Code (subscription)

def _claude_code_cmd(exe: str, model: str, system_file: str) -> list[str]:
    cmd = [
        exe, "-p",
        "--output-format", "json",
        "--model", model,
        "--system-prompt-file", system_file,  # replaces Claude Code's own coding-agent prompt
        "--tools", "",                        # text in, text out: no file, shell or web tools
        "--disallowedTools", "mcp__*",
        "--strict-mcp-config",                # and no MCP servers from the machine's config
        "--no-session-persistence",
    ]
    effort = os.getenv("CLAUDE_CODE_EFFORT")
    if effort:
        cmd += ["--effort", effort]
    return cmd


def _parse_claude_code_output(stdout: str) -> dict:
    data = json.loads(stdout)
    if isinstance(data, list):  # message-list output: the last "result" message is the answer
        data = next((m for m in reversed(data) if isinstance(m, dict) and m.get("type") == "result"), None)
    if not isinstance(data, dict):
        raise ValueError("unexpected output shape")
    return data


def _claude_code_once(system, prompt, model):
    exe = os.getenv("CLAUDE_CODE_BIN") or shutil.which("claude")
    if not exe:
        raise LLMError("Claude Code CLI not found. Install it with: npm install -g @anthropic-ai/claude-code", status=0)
    env = dict(os.environ)
    if env.get("CLAUDE_CODE_OAUTH_TOKEN"):
        # An API key in the environment would win over the subscription token and bill the API instead.
        env.pop("ANTHROPIC_API_KEY", None)
    timeout = float(os.getenv("CLAUDE_CODE_TIMEOUT") or 600)
    with tempfile.TemporaryDirectory(prefix="radar-claude-") as tmp:
        system_file = Path(tmp) / "system.txt"
        system_file.write_text(system, encoding="utf-8")
        try:
            # The prompt goes in on stdin: article text is far longer than a Windows command line allows.
            # Running from an empty temp dir keeps the repo's CLAUDE.md and project settings out of the prompt.
            r = subprocess.run(
                _claude_code_cmd(exe, model, str(system_file)),
                input=prompt, capture_output=True, text=True, encoding="utf-8", errors="replace",
                timeout=timeout, cwd=tmp, env=env,
            )
        except subprocess.TimeoutExpired:
            raise LLMError(f"Claude Code timed out after {timeout:.0f}s")
        except OSError as e:
            raise LLMError(f"could not start Claude Code: {e}", status=0)
    try:
        data = _parse_claude_code_output(r.stdout)
    except ValueError:  # includes json.JSONDecodeError
        detail = (r.stderr or r.stdout or "").strip()[-400:]
        raise LLMError(f"Claude Code exited {r.returncode} without JSON output: {detail or 'no output'}")
    text = str(data.get("result") or "").strip()
    if data.get("is_error") or data.get("subtype") not in (None, "success"):
        raise LLMError(f"Claude Code error ({data.get('subtype')}): {text[:300] or (r.stderr or '').strip()[-300:]}")
    if not text:
        raise LLMError("empty response from Claude Code")
    usage = data.get("usage") or {}
    print(
        f"  claude-code {model}: {usage.get('input_tokens', '?')} in / {usage.get('output_tokens', '?')} out tokens, "
        f"{(data.get('duration_ms') or 0) / 1000:.0f}s",
        file=sys.stderr,
    )
    return text


def _claude_code(system, prompt, json_mode):
    model = os.getenv("CLAUDE_CODE_MODEL") or DEFAULT_CLAUDE_CODE
    if json_mode:
        system += JSON_NOTE
    last = None
    for i in range(2):
        try:
            return _claude_code_once(system, prompt, model), model
        except LLMError as e:
            last = e
            if e.status == 0 or _PERMANENT.search(str(e)):
                break  # missing CLI, no login or a used-up limit: trying again won't help
            if i == 0:
                time.sleep(_base_sleep() * 2)
    raise last


# ---------------------------------------------------------------- Claude API (billed separately)

def _claude_api(system, prompt, json_mode):
    if not os.getenv("ANTHROPIC_API_KEY"):
        raise LLMError("ANTHROPIC_API_KEY is not set")
    model = os.getenv("CLAUDE_MODEL") or DEFAULT_CLAUDE
    if json_mode:
        system += JSON_NOTE
    # No temperature: current Claude models reject non-default sampling settings.
    body = {
        "model": model,
        "max_tokens": 16000,
        "system": system,
        "messages": [{"role": "user", "content": prompt}],
    }
    headers = {"x-api-key": os.environ["ANTHROPIC_API_KEY"], "anthropic-version": "2023-06-01"}
    data = _post("https://api.anthropic.com/v1/messages", headers, body).json()
    if data.get("stop_reason") == "refusal":
        raise LLMError("Claude declined the request (stop_reason=refusal)")
    text = "".join(b.get("text", "") for b in data.get("content", []) if b.get("type") == "text").strip()
    if not text:
        raise LLMError("empty response from Claude")
    return text, model


# ---------------------------------------------------------------- Gemini

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
            text = _gemini_call(model, system, prompt, json_mode, temperature)
        except LLMError as e:
            last = e
            if e.status in (None, 404, 429, 500, 502, 503, 504, 529):
                print(f"  model {model} unavailable ({e}); trying the next one", file=sys.stderr)
                continue
            raise
        gap = os.getenv("CALL_GAP_SECONDS")
        time.sleep(float(gap) if gap not in (None, "") else 2.0)  # stay polite to free-tier rate limits
        return text, model
    raise last


# ---------------------------------------------------------------- the one entry point

def _call(p, system, prompt, stage, json_mode, temperature):
    if p == "mock":
        return _mock(stage), ""
    if p == "claude-code":
        return _claude_code(system, prompt, json_mode)
    if p == "claude-api":
        return _claude_api(system, prompt, json_mode)
    return _gemini(system, prompt, json_mode, temperature)


def complete(system: str, prompt: str, *, stage: str, json_mode: bool = False, temperature: float = 0.8) -> str:
    chain = providers()
    failures = []
    for p in chain:
        if p in _down:
            continue
        try:
            text, model = _call(p, system, prompt, stage, json_mode, temperature)
        except LLMError as e:
            failures.append(e)
            _down.add(p)
            rest = [q for q in chain if q not in _down]
            if rest:
                print(f"  {LABELS[p]} failed at '{stage}' ({e}); using {LABELS[rest[0]]} for the rest of this run",
                      file=sys.stderr)
            continue
        _used.append((stage, p, model))
        return text
    if len(failures) == 1:
        raise failures[0]
    if failures:
        raise LLMError("every provider failed: " + " | ".join(str(e) for e in failures))
    raise LLMError("every provider already failed earlier in this run")


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
