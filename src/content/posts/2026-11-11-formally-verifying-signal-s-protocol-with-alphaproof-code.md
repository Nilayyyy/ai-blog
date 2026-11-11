---
title: "Formally verifying Signal’s protocol with AlphaProof Code"
description: "Google DeepMind used an AI agent framework and Lean to formally verify the cryptographic code underlying the Signal protocol."
pubDate: 2026-11-11
tags: ["formal-verification", "security", "lean", "cryptography", "ai-agents", "ai-radar"]
kind: radar
sources: ["https://deepmind.google/blog/introducing-alphaproof-code/"]
canonical:
---

Google DeepMind researchers have used an AI agent framework to formally verify the implementation of the Signal cryptographic protocol. By generating over six million lines of Lean code, the team proved that the compiled code running on devices matches its security specifications.

```diagram
{
  "type": "flow",
  "title": "Verifying Signal with AlphaProof",
  "caption": "AlphaProof Code automates formal verification, reducing years of work to four weeks.",
  "steps": [
    {
      "label": "Translate requirements",
      "detail": "Experts and AI translate security needs into formal mathematical specifications."
    },
    {
      "label": "Generate proofs",
      "detail": "AI agents use Lean to generate proofs for the code."
    },
    {
      "label": "Audit and review",
      "detail": "Humans review one percent of code while Lean validates the rest."
    },
    {
      "label": "Verify implementation",
      "detail": "System confirms compiled code matches security specifications, closing the design gap."
    }
  ]
}
```

## Situation
Formal verification—mathematically proving code is free of flaws—is considered the gold standard for security. Historically, this process is incredibly labor-intensive and slow, often taking expert teams years to complete. Furthermore, most existing verification efforts stop at the design level, ignoring the implementation. This creates a dangerous gap between a perfect design and the actual, potentially buggy code running on hardware. Real-world vulnerabilities frequently hide in this gap, making high-assurance verification a massive engineering hurdle for any widely deployed software system.

## Task
The goal was to formally verify the actual production code of the Signal cryptographic protocol to ensure it adheres to key security properties. The team aimed to prove that the compiled code maintains security even when devices are temporarily compromised, effectively closing the gap between design and implementation.

## Action
The researchers developed AlphaProof Code, a multi-LLM agentic framework that partitions the verification process between human experts and AI. The workflow includes:

*   **Translation:** Human experts collaborate with AI models to translate Signal’s security requirements into formal mathematical specifications.
*   **Automated Proof Generation:** AI agents generate the necessary proofs using Lean, a language designed for mathematical theorem proving. 
*   **Audit and Review:** Agents identify specific code segments requiring human oversight. This targeted approach allowed experts to focus on only one percent of the codebase, while Lean automatically validated the remainder.

The system uses Gemini Carbon as the underlying engine to handle the complexity of translating live code into valid Lean theorems. To validate the framework, the team reintroduced two previously fixed bugs into the code; the system successfully generated proofs confirming that the buggy versions were insecure.

## Result
The process reduced the verification timeline from years to just four weeks. According to the company, this marks the first time a widely deployed cryptographic protocol has been formally verified at the implementation level. While this demonstrates that AI can handle complex, deep-level verification, scaling these techniques to other systems like medical device firmware or power grid software remains an ongoing research challenge. Google DeepMind has open-sourced their formal verification artifacts. Developers interested in high-assurance systems should review the technical paper and the provided artifacts to see how Lean can be integrated into their own security audits.

## My take

TODO(nilay): add 2-4 sentences from your own experience or opinion, then delete this line.

## Sources

- [Formal Verification of Signal’s Protocol with Gemini](https://deepmind.google/blog/introducing-alphaproof-code/) (Google DeepMind)
