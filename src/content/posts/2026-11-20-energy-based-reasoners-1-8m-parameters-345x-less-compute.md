---
title: "Energy-Based Reasoners: 1.8M parameters, 345x less compute"
description: "A small looped model learns an energy score over its own reasoning states, and the paper reports 99.9% on Sudoku-Extreme with 345x less inference compute."
pubDate: 2026-11-20
tags: ["reasoning", "energy-based-models", "recurrent-models", "inference-efficiency", "research", "ai-radar"]
kind: radar
sources: ["https://energy-based-reasoners.github.io/"]
canonical:
---

A 1.8M-parameter model reaches 99.9% accuracy on Sudoku-Extreme while using 345× less inference compute than the next-best model, according to its authors. The trick is that the model learns a score for its own half-finished reasoning and uses that score to decide when to stop. <!-- VERIFY: the editor's note said 385x, but the source text says 345x throughout; this post uses 345x -->

This is a recurrent reasoning paper, not a new LLM decoding method. The comparison is against other looped reasoners on puzzle benchmarks, so treat the number accordingly.

```diagram
{
  "type": "flow",
  "title": "How Energy-Based Reasoners think",
  "caption": "One learned energy handles scoring, refining, stopping and selecting, per the authors' claims.",
  "steps": [
    {
      "label": "Score",
      "detail": "Energy rates how well a reasoning state fits the board; lower is better"
    },
    {
      "label": "Refine",
      "detail": "The energy gradient gives an improvement direction for the state"
    },
    {
      "label": "Stop",
      "detail": "Each trajectory halts when its gradient falls below a threshold"
    },
    {
      "label": "Select",
      "detail": "Across multiple trajectories, pick the lowest-energy candidate solution"
    }
  ]
}
```

## Situation

Looped models get their depth by running the same block repeatedly on a latent state. That lets a small network do multi-step reasoning without emitting a long chain of tokens.

The weakness the authors point to is that these models have no explicit measure of progress. A looped model updates its state, but nothing in the model says whether the new state is better than the old one. That makes two things hard: knowing when to stop looping, and knowing how to improve the current state.

## Task

The goal was to give a looped reasoner a built-in signal for progress. Specifically, the authors wanted one mechanism that could tell the model how good a candidate is, which direction to move it, and when it is done.

They also wanted to avoid bolting on an external verifier. Ideally the model that reasons also judges its own answers.

## Action

The paper, from Duke, UIUC and Harvard, introduces Energy-Based Reasoners (EBRs). An EBR learns an energy function over latent reasoning states. The looped update is then formulated as gradient descent on that energy. The authors describe four roles for the energy:

- **Score.** The energy rates how compatible a reasoning state is with the initial board. Lower is better.
- **Refine.** The gradient of the energy gives an improvement direction for the state.
- **Stop.** When the gradient is small, the state is effectively stationary. Each trajectory stops once its energy gradient falls below a threshold, so easy puzzles finish in a few steps and hard ones keep going.
- **Select.** When you run multiple trajectories and get multiple candidate solutions, pick the one with the lowest energy.

That gives you two knobs at inference time. More descent steps refine each answer further, and more trajectories give the energy more candidates to choose from.

Training gets its own addition: exploration-based training. The authors say it helps discover additional modes and shapes the energy landscape over a broader set of states, rather than only the states near one solution. This matters for problems with many valid answers, since the model needs to land in different basins.

The authors describe the sampling behavior as acting like stochastic gradient descent, which lets one model capture many different solutions.

## Result

The numbers below are the authors' own, from their project page and paper (arXiv 2611.08977).

- On Sudoku-Extreme, EBRs reach 99.9% accuracy with 1.8M parameters, using 345× less inference compute than the next-best model and comparable training compute.
- On N-Queens and Graph Coloring, which have multiple valid solutions, EBRs achieve state-of-the-art coverage while keeping near-100% single-sample accuracy. Coverage here is the share of an input's distinct valid solutions that 20 samples find.
- Across four algorithmic reasoning benchmarks, the authors say EBRs match or outperform prior recurrent reasoning models.

Still unknown from the source text: how this behaves on tasks outside structured puzzles, whether it transfers to language models, and how the compute figure translates to wall-clock time. The page also doesn't name the next-best model in the excerpt.

If you work on looped or test-time-compute models, read the paper for how the stopping rule and lowest-energy selection are implemented.

## My take

TODO(nilay): add 2-4 sentences from your own experience or opinion, then delete this line.

## Sources

- [Energy-Based Reasoners: Your Recurrent Reasoner Should Be an Energy-Based Model](https://energy-based-reasoners.github.io/) (Hacker News)
