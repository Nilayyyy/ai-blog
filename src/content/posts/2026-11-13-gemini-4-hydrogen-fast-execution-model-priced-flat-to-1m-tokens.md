---
title: "Gemini 4 Hydrogen: Fast Execution Model, Priced Flat to 1M Tokens"
description: "Google's Gemini 4 Hydrogen is a fast execution model that the company says edges past Argon on one index, at $1.50 per million input tokens and $7.50 output."
pubDate: 2026-11-13
tags: ["gemini", "llm", "coding-agents", "pricing", "google", "ai-radar"]
kind: radar
sources: ["https://blog.google/innovation-and-ai/models-and-research/gemini-models/introducing-gemini-4-hydrogen/"]
canonical:
---

Google says Gemini 4 Hydrogen scores 51 on the Artificial Analysis Intelligence Index at its default thinking level, one point above its larger sibling Gemini 4 Argon at 50. It is priced at $1.50 per million input tokens and $7.50 per million output tokens, with no surcharge as the context grows.

That is a company claim on a single index, so treat it as a reason to test rather than a verdict. Still, the pricing and the thinking-level dial make it easy to run your own comparison. Simon Willison's llm-gemini plugin reportedly supports it already. <!-- VERIFY: confirm llm-gemini release version and that it supports Gemini 4 Hydrogen -->

```diagram
{
  "type": "compare",
  "title": "Hydrogen vs Gemini 3.8 Flash",
  "caption": "All figures are Google's own claims; test on your own agent tasks at low, high and xhigh.",
  "before": {
    "heading": "Before",
    "points": [
      "Gemini 3.8 Flash was the fast tier",
      "57% vs 18.2% gap: Flash scores 18.2% on Terminal-Bench 4.1",
      "One model per session, frontier or fast",
      "Manual choice of model for each step"
    ]
  },
  "after": {
    "heading": "After",
    "points": [
      "Hydrogen finishes tasks 2.5x faster at default",
      "Scores 57% on Terminal-Bench 4.1",
      "Orchestrator switches Carbon and Hydrogen in one session",
      "Flat price to 1M tokens, no surcharge"
    ]
  }
}
```

## Situation

The Gemini 4 family has frontier models, Carbon and Argon, which Google positions for deep, long-horizon reasoning on hard problems. Those are the models you want for architectural judgment or a subtle bug.

Most of a coding agent's day is not that. It reads files, writes code, runs tests and checks the result. Running a frontier model on every step is slow and costs more than it needs to. Teams on Gemini 3.8 Flash, the previous fast tier, were the obvious candidates for something better.

## Task

The goal was a model that handles everyday coding and agentic work quickly, and that can either stand alone or act as the execution layer under a bigger model. A second problem was practical: deciding by hand which model gets which step is tedious, so the switching needed to be automatic.

## Action

Hydrogen is the fast, efficient member of the Gemini 4 family. Google describes its design as follows:

- **Thinking levels.** Four settings: low, medium, high (the default) and a new xhigh. The company says they scale smoothly, so you pay and wait only for the reasoning depth a task needs.
- **Flat pricing and big context.** A 1 million-token input window with up to 1 million output tokens, at one price across the whole window.
- **Parallel tool calls.** Google says the model batches file-read and search calls in parallel instead of inspecting files one at a time, which matters when exploring large repositories.
- **Surgical edits.** For debugging and issue resolution, the company says it makes focused changes without rewriting unrelated files.
- **Orchestrator in Google Antigravity.** Instead of one model for a whole session, Orchestrator switches between models such as Carbon and Hydrogen within the same session.
- **Coordinator and workers.** For parallel agents, Carbon can coordinate while Hydrogen runs worker and verifier agents that build and test changes in isolated workspaces.

Availability is broad. Google lists all tiers of Google AI Studio, the Gemini API, Gemini for business, the Gemini app and Search. Paid Google AI Pro and Ultra subscribers get it in Antigravity.

## Result

All figures below come from Google's announcement and are the company's own claims.

- Against Gemini 3.8 Flash, Hydrogen finishes tasks 2.5 times faster at its default setting. It scores 57% versus 18.2% on Terminal-Bench 4.1 and cuts fabricated claims by more than 5x.
- Google says partners in early testing saw runs 2x to 2.8x faster with 12% to 23% fewer tokens than 3.8 Flash.
- On Terminal-Bench 4.0, Orchestrator reached near-Carbon task success while using 24% less quota and finishing 19% faster, on average.
- Hydrogen reaches 54 on the Intelligence Index at xhigh.

Not yet known: how these numbers hold up on independent runs, and how Hydrogen behaves on your codebase. The announcement gives no absolute latency figures.

A reasonable first experiment is to run one of your real agent tasks at low, high and xhigh, then compare tokens used, wall time and pass rate against your current model.

## My take

TODO(nilay): add 2-4 sentences from your own experience or opinion, then delete this line.

## Sources

- [Introducing Gemini 4 Hydrogen](https://blog.google/innovation-and-ai/models-and-research/gemini-models/introducing-gemini-4-hydrogen/) (Hacker News)
