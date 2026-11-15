---
title: "Implementing DeepSeek V3 in 190 lines of JAX"
description: "A minimal JAX implementation of DeepSeek V3 provides a readable, stripped-down look at MoE and MLA architectures on consumer hardware."
pubDate: 2026-11-15
tags: ["deepseek", "jax", "llm", "architecture", "machine-learning", "ai-radar"]
kind: radar
sources: ["https://github.com/Vaibhaav-Tiwari/deepseek-v3-jax"]
canonical:
---

You can now run a functional replica of the DeepSeek V3 architecture in just 190 lines of clean JAX code. The implementation manages to fit the model's complex components—including DeepSeekMoE and Multi-head Latent Attention (MLA)—into a single file that you can read from top to bottom.

```diagram
{
  "type": "flow",
  "title": "DeepSeek V3 Architecture Flow",
  "caption": "A 190-line JAX implementation that demystifies DeepSeek V3 logic through readable, standalone code.",
  "steps": [
    {
      "label": "Parameter Definition",
      "detail": "Uses plain dictionaries of arrays instead of complex framework abstractions."
    },
    {
      "label": "Dense MoE Routing",
      "detail": "Processes all tokens through experts, zeroing out unpicked ones for simplicity."
    },
    {
      "label": "Explicit MLA Decompression",
      "detail": "Decompresses latent states explicitly to make transformation steps easy to trace."
    },
    {
      "label": "JAX Compute Execution",
      "detail": "Runs standard JAX functions compatible with Apple Silicon via JAX-Metal."
    }
  ]
}
```

## Situation
Modern state-of-the-art models like DeepSeek V3 are notoriously opaque to developers who don't have access to massive distributed clusters or proprietary framework internals. The official architecture relies on sophisticated techniques like DualPipe, FP8 training, and complex sparse expert routing that are typically hidden behind layers of abstraction in heavy frameworks like PyTorch or custom distributed backends. For a developer wanting to understand the math behind Multi-head Latent Attention (MLA) or how auxiliary-loss-free balancing works, the production-grade codebases are often too bloated to serve as a reference.

## Task
The goal was to create an educational, accessible implementation of the DeepSeek V3 technical report that functions as a standalone architecture demo. It needed to be readable enough to explain the core mechanisms of the model—specifically the routing math and latent compression—without relying on massive infrastructure or external dependencies like Flax or Equinox.

## Action
The implementation avoids framework bloat by using plain dictionaries of arrays for parameters and standard JAX functions for the compute. It strips away production optimizations like sparse dispatch or weight absorption to prioritize clarity.

Key technical choices include:
*   **Dense MoE Compute:** Every expert processes every token, with unpicked experts zeroed out to simplify the routing logic.
*   **Explicit MLA Decompression:** Instead of weight absorption, the model decompresses the latent state explicitly, making the transformation steps easier to trace.
*   **Hardware Compatibility:** The code is written to run on Apple Silicon via JAX-Metal, with specific accommodations to avoid operations that the current jax-metal 0.1.1 backend cannot handle, such as gradients through 2-axis contraction.

The setup is minimal, requiring only Python 3.12 and pinned dependencies. By focusing on the architecture rather than scale, the model runs with 36.2M parameters and 6 layers, compared to the original's 671B parameters and 61 layers.

## Result
The implementation provides a verifiable baseline for how the model’s balancing logic affects training. In a 2,000-step run on an M5 MacBook Air, validation loss was nearly identical whether balancing was enabled (3.921) or disabled (3.923), supporting the technical report's claim that the bias mechanism evens out experts without significant cost. 

While this version lacks features like YaRN context extension and node-limited routing, it successfully demonstrates the model's core logic on a local machine. Because the checkpoint is a Python pickle, it is important to load these files only from trusted sources. If you want to explore the architecture, try running the provided `sample.py` to see how the model behaves on public-domain detective fiction, or use the `small` configuration to test the training loop on systems with limited memory.

## My take

TODO(nilay): add 2-4 sentences from your own experience or opinion, then delete this line.

## Sources

- [GitHub - Vaibhaav-Tiwari/deepseek-v3-jax: DeepSeek V3 (MLA, DeepSeekMoE, aux-loss-free bal](https://github.com/Vaibhaav-Tiwari/deepseek-v3-jax) (Hacker News)
