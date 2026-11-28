---
title: "DeepMind lets AI agents control part of Gemini's compute"
description: "DeepMind's Koray Kavukcuoglu says agents now run Gemini experiments and control part of the compute, though full recursive self-improvement is far off."
pubDate: 2026-11-28
tags: ["deepmind", "gemini", "ai-agents", "research-infrastructure", "safety", "ai-radar"]
kind: radar
sources: ["https://the-decoder.com/ai-agents-now-control-part-of-deepminds-compute-for-gemini-experiments-but-recursive-self-improvement-remains-distant/"]
canonical:
---

Google DeepMind has AI agents running experiments for the next Gemini model, and those agents control part of the compute themselves. That comes from Koray Kavukcuoglu, VP of Research and the person who leads Gemini development, speaking on the company's podcast. He also says the lab is still far from full recursive self-improvement.

The details are thin, but the claim is concrete: agents are operating real research infrastructure, not just writing code for humans to run.

```diagram
{
  "type": "flow",
  "title": "How DeepMind's agents help build Gemini",
  "caption": "Details are thin: no figures, architecture, or review process were reported.",
  "steps": [
    {
      "label": "Agents run experiments",
      "detail": "They run experiments for the next Gemini model on their own."
    },
    {
      "label": "Control part of compute",
      "detail": "Agents manage a share of compute; the amount isn't disclosed."
    },
    {
      "label": "Thought stream unrewarded",
      "detail": "Training doesn't reward chain of thought, as a safety measure."
    },
    {
      "label": "Intentions stay readable",
      "detail": "Unfiltered natural-language intentions can be reviewed before agents act."
    }
  ]
}
```

## Situation

Most agent talk in developer circles is about coding assistants and tool use inside a repo or a browser. Research labs are a different setting, because the scarce resource is compute and every experiment competes for it.

According to Kavukcuoglu, DeepMind has also changed how it organizes work. Instead of separate teams for specialized projects like AlphaFold and nuclear fusion, the lab now relies on a single general-purpose algorithm for both science and products. He adds that each Gemini generation is a hand-built one-off rather than a fixed architecture, while parallel teams already work on its successors.

## Task

The goal, as described, is to move faster on the next Gemini model. Experiments are the bottleneck in that work, and if agents can run them on their own, human researchers spend less time on setup and scheduling.

The harder part is doing this without losing sight of what the agents are doing. Giving software control over compute only works if people can still tell why it made a given choice.

## Action

The source gives a short list of what DeepMind says it is doing:

- **Agents run experiments for the next Gemini model.** Kavukcuoglu says they do this on their own.
- **Agents control part of the compute.** Not all of it. The source does not say how much, how it is allocated, or what limits or approvals apply.
- **Chain of thought is not rewarded in training.** As a safety measure, DeepMind doesn't reward the agents' internal thought streams, he says. The idea is that their intentions stay unfiltered and reviewable in natural language before they act.

That last point is the most technically interesting. If you train a model to produce reasoning that looks good, you risk teaching it to write reasoning that looks good rather than reasoning that is honest. Leaving the thought stream out of the reward is meant to keep it a more faithful record. That is general background, and the source only reports DeepMind's stated approach.

The source does not describe the agent architecture, the scheduler, the model behind the agents, or how humans review the thought streams. It also says nothing about how the agents' experiment choices are checked, or what happens when an agent's plan looks wrong.

Kavukcuoglu also points to limits in current models. They can depict physical processes such as fluid flows and collisions with visual accuracy, he says, but don't understand them precisely.

## Result

No measurements are reported. There are no figures on how much compute the agents control, how many experiments they run, or how much faster Gemini development has become. Everything here is Kavukcuoglu's account of his own lab, relayed by The Decoder.

His stance on the bigger question is cautious. He says no test can show when models will reach AGI, because no benchmark captures the core of intelligence. In his view, AGI won't begin until useful everyday products earn enough trust for people to hand decisions over to them, the way they would when working with other people.

If you build agents that touch real resources, watch for DeepMind publishing more on how it scopes and reviews that control. In the meantime, the design question to borrow is simple: can you read what the agent intended before it acts?

## My take

TODO(nilay): add 2-4 sentences from your own experience or opinion, then delete this line.

## Sources

- [AI agents now control part of Deepmind's compute for Gemini experiments, but recursive sel](https://the-decoder.com/ai-agents-now-control-part-of-deepminds-compute-for-gemini-experiments-but-recursive-self-improvement-remains-distant/) (Hacker News)
