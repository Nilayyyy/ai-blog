---
title: "Tricks & Tips Thursday: Judges, Modern Web Rules, Tiny RAM"
description: "Five practical tricks: a fail-closed LLM judge, planted-breach test sets, a word-list baseline, a modern-web agent scan, and quantization mixing for local MoE models."
pubDate: 2026-11-12
tags: ["llm-evals", "guardrails", "coding-agents", "local-models", "quantization", "tips-thursday"]
kind: tips
sources: ["https://dev.to/kimolsen/human-in-the-loop-ai-building-a-fail-closed-llm-judge-for-outbound-email-2ml3", "https://github.com/GoogleChrome/modern-web-guidance", "https://github.com/synchopate/llama-modchip"]
canonical:
---

Your guardrail passes a test you wrote yourself, and your coding agent still reaches for 2019-era JavaScript. Local models keep asking for more RAM than you have.

Here are five tricks from this week's reading that cut down on each of those.

```diagram
{
  "type": "compare",
  "title": "Judging LLM Checks: Vibes vs Measured",
  "caption": "The author's word list stopped 11 of 22 breaches and held 6 of 18 clean emails.",
  "before": {
    "heading": "Before",
    "points": [
      "Read ten outputs, they look fine, ship",
      "Labels written after seeing the judge's answers",
      "Free-form judge replies that are hard to parse",
      "No baseline to show the model is worth it"
    ]
  },
  "after": {
    "heading": "After",
    "points": [
      "Labeled test set with verdicts, rules, marker strings",
      "Half the clean cases are adversarial traps",
      "Keyword filter baseline scored on the same set",
      "One enum tool call, fail closed on malformed"
    ]
  }
}
```

## Situation

LLM checks are often judged by feel. You read ten outputs, they look fine, and you ship.

Coding agents have their own problem: training data is full of legacy code, so they write bloated JavaScript for things the browser now does natively. And running a big mixture-of-experts model locally usually means "buy a GPU" or "give up".

## Task

You want a first-pass reviewer you can measure, an agent that writes modern web code, and a sense of which memory tricks make large local models fit on ordinary hardware.

## Action

### Build the test set with the truth baked in

Via dev.to: label every test item when you write it, not afterwards. Each email carries its verdict, the policy rule it breaks, the shape it hides in, and the exact strings that make it a breach.

```python
{"id": "D16", "verdict": "stop", "rule": "concession",
 "shape": "amount", "markers": ["1.200 kr."]}
```

Why it works: if you label after seeing the judge's answers, you grade the judge against itself. Planted markers also let you check a rewritten email with a plain string search, no model needed.

### Make half the clean cases traps

Via dev.to: the author's 18 clean emails were mostly adversarial, such as a buyer's own demand quoted under the signature, an allowed free pilot, and the word "internal" used innocently. Add the same kind of near-misses to your set.

Why it works: a judge that stops everything would beat a word list on breaches. Trap cases are what show the false-positive cost.

### Measure the dumb baseline first

Via dev.to: before the model, write the Friday-afternoon keyword filter and score it on the same set. The author's word list stopped 11 of 22 breaches and held 6 of 18 clean emails.

```python
WORDS = ["internal", "floor", "approve", "free"]
PCT = re.compile(r"(\d{1,3})\s?%")
```


Why it works: it gives you a bar the model has to clear, and it tells you whether the model is worth its cost.

### Force the judge to answer through one tool call

Via dev.to: give the judge the policy in the system prompt and one item as the user message, and require a tool call with an enum decision. The author's schema also asks for rule numbers, a quoted citation and a reason.

```python
"beslutning": {"type": "string", "enum": ["send", "stop"]},
"regler": {"type": "array", "items": {"type": "integer"}},
"citat": {"type": "string"},
```

Why it works: a constrained answer is easy to parse, and anything malformed can be treated as "stop". That is what fail-closed means. Requiring a citation also gives you something to check against the original text.

### Scan for legacy patterns, then install the guidance

Via Hacker News: Google Chrome's Modern Web Guidance project says agents default to older patterns because training data is full of legacy code. Its CLI can scan a codebase and pull targeted guides into the agent's context.

```bash
npx modern-web-guidance@latest legacy-scan .
npx modern-web-guidance@latest search "animate a dialog modal backdrop"
```

Why it works: the guides are short, curated and token-efficient, according to the project, so the agent gets current patterns without a long prompt of your own.

### Mix quantization formats by layer for local MoE models

Via Hacker News: the llama-modchip project says it runs a 284B DeepSeek model in under 59 GiB of RAM on CPU, with no GPU. Its trick is to keep sensitive layers (down projections, attention) at a higher bit width and compress the interior expert projections harder. The project claims this cuts that part's footprint by 33.3% against Q4_0.

Why it works: CPU inference on MoE models is bound by memory bandwidth per token, so fewer bits per weight means fewer bytes to move. These are the project's own numbers, so benchmark on your own hardware before relying on them.
## Result

Your guardrail now has a score instead of a vibe, and it has to beat a keyword filter to earn its place. Your agent gets a scan and a rules source rather than a hope. Your RAM budget gets a new set of options to try.

- Write the test set first, with verdicts, rules and marker strings built in, plus trap cases.
- Force a structured, citation-backed answer and fail closed on anything else.
- Scan for legacy web patterns, and give each model layer only as many bits as it needs.


## Sources

- [Human in the loop AI: building a fail-closed LLM judge for outbound email](https://dev.to/kimolsen/human-in-the-loop-ai-building-a-fail-closed-llm-judge-for-outbound-email-2ml3) (dev.to LLM)
- [GitHub - GoogleChrome/modern-web-guidance: Keep your coding agent up to date with the late](https://github.com/GoogleChrome/modern-web-guidance) (Hacker News)
- [GitHub - synchopate/llama-modchip: Run 284B DeepSeek-V4-Flash (<59GiB RAM: 41.1 cold pp, 9](https://github.com/synchopate/llama-modchip) (Hacker News)
