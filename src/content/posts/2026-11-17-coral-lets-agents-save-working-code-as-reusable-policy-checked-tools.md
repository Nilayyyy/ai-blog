---
title: "Coral lets agents save working code as reusable, policy-checked tools"
description: "Coral, an open-source gateway, has agents write TypeScript against your tools, then saves what works as custom tools that stay under your policy."
pubDate: 2026-11-17
tags: ["agents", "mcp", "open-source", "security", "infrastructure", "ai-radar"]
kind: radar
sources: ["https://github.com/withcoral/coral"]
canonical:
---

Coral is an open-source gateway that lets an agent write a short TypeScript program to use your tools, then save the program as a new custom tool if it worked. The next run calls that tool in one step instead of working it out again. The gateway checks every underlying call against your policy.

The project showed up on Hacker News as a Show HN and drew 208 points. <!-- VERIFY: figure 208 not found in the source text -->

```diagram
{
  "type": "flow",
  "title": "How Coral turns working code into tools",
  "caption": "The agent remembers the route without getting wider access.",
  "steps": [
    {
      "label": "Agent writes program",
      "detail": "Short TypeScript over MCP calls several tools and filters results"
    },
    {
      "label": "Sandboxed run",
      "detail": "Fresh V8 isolate: no network, no credentials, no imports"
    },
    {
      "label": "Policy check",
      "detail": "Each inner call is Allow, Ask or Block; Coral adds credentials"
    },
    {
      "label": "Save as custom tool",
      "detail": "A program that worked becomes a searchable tool beside GitHub, Slack"
    },
    {
      "label": "Reuse in one step",
      "detail": "Next run calls the tool; provider calls inside stay checked"
    }
  ]
}
```

## Situation

Most agent setups with MCP work like this: the agent sees a list of tools, reads their schemas, calls them one at a time, and pushes every raw result through the model's context. Next session, it does it all again.

Access control is usually coarse too. The README points out that most MCP gateways only decide which tools an agent can see. If an agent can call `update_record`, it can update any record in any way that tool allows.

## Task

Coral's authors say they started while building an AI SRE. Investigating an incident meant connecting telemetry and undocumented relationships across many systems. The agent needed broad permissions and a lot of tokens, and it started from scratch the next time.

The goal: let the agent remember the route, without handing it wider access in exchange.

## Action

Coral is a self-hosted gateway written in Rust that sits between agents and the systems they work on. It runs as a desktop app (macOS on Apple silicon, Windows x64, Linux x86_64) or as a shared server via Docker Compose or Kubernetes. The shared server needs an OIDC identity provider, a reverse proxy for TLS, and SQLite or Postgres.

How it works:

- **Code mode.** The agent connects over MCP and writes a short TypeScript program. One program can call several tools, filter the results, and return only what the task needs.
- **Sandboxing.** Each program runs in a fresh V8 isolate with no network access, no credentials and no imports.
- **Policy gate.** Every tool call from inside the program is checked against workspace policy. Coral then adds credentials and forwards the call. Each tool is set to Allow, Ask or Block. By default, read tools run right away and everything else needs approval. An approval shows the exact call and arguments.
- **Custom tools.** When a program works, the agent saves it as a custom tool. It turns up in the same search as provider tools like GitHub, Slack or Datadog. You set Allow, Ask or Block on it like any other tool, and provider calls inside it are still checked.
- **Sharing.** Workspace owners can share custom tools with the team. A provider can be set to use the caller's own account, so teammates share tools without sharing API tokens.
- **Providers.** Pick one from the catalog, or bring your own OpenAPI document or MCP server.

The useful part is that a custom tool is code, so it can carry a rule that Allow and Block cannot. The README's example is `closeStaleTicket`, which changes one field and only on tickets with no activity for 30 days.

Connecting a client is one line, for example `claude mcp add --scope user --transport http coral <your-mcp-url>` for Claude Code.

## Result

The numbers below are the project's own claims, not independent measurements. The README says that across 34 tasks on GitHub, Linear and Slack with Opus 5.5, custom tools cut tokens by 37%, cost by 31% and time by 29%. It also says blind benchmarks of 100 enterprise tasks found agents more accurate and cheaper with Coral than with other MCP gateways, and that a smaller model can reach Opus 5.5 accuracy at Haiku 5.5 cost for many tasks. It claims thousands of developers at more than 450 companies use it.

What the README doesn't settle: how well the sandbox holds up under adversarial programs, how saved tools behave when an upstream API changes, and how much review a shared custom tool needs before a team trusts it. The licence is Apache 2.0, and the README says everything outside Coral Enterprise is in the open-source edition.

To try it, install the desktop app, add one provider such as GitHub, connect your MCP client, and ask for your open pull requests.

## My take

TODO(nilay): add 2-4 sentences from your own experience or opinion, then delete this line.

## Sources

- [GitHub - withcoral/coral: Execution rails for agents. Equip your AI to work with sensitive](https://github.com/withcoral/coral) (Hacker News)
