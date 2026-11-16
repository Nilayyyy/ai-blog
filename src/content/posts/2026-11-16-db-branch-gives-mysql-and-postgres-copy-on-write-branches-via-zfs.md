---
title: "db-branch gives MySQL and Postgres copy-on-write branches via ZFS"
description: "db-branch, a beta open-source tool, uses ZFS clones to make database branches for AI agents and CI in seconds without copying data."
pubDate: 2026-11-16
tags: ["databases", "zfs", "ai-agents", "ci", "open-source", "ai-radar"]
kind: radar
sources: ["https://github.com/db-branch/db-branch"]
canonical:
---

A new open-source project called db-branch says it can create a branch of a large MySQL or PostgreSQL database in seconds, with nothing copied. It does this with ZFS clones, runs on your own servers, and includes an MCP server so an LLM agent can create, abuse and delete its own branch.

It is in beta, licensed Apache-2.0, and the authors warn that APIs and command-line details may change before 1.0.

```diagram
{
  "type": "flow",
  "title": "How db-branch makes a database branch",
  "caption": "Authors report a PostgreSQL branch in about 0.5 s and MySQL in about 3 s, with 0 bytes copied.",
  "steps": [
    {
      "label": "Load a base",
      "detail": "A ZFS dataset holds a loaded database, e.g. from a dump"
    },
    {
      "label": "Snapshot the base",
      "detail": "A ZFS snapshot freezes the base's current state"
    },
    {
      "label": "Clone the snapshot",
      "detail": "Copy-on-write clone shares blocks, so no data is copied"
    },
    {
      "label": "Run own server",
      "detail": "Each branch runs its own database server on its own port"
    },
    {
      "label": "Route and discard",
      "detail": "Optional ProxySQL routes clients; branches can expire, reset, or be deleted"
    }
  ]
}
```

## Situation

Giving an AI agent a database to work on is awkward. Pointing it at production is a bad idea, and restoring a dump for every experiment is slow once the data is large. CI has the same problem: a database per pull request sounds nice until each one takes a long time to load.

Hosted database services have offered branching for a while. If you run your own MySQL or Postgres on your own hardware, the options are thinner.

## Task

The goal, as the project describes it, is to make a full copy of a large database cheap enough to be disposable. You should be able to test a migration, let an agent loose, or give each pull request its own copy, then break it, reset it, or throw it away. It should work self-hosted, for both MySQL and PostgreSQL.

## Action

The core idea is ZFS copy-on-write. A clone of a snapshot shares its blocks with the original and only stores what changes afterwards, so creating one copies no data.

In db-branch's terms:

- A **base** is a ZFS dataset holding a loaded database, for example one restored from a dump.
- A **branch** is a ZFS clone of a base snapshot. Each branch runs its own database server on its own port.
- **ProxySQL** can optionally route client connections to the right branch, by user name or by a `/*db_branch='name'*/` query comment, so applications keep one address.
- **Clustering** uses Raft across several VMs, sharing bases, branches, settings and users.

The workflow is a handful of commands:

```
db-branch runtime install postgres@18.6
db-branch base create prod --runtime postgres@18.6 --dump prod.sql.gz
db-branch branch create feature-x --base prod --ttl 72h
db-branch branch checkpoint feature-x --name before-migration
db-branch branch restore feature-x before-migration
db-branch branch reset feature-x
db-branch branch delete feature-x
```

`--ttl` expires a branch automatically, `reset` returns it to its creation state, and checkpoints save and restore a running branch's state.

There is also `branch upgrade`, which moves a single branch to a newer engine version (say MySQL 8.0 to 8.4) while the base and other branches stay put. It saves a checkpoint first and rolls back on failure, and `--check-only` previews what the upgrade would run into.

The CLI, REST API, web console and MCP server all share the same API. Engine versions are installed side by side.

## Result

The only numbers come from the authors. On their own 3-node test cluster, they report a PostgreSQL branch ready in about 0.5 s and a MySQL branch in about 3 s, with 0 bytes copied at creation. There are no independent benchmarks, and nothing in the README says how performance holds up under heavy writes or many simultaneous branches.

Requirements are Ubuntu 24.04 or 26.04 LTS and a ZFS pool. On a Mac or Windows machine, the README suggests a Multipass Ubuntu VM with a cloud-init script that loads a small sample MySQL database, though its file-backed pool is not meant for real data. A browser demo at demo.db-branch.com runs entirely in the page and creates nothing real.

If you run self-hosted MySQL or Postgres and have been wondering how to let an agent loose on realistic data, the Multipass setup is a cheap afternoon experiment.

## My take

TODO(nilay): add 2-4 sentences from your own experience or opinion, then delete this line.

## Sources

- [GitHub - db-branch/db-branch: Instant MySQL database branches on ZFS clones, clustered acr](https://github.com/db-branch/db-branch) (Hacker News)
