---
title: "GLM-5.4 reuses its own layers, and you can call it today"
description: "Z.ai's GLM-5.4 is its first looped transformer, and it's the second looped model in a week, but it's only reachable through a Coding Plan API."
pubDate: 2026-11-24
tags: ["glm", "looped-transformer", "coding-models", "z-ai", "architecture", "ai-radar"]
kind: radar
sources: ["https://simonwillison.net/2026/Nov/23/glm-54/"]
canonical:
---

Z.ai's GLM-5.4 runs a group of weight-shared layers multiple times per forward pass, which the lab says gives a deeper network without adding parameters. It is the company's first looped transformer, and it is available now through the Z.ai API.

It is also the second looped model Simon Willison noticed in a week, which makes this look less like a one-off experiment.

```diagram
{
  "type": "compare",
  "title": "Standard vs looped transformer",
  "caption": "Z.ai says GLM-5.4 gets depth without extra parameters; no benchmarks yet confirm it helps coding.",
  "before": {
    "heading": "Before",
    "points": [
      "Each layer runs once per forward pass",
      "More depth means adding layers",
      "Parameter count rises with depth"
    ]
  },
  "after": {
    "heading": "After",
    "points": [
      "Weight-shared layer group runs multiple iterations",
      "Each pass refines the previous hidden states",
      "Depth grows without adding parameters"
    ]
  }
}
```

## Situation

In a standard transformer, each layer runs once per forward pass. If you want more depth, you add layers, and the parameter count goes up with them.

Looped designs take another route. Z.ai describes it this way: a group of weight-shared layers runs for multiple iterations, refining the hidden states from the previous pass.

GLM-5.4 is not alone here. Willison points to Inkling 2 Mini from Thinking Machines Lab, released on November 20th, as the first looped transformer he saw that week. Two in seven days is a small sample, but it is enough to pay attention.

## Task

The goal, as the two labs frame it, is more reasoning quality without a bigger model. Z.ai's pitch is depth without extra parameters.

Thinking Machines Lab says its looped design lets the model apply more reasoning and reach the right answer with fewer tokens. It names agentic coding as a task that depends on that reasoning quality. GLM-5.4's title points at the same target: generalized coding.

## Action

Based on the descriptions in the sources, the mechanism is simple to state:

- **Shared layers, repeated.** A group of layers with tied weights runs several times instead of once. Each pass refines the hidden states from the previous pass.
- **Same parameters, more compute per token.** Depth increases, the parameter count does not. Z.ai makes this claim itself.
- **Inkling 2 Mini's version.** Thinking Machines Lab says it runs the middle layers of the model three times for every token. Z.ai's source text, as quoted by Willison, does not say how many iterations GLM-5.4 uses or which layers loop.

Access is the awkward part. Willison reports that GLM-5.4 is not available as open weights, at least not yet. It also cannot currently be reached through Z.ai's regular API.

He got in by signing up for the Coding Plan subscription. The coding plan and the regular API share the same OpenAI-compatible Responses API, at `https://api.z.ai/api/v1`. The coding plan key worked against that endpoint and gave him access to the new model.

He then wrote an `llm-glm` plugin for his LLM tool, only to find that `llm-zai` by Tommy Hughes already exists. He published his anyway because `llm-zai` does not yet support the new model, and says he will likely retire his once that plugin catches up.

## Result

There are no benchmark numbers in the source, so nothing here says whether looping improves coding. Z.ai's claims about depth and parameter count are the company's own, and the source does not show them tested.

What Willison did report is informal. He ran his pelican drawing test at low, high, and max effort levels. GLM-5.4's output looks similar in quality to GLM-5.3's, and both look more like pelicans from OpenAI or Anthropic models. GLM-5.1 and 5.2 had a distinctive look of their own. That is a style observation, not a measure of coding ability.

Still unknown: open weights, iteration counts, and real coding evals. If you have a Coding Plan, point an OpenAI-compatible client at the Responses endpoint and compare it against your current coding model on your own tasks.

## My take

TODO(nilay): add 2-4 sentences from your own experience or opinion, then delete this line.

## Sources

- [GLM-5.4: Toward Generalized Coding with Our First Loop Transformer](https://simonwillison.net/2026/Nov/23/glm-54/) (Simon Willison)
