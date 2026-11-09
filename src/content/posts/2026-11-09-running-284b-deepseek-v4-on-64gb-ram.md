---
title: "Running 284B DeepSeek-V4 on 64GB RAM"
description: "The llama-modchip project enables running massive MoE models on consumer CPUs by optimizing memory footprint and cache-aware inference kernels."
pubDate: 2026-11-09
tags: ["llm", "inference", "optimization", "cpu", "quantization", "ai-radar"]
kind: radar
sources: ["https://github.com/synchopate/llama-modchip"]
canonical:
---

You can now run a 284B parameter DeepSeek-V4-Flash model on a standard workstation with 64GB of RAM without needing a massive GPU cluster. By using aggressive quantization and custom memory-management patches, this project fits the entire model into system memory while maintaining usable inference speeds.

```diagram
{
  "type": "flow",
  "title": "Running 284B Models Locally",
  "caption": "Custom patches enable 284B parameter models to run on 64GB RAM workstations.",
  "steps": [
    {
      "label": "Aggressive Quantization",
      "detail": "Compresses 284B model footprint from 82GB down to 56.56 GiB."
    },
    {
      "label": "Kernel Optimization",
      "detail": "Uses AVX-512BW tiling to maximize CPU cache hits during inference."
    },
    {
      "label": "Memory Management",
      "detail": "Prevents cold expert weights from evicting hot KV cache lines."
    },
    {
      "label": "Speculative Drafting",
      "detail": "Integrates an n-gram drafter to accelerate token generation speeds."
    }
  ]
}
```

## Situation
Running state-of-the-art Mixture-of-Experts (MoE) models typically requires high-end hardware, specifically massive amounts of VRAM to hold the model weights. Standard inference engines usually offload these to GPUs, but when the model size exceeds local hardware capacity, the system resorts to swap space or simply crashes with an Out-of-Memory (OOM) error. Developers working on local LLM applications were effectively gated by hardware costs, unable to run the most capable models locally because even 80GB A100 GPUs struggled with the full parameter counts of the largest MoEs. <!-- VERIFY: figure 80 not found in the source text -->

## Task
The goal was to make 284B parameter models runnable on common consumer hardware, specifically machines with 64GB of physical RAM. This required reducing the model's footprint to fit within system memory while ensuring the inference performance remained high enough for actual use, avoiding the performance penalty of swapping to disk.

## Action
The project, llama-modchip, provides a set of ggml/llama.cpp kernel patches and quantization tools to optimize MoE checkpoints. It focuses on memory efficiency and CPU cache utilization:

*   **Quantization:** It compresses DeepSeek-V4-Flash from its standard ~82GB footprint down to 56.56 GiB using custom block-64 BF16-scale tensors (type ID 40). <!-- VERIFY: figure 82 not found in the source text -->
*   **Kernel Patches:** The engine replaces standard matrix-vector loops with a multi-column tiling schedule (using AVX-512BW) to maximize L1, L2, and L3 cache hits.
*   **Speculative Drafting:** It integrates a Stockfish-PVS v2 n-gram drafter to speed up token generation.
*   **Memory Management:** The system uses non-temporal hints to prevent cold expert weights from evicting hot KV cache lines from the L3 cache.

To launch a model, the tool handles the heavy lifting of detecting system resources:
```bash
./llama-server-modchip-linux-x86_64 -m ./dsv4/DeepSeek-V4-Flash-0731-Fractal-00001-of-00003.gguf -c 32768 -t 16 -fa on --port 8080
```

## Result
On a 16-core Zen 5 processor, the system achieves 9.1–14.7 tokens per second for the 284B model. The project claims a 77% improvement in prefill and a 53% improvement in decode speeds compared to unoptimized implementations. While the tool supports various hardware, it requires specific patched binaries because standard Ollama or LM Studio builds will reject these custom tensor types. The project includes a benchmark suite for users to verify their specific CPU performance. If you have a machine with 64GB of RAM, you can try cloning the repository and running the `./modchip bench` command to see how your specific architecture handles these MoE workloads.

## My take

TODO(nilay): add 2-4 sentences from your own experience or opinion, then delete this line.

## Sources

- [GitHub - synchopate/llama-modchip: 🐋 Run 284B DeepSeek-V4-Flash (<59GiB RAM, 44.4 tok/s pp](https://github.com/synchopate/llama-modchip) (Hacker News)
