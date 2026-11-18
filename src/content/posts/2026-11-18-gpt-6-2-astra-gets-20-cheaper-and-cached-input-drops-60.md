---
title: "GPT-6.2 Astra gets 20% cheaper, and cached input drops 60%"
description: "OpenAI's GPT-6.2 Astra costs $8/$40 per million tokens, with cached input at $0.40. Early reception, though, is mixed."
pubDate: 2026-11-18
tags: ["openai", "gpt-62", "api-pricing", "agents", "llm", "ai-radar"]
kind: radar
sources: ["https://simonwillison.net/2026/Nov/17/gpt62-astra-and-sol/"]
canonical:
---

The most practical detail in OpenAI's GPT-6.2 launch is the price of cached input. GPT-6.2 Astra charges $0.40 per million cached tokens, down from $1 for GPT-6 Astra, according to Simon Willison's write-up. That matters for long-running agent sessions, which resend the same context many times.

Both models are in the API now. Early opinions are mixed.

```diagram
{
  "type": "compare",
  "title": "GPT-6.2 Astra vs GPT-6 Astra pricing",
  "caption": "Cached input drops 60%, which helps long agent sessions that resend context.",
  "before": {
    "heading": "GPT-6 Astra",
    "points": [
      "$10 per million input tokens",
      "$50 per million output tokens",
      "$1 per million cached tokens"
    ]
  },
  "after": {
    "heading": "GPT-6.2 Astra",
    "points": [
      "$8 per million input tokens",
      "$40 per million output tokens",
      "$0.40 per million cached tokens",
      "Matches Claude Fable 5.2's price"
    ]
  }
}
```

## Situation

Frontier model pricing has been drifting down in steps. Willison notes that GPT-6 Astra and Claude Fable 5 both cost $10 per million input tokens and $50 per million output tokens. Fable 5.2 then came in at 80% of its predecessor's price.

The cheaper tier has moved the same way. GPT-5.6 Sol cost $4/$20, and GPT-6 Sol and 6.1 Sol both halved that to $2/$10.

For anyone running agents, cost per task and cost of cached context are the numbers that decide which model you can afford to leave running.

## Task

OpenAI is selling two models for two jobs. In its words, GPT-6.2 Astra is "our new frontier model for your hardest projects," and GPT-6.2 Sol is "our efficient, versatile model for everyday work."

The aim is a clear split: pay more for Astra when the problem is hard, and use Sol when it isn't.

## Action

OpenAI shipped two models, available in the API as `gpt-6.2-astra` and `gpt-6.2-sol`. Here is what the source says about them:

- **Astra pricing:** $8 per million input tokens and $40 per million output tokens, which is 80% of GPT-6 Astra's $10/$50. That matches Claude Fable 5.2's price, according to Willison.
- **Astra cached input:** $0.40 per million, against $1 for the previous Astra. Willison calls this "great news for longer running agentic sessions."
- **Sol pricing:** unchanged at $2/$10, the same as 6.1 Sol and 6 Sol.
- **Tooling:** Willison shipped LLM 0.38 with support for both models. He also tested them in the Codex CLI and the Codex desktop app at "Ultra" effort levels. The pelican comparisons he mentions ran at high, xhigh and max.

The editor's pitch for this post mentioned gains in coding and computer use. The source I have doesn't include OpenAI's benchmark figures or capability claims, so I can't confirm those. What is confirmed is the pricing and availability.

## Result

Nothing here is a controlled benchmark, and the one task Willison reports is his own informal test. He asked both models, at Ultra effort, to build a three.js animation of Yonkers standing up as a giant mech and stomping across Manhattan, Queens and Brooklyn using OpenStreetMap data. He says neither did a good enough job of the mech transformation compared with Claude Fable 5.2 and Gemini 4 Carbon.

He also describes the wider reaction as mixed. Astra 6.2 isn't scoring quite as high as Fable 5.2 on various benchmarks, and he's seen complaints that its communication style can be confusing. Theo Browne's pre-release feedback letter gives an example. Two hours into a `/goal` task to make a new level for Outer Wilds, the model was "blocked" asking whether a reviewer writes its clips to one filename or another.

Still unknown is how Astra's price-to-quality ratio holds up on real workloads. If you run long agent sessions, compare your actual cached-token bill and how often the model stops to ask unnecessary questions.

## My take

TODO(nilay): add 2-4 sentences from your own experience or opinion, then delete this line.

## Sources

- [GPT‑6.2 Astra and GPT‑6.2 Sol](https://simonwillison.net/2026/Nov/17/gpt62-astra-and-sol/) (Simon Willison)
