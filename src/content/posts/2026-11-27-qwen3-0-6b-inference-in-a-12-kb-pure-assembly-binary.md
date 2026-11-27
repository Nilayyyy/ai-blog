---
title: "Qwen3-0.6B inference in a 12 KB pure-assembly binary"
description: "llm.asm runs Qwen3-0.6B, boots as a bare-metal OS and trains a tiny GPT, all in x86-64 NASM assembly with no libc or dependencies."
pubDate: 2026-11-27
tags: ["assembly", "inference", "qwen3", "x86-64", "open-source", "ai-radar"]
kind: radar
sources: ["https://github.com/alesha-pro/llm.asm"]
canonical:
---

A Qwen3-0.6B inference engine fits in a 12 KB binary written entirely in x86-64 NASM assembly, with no C, no libc and no libm. The same repo also holds a bootable bare-metal OS and a from-scratch Mini-GPT trainer.

The weights still take about 614 MiB. The code that runs them does not. <!-- VERIFY: figure 614 not found in the source text -->

```diagram
{
  "type": "stack",
  "title": "llm.asm: Qwen3-0.6B with nothing underneath",
  "caption": "Author reports 18-36% faster decode than llama.cpp on one EPYC 7642; prefill is slower.",
  "layers": [
    {
      "label": "Three assembly projects",
      "detail": "Inference 12 KB, bare-metal OS 22 KB, Mini-GPT trainer 32 KB"
    },
    {
      "label": "Transformer math kernels",
      "detail": "RMSNorm, RoPE, SiLU, softmax, BPE tokenizer, hand-written in assembly"
    },
    {
      "label": "AVX2 GEMM/GEMV engine",
      "detail": "INT8xINT8 arithmetic, FP16 block scales, next-row prefetch"
    },
    {
      "label": "Raw thread pool",
      "detail": "Parallel grouped-query attention, bit-exact across thread counts"
    },
    {
      "label": "No C, libc or libm",
      "detail": "Pure x86-64 NASM; 17,252 lines of assembly in total"
    }
  ]
}
```

## Situation

Most LLM inference code you run sits on a deep stack: Python or C++, a math library, a threading runtime, a BLAS or a hand-tuned kernel set. That is sensible engineering, but it hides how small the core computation is.

A transformer forward pass is matrix-vector products, a few normalizations, an attention loop and a sampler. The rest is mostly packaging.

llm.asm is a project that strips the packaging away, to see what is left.

## Task

The goal, as the repo presents it, is three complete LLM projects with nothing underneath them: inference, a bootable OS that runs the model, and a trainer. Each had to be fast enough to be worth running, not only a demo of the idea.

The author also compares decode speed against llama.cpp, so "small" is not the only claim being made.

## Action

The repo says everything is assembled with `nasm` and linked with `ld`, with 17,252 lines of assembly across the three projects. That includes the math kernels, the tokenizer and the thread pool.

- **Inference (12 KB):** a Qwen3-0.6B engine with a hand-written `expf`, `sincosf`, RMSNorm, RoPE, SiLU and softmax, an AVX2+FMA+F16C GEMM/GEMV engine, a BPE tokenizer, and a thread pool built on raw `clone()` and `futex()`. It has a `--chat` mode that keeps the KV cache across turns.
- **Bare-metal OS (22 KB):** a bootable kernel with SMP support that runs the same model. The repo describes a boot path through Multiboot, 4-level paging and long mode, and offers a BIOS+UEFI ISO for QEMU or Proxmox VE. <!-- VERIFY: figure 22 not found in the source text -->
- **Mini-GPT trainer (32 KB):** an analytical backward pass, an AdamW optimizer and a live Unicode Braille TUI that draws the loss curve in the terminal. <!-- VERIFY: figure 32 not found in the source text -->

For decode speed, the README credits INT8xINT8 AVX2 arithmetic, FP16 block scales, next-row prefetch, a head-major KV cache and parallel grouped-query attention. It also says outputs are bit-exact across thread counts.

Weights use a custom `.asmbin` format that you export from a model directory with a Python script. Training itself needs no Python:

```
make train
./build/asm-gpt-train --data data/tinyshakespeare.txt --steps 400 --seq 128 -t 16 --save checkpoints/shakespeare.ckpt
```

## Result

On an AMD EPYC 7642, CPU-only, with Qwen3-0.6B Q8_0, the author reports llm.asm beating llama.cpp on decode by 18% to 36% across 1 to 40 threads, and the bare-metal OS gaining roughly another 10% from huge pages. These are the author's own numbers from a 3-run average on one machine. The README also notes that llama.cpp is ahead on prompt prefill, since llm.asm processes prompt tokens one at a time. <!-- VERIFY: figure 40 not found in the source text -->

The sample trainer output is a 2.68M-parameter model reaching a validation loss of 1.8399 in 35.2 seconds. Its sample text is still garbled Shakespeare. <!-- VERIFY: figure 2.68M not found in the source text -->

Independent reproductions and other CPUs are not covered. If you want to try it, `make all` builds everything, and the inference path is the place to start.

## My take

TODO(nilay): add 2-4 sentences from your own experience or opinion, then delete this line.

## Sources

- [GitHub - alesha-pro/llm.asm: Qwen3-0.6B inference (12 KB), bare-metal bootable OS (22 KB),](https://github.com/alesha-pro/llm.asm) (GitHub)
