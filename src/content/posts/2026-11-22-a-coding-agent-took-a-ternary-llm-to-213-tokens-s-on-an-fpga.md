---
title: "A coding agent took a ternary LLM to 213 tokens/s on an FPGA"
description: "A founder let coding agents write C++ and Verilog for an AWS FPGA, going from 6 to 213 tokens/s on a ternary-weight model, with little hardware knowledge."
pubDate: 2026-11-22
tags: ["fpga", "coding-agents", "inference", "verilog", "hardware", "ai-radar"]
kind: radar
sources: ["https://ankitg.me/blog/vibecoding-inference-chip/"]
canonical:
---

The author says he has never written Verilog and hasn't touched serious C++ in about a decade. A cloud coding agent still got a full model running on an FPGA and made it 33x faster, from 6 to 213 tokens per second. The post is a first-person account, so the numbers are his, not independently verified.

```diagram
{
  "type": "flow",
  "title": "How an agent got a ternary LLM running fast on FPGA",
  "caption": "The author's own figures: 33x speedup, about $10,000 in tokens, not independently verified.",
  "steps": [
    {
      "label": "Rent FPGA",
      "detail": "Codex reserved an AWS F2 instance with 16 GB HBM"
    },
    {
      "label": "Run cloud agent",
      "detail": "Agent iterated for days in Conductor on a bit-exact baseline"
    },
    {
      "label": "Nudge with prompts",
      "detail": "Vibes plus ideas like speculative decoding; agent chose what to try"
    },
    {
      "label": "Add DeepGrove lessons",
      "detail": "Around 10 tokens/s, pasted ternary batch-1 design tips as context"
    },
    {
      "label": "Reach 213 tokens/s",
      "detail": "Hundreds of experiments took it from 6 to 213 tokens/s"
    }
  ]
}
```

## Situation

FPGAs are chips you can reconfigure so the loaded design determines how logic and routing are connected. In theory that gives performance advantages over a general-purpose CPU. In practice, the author says, programming one meant a mountain of C++ and manually analyzing waveforms for simulation and verification.

There are some GitHub repos that port ML models to FPGAs, but he hadn't seen a writeup on whether coding agents can write the low-level C++ and Verilog and verify the outputs well enough to run accurately.

## Task

The goal was to find out if agents could get a model running on an FPGA and fast enough to be useful. He rented AWS F2 instances, which have FPGA hardware with 16 GB of HBM, rather than buying a board. The model came from DeepGrove, whose founders he was talking to: a ternary-weight architecture that suits memory-limited setups.

## Action

He had Codex reserve the instance, then ran a cloud agent in Conductor for several days while he mostly encouraged it now and then. He says both Astra and Opus worked for this, interchangeably.

His own prompts were mostly vibes ("let's go for 2x faster, you got this"). Occasionally he added ML knowledge, such as suggesting speculative decoding or asking why something was running on CPU.

The most significant guidance came around 10 tokens/s. The DeepGrove founders, surprised it was working, said they had tried a few months earlier and the models weren't good enough. They sent a prompt of lessons from a batch-size-1 ternary design, which he pasted in as context. The excerpt includes:

- **No multipliers.** A 2-bit weight drives a 3:1 mux that picks x, ~x, or 0. The unused fourth code raises an error flag, so corrupt weights get caught.
- **Cheaper negation.** Lanes flag negatives, and the row reducer adds the +1s once per row instead of per lane.
- **Integer activations.** INT12, or INT16 where more range is needed, reduced as integers, with FP32 group scales and accumulation.
- **Deferred RMSNorm.** Quantize first, apply the scale after accumulation.
- **Packed weights.** 2-bit storage moves 8x more per transfer than 16-bit, which matters because at batch 1 fetching weights costs more than the math.
- **Streaming from HBM.** Weights go straight into compute lanes, with one chain per memory channel rather than a crossbar, keeping all 32 channels busy.

The prompt itself told the agent to treat the ideas as optional and avoid hours-long steps like physical design.

## Result

The author reports a 33x speedup from the first full-model bit-exact baseline, 6 to 213 tokens/s. He says the run produced roughly 3M lines of code across the experiment history, parsed 30M lines of output, and cost about $10,000 in Claude and OpenAI tokens across hundreds of experiments.

Open questions: he doesn't say how 213 tokens/s compares with GPUs or other hardware, and the sources here don't cover power or cost per token. How much the DeepGrove prompt contributed beyond his claim that it was the most significant guidance is also unclear.

If you want to try something similar, the experiment loop is the part worth copying: a bit-exact baseline, a measurable speed target, and an agent that keeps iterating.

## My take

TODO(nilay): add 2-4 sentences from your own experience or opinion, then delete this line.

## Sources

- [Vibecoding an inference chip](https://ankitg.me/blog/vibecoding-inference-chip/) (Hacker News)
