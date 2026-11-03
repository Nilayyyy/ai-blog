---
title: "RAG in Practice: Chunking, Embeddings and Retrieval Without the Hype"
description: "A practical guide to building retrieval-augmented generation pipelines by focusing on data chunking, vector embeddings, and evaluation."
pubDate: 2026-11-03
tags: [rag, llm, cloud, vector-databases, data-engineering]
canonical:
---

Retrieval-Augmented Generation (RAG) is often framed as a simple pipeline: grab text, turn it into vectors, and shove it into an LLM. In practice, the gap between a prototype and a functional system is defined by data quality and retrieval precision. If your context is noisy or incomplete, your LLM will provide irrelevant answers regardless of the model architecture.

## The Reality of Chunking

Most developers start with a fixed-size window, splitting text into 500-token blocks with a 50-token overlap. This is easy to implement, but it frequently destroys the semantic integrity of your data. If a split happens in the middle of a sentence or between a header and its corresponding paragraph, the embedding model loses the surrounding context needed to generate a meaningful vector.

Instead of fixed windows, look at the structure of your documents. If you are using Markdown or HTML, use headers as natural boundaries. A chunk should represent a single logical idea. If a section is too long, split it recursively by paragraph, but keep the header as metadata attached to each resulting chunk. This ensures that when a user searches for a concept, the retriever returns a chunk that carries the context of where that information originated.

## Choosing an Embedding Model

There is a temptation to chase the highest score on the MTEB leaderboard. While these scores provide a baseline, they rarely predict how a model will perform on your specific domain data. A model trained on general web-crawled text may perform poorly on specialized medical, legal, or technical documentation. <!-- VERIFY: check current state of MTEB benchmarks -->

The most effective approach is to build a small evaluation set. Create 50 to 100 questions your users might ask and manually identify the specific chunks that contain the correct answers. Run these queries against a few candidate models and measure the "top-k" accuracy—how often the correct chunk appears in the top results. If a smaller model consistently retrieves the right data for your domain, there is no technical reason to pay for a larger, more general model.

## Retrieval Strategies

Simple cosine similarity is a fine starting point, but it often fails on keyword-heavy queries. If a user searches for a specific error code or product ID, semantic search might find documents that are "conceptually related" but lack the specific string requested.

This is why hybrid search is standard practice. You combine dense vector search (semantic) with sparse retrieval (like BM25). By ranking results from both and using a re-ranking model—a smaller model designed to score the relevance of retrieved chunks to the user's query—you can significantly improve precision. Furthermore, never underestimate metadata filtering. If your system knows the user is only interested in "2024 documentation," use that metadata to filter the index before performing the vector search. This narrows the search space and prevents the retriever from surfacing irrelevant, outdated documents.

## Common Failure Modes

Even with a perfect retriever, the LLM can still fail. One common issue is the "lost in the middle" phenomenon. LLMs often prioritize information at the very beginning and very end of their input context, treating the middle as noise. If you feed an LLM ten chunks, place the most critical information at the start or end of the prompt.

Another failure mode is "context stuffing." Providing as much data as possible increases the likelihood that the model will focus on the wrong information. If your retrieval system returns five chunks, but only one is relevant, you are distracting the LLM. You need a way to discard low-relevance chunks before they reach the generation stage. If a retrieved chunk has a low similarity score, do not pass it to the prompt.

## Evaluation Without Guesswork

Evaluation is the most skipped step in RAG development. You cannot rely on "it looks right" during manual testing. You need a quantitative feedback loop.

Start by measuring two metrics: retrieval precision (did we find the right chunks?) and generation accuracy (did the LLM synthesize them correctly?). You can automate the retrieval check by using a secondary LLM as a grader. Give the grader the user query and the retrieved chunks, and ask it to output a boolean value: *Does this set of chunks contain the information required to answer the user's question?*

Build a dashboard that tracks this metric every time you change your chunking strategy or embedding model. If your precision drops, you know your retrieval pipeline has drifted. By separating retrieval evaluation from generation evaluation, you stop guessing why a prompt failed. You can see clearly if the error was a failure to find the right data or a failure of the LLM to synthesize the data you provided.

## My take

TODO(nilay): add 2-4 sentences from your own experience or opinion, then delete this line.

