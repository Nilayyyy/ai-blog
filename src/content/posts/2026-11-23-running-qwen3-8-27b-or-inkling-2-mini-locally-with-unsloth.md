---
title: "Running Qwen3.8-27B or Inkling 2 Mini locally with Unsloth"
description: "A GPUPartner guide shows how to serve a quantized Qwen or Inkling 2 Mini model from a Windows PC with Unsloth Desktop, and share it across your home network."
pubDate: 2026-11-23
tags: ["local-ai", "qwen", "unsloth", "quantization", "inkling", "ai-radar"]
kind: radar
sources: ["https://www.gpupartner.com/blog/beginners-guide-local-ai-inkling-qwen-unsloth"]
canonical:
---

Inkling 2 Mini's recommended 4-bit file is 17.6 GB, within 0.1 GB of the Qwen3.8-27B file the guide uses. On a 32GB card that leaves about 14GB for context, according to the guide. It's a practical walkthrough for getting a chat model running at home without a terminal.

```diagram
{
  "type": "flow",
  "title": "Run a local model with Unsloth Desktop",
  "caption": "Quantization shrinks the ~56GB full Qwen model so it fits consumer GPUs; setup takes about 10-15 minutes, excluding downloads.",
  "steps": [
    {
      "label": "Check your VRAM",
      "detail": "Match model size to GPU memory; 32GB+ allows 64K-128K+ context."
    },
    {
      "label": "Install Unsloth Desktop",
      "detail": "Free app that serves the model through a chat interface."
    },
    {
      "label": "Download quantized model",
      "detail": "Pick a 4-bit file that fits, such as Q4 variants."
    },
    {
      "label": "Set context size",
      "detail": "Context competes with the model for memory, so leave room."
    },
    {
      "label": "Turn on LAN access",
      "detail": "Everyone on the home network can then use the model."
    }
  ]
}
```

## Situation

The guide's author, Jerry James at GPUPartner, argues that open-weight models like Qwen make cloud LLM providers look more like infrastructure than something you must depend on for routine tasks. He claims OpenAI and Anthropic have dropped quality in "latest" versions and limit what you can run. That is his opinion, and the post offers no evidence for it here. He adds rising costs and privacy worries to the case.

His practical complaint is simpler: usage limits on token-heavy work.

## Task

James wanted to offload research, data collection and coding tasks to a model running on his own hardware, so he wasn't watching a usage meter. He kept it beginner-friendly: Windows, no terminal commands, no Python environments, no subscriptions. The goal was also to let everyone on the home network use it.

He says that once the hardware is sorted, setup takes about 10-15 minutes, excluding downloads.

## Action

The setup is Unsloth Desktop, a free app that serves the model through a chat interface, plus a model sized to your GPU's VRAM. The short version in the guide: install it, download a quantized model that fits, set the context size, and turn on LAN access.

The guide's main lessons:

- **Quantization is the enabler.** It compresses weights to lower precision, trading some accuracy for a model that fits and runs faster. The guide says some workloads barely notice and others become nearly unusable. The full-size Qwen model is around 56GB, too big for most consumer GPUs.
- **Match the model to VRAM.** The guide's rough tiers are 8-12 GB (small models, 8K-16K context), 16 GB, 24 GB, and 32 GB+ (64K-128K+ context). The Q4 variants (UD-Q4_K_XL, Q4_K_M and so on) are the common starting points.
- **Mixture-of-experts helps small cards.** MoE models run only a few billion parameters per token, with the rest in system RAM. That is why the guide puts a 35B model in the 16 GB row.
- **Context competes with the model for memory.** On his RTX 5090 (32GB), James chose Qwen3.8-27B at 4-bit rather than the largest model that fits, to leave room for a bigger context window.
- **Inkling 2 Mini fits the same recipe.** The guide says Thinking Machines Lab released it on November 17, 2026: 26.4B parameters, Apache 2.0, vision support, 1M-token context, 5.4B active parameters. You need a recent Unsloth Desktop build.
- **Inkling 2 Small does not fit.** It is a 594B model, and the smallest Unsloth file is 171.7 GB. That means a 256GB Mac Studio or a DGX Station.

Macs work too thanks to unified memory. The guide says to grab the MLX build for Apple Silicon.

The text we have cuts off before the step-by-step Unsloth Desktop instructions, so the exact clicks aren't covered here.

## Result

No quality benchmarks against cloud models are reported. The one speed figure is from GPUPartner's own VRAM calculator, not a measurement in the article: about 47 tokens per second for Qwen3.6-35B on an RTX 5060 Ti 16GB. Unsloth's Inkling 2 Mini sizes are 10-11 GB at 2-bit, 17-18 GB at 4-bit and 24 GB at 8-bit. They count RAM and VRAM together and cover the model alone, so long contexts need more.

Unknown: how these models compare with the cloud services on your own tasks, and how well a shared home server holds up under several users.

If you have a 24-32GB card, check your VRAM, pick a 4-bit file, and test it on a task you currently send to a cloud API.

## My take

TODO(nilay): add 2-4 sentences from your own experience or opinion, then delete this line.

## Sources

- [A beginner's guide to Local AI with Inkling, Qwen, and Unsloth](https://www.gpupartner.com/blog/beginners-guide-local-ai-inkling-qwen-unsloth) (Hacker News)
