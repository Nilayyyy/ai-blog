---
title: "Kitesurf, Cloudflare's agent browser, is now open source"
description: "Cloudflare open-sourced Kitesurf, a browser engine for agents that runs on Workers without a browser container, under Apache 2.0."
pubDate: 2026-11-14
tags: ["cloudflare", "browser", "agents", "open-source", "webassembly", "ai-radar"]
kind: radar
sources: ["https://blog.cloudflare.com/kitesurf-open-source/"]
canonical:
---

Kitesurf, Cloudflare's browser for AI agents, parses HTML, applies CSS, runs page JavaScript and renders screenshots entirely on Workers, with no browser container. As of now the code is on GitHub under Apache 2.0, and you can run it on your laptop with four commands.

The more interesting part is what it is not: a stripped-down Chromium. It is a different engine, assembled from Rust libraries compiled to WebAssembly.

```diagram
{
  "type": "stack",
  "title": "How Kitesurf is built",
  "caption": "Kitesurf is a new engine from Rust libraries compiled to WebAssembly, not a stripped-down Chromium.",
  "layers": [
    {
      "label": "CDP clients",
      "detail": "Puppeteer or your own agent harness connect via Chrome DevTools Protocol"
    },
    {
      "label": "Kitesurf: Engine, PageScript, Pa",
      "detail": "Engine manages sessions, PageScript runs JavaScript, PageRenderer draws the result"
    },
    {
      "label": "Rust libraries in WebAssembly",
      "detail": "Blitz, Stylo, Boa, Linebender and Krilla handle parsing, CSS, JS, graphics"
    },
    {
      "label": "Dynamic Workers",
      "detail": "Isolated Workers created for pages; Boa runs JS only as fallback"
    },
    {
      "label": "Cloudflare Workers",
      "detail": "Runs everything with no browser container, scaling across the global network"
    }
  ]
}
```

## Situation

Cloudflare introduced Kitesurf in August as a stateless browser for AI agents that runs on top of Workers. In September it followed up with WebMCP support, new APIs and better compatibility. Each time, the company says, it promised to open source the project so developers could run their own browser engine on their own Cloudflare accounts.

Until now, using it meant the managed route: Cloudflare's Browser Run APIs. You could use the hosted thing, but you couldn't read how it worked or change it.

## Task

The company says the goal is a lightweight, efficient browser for agents: one that loads sites, executes JavaScript and interacts with pages while using less CPU and memory than a full browser like Chromium. It should also scale on demand across Cloudflare's global Workers network.

Open sourcing is the second half of that: letting developers inspect the engine and host it themselves.

## Action

Kitesurf builds on Cloudflare's developer platform plus a set of open-source Rust packages compiled to WebAssembly:

- **Blitz** handles HTML parsing, the DOM, layout and painting.
- **Stylo** handles CSS parsing, cascading and computed styles.
- **Boa** runs JavaScript inside WebAssembly, but only as a last resort when JavaScript can't run in Dynamic Workers.
- **Linebender** libraries do text layout and 2D graphics, and **Krilla** generates PDF output.

Those projects keep their own licenses, and the repository's NOTICE file documents them.

Kitesurf itself has three parts. The Engine manages browser sessions and client connections, PageScript runs the page and its JavaScript, and PageRenderer draws the result. The engine, its Rust core, DOM shims, renderer and CLI each live in their own folder under the `packages` directory.

It speaks the Chrome DevTools Protocol, so existing clients such as Puppeteer can connect. The local setup from the post:

```
git clone https://github.com/cloudflare/kitesurf.git
cd kitesurf
pnpm install --frozen-lockfile
pnpm run dev
```

The first build compiles the Rust core and its dependencies, so it takes a while; later builds reuse the cache. Wrangler then starts a dev server at `http://127.0.0.1:8787`. From a Node script, you connect Puppeteer with `puppeteer.connect` and a `browserWSEndpoint` of `ws://127.0.0.1:8787/devtools/browser`. Or you point your own agent harness at the local CDP port.

To deploy, run `pnpm run deploy` from the repository root. That requires a Workers Paid plan, because Kitesurf uses Dynamic Workers to create isolated Workers for pages.

## Result

The post reports no benchmark numbers. The lower CPU and memory use compared with Chromium is the company's stated goal, not a measured result in this announcement. It points to a Web Platform Tests page and benchmarks on the landing page for compatibility and performance updates.

Cloudflare also says plainly that Kitesurf is under heavy development, with work focused on compatibility, reliability and efficiency. Expect gaps on real-world pages. Contributions require opening an issue first and getting vouched for by a maintainer before sending a pull request.

If you build agents, clone it, point a Puppeteer script at the local endpoint, and see which of your target pages render correctly.

## My take

TODO(nilay): add 2-4 sentences from your own experience or opinion, then delete this line.

## Sources

- [Kitesurf is now open source](https://blog.cloudflare.com/kitesurf-open-source/) (Cloudflare)
