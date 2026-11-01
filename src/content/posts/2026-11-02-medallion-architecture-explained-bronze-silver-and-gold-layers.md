---
title: "Medallion Architecture Explained: Bronze, Silver and Gold Layers"
description: "A plain-English guide to the Medallion Architecture, breaking down how data flows from raw ingestion to clean, business-ready insights."
pubDate: 2026-11-02
tags: [data engineering, lakehouse, data architecture, cloud]
canonical:
---

When companies first adopt cloud storage, the default approach is often to dump everything into a "lake." You end up with raw JSON logs, CSV exports, and event streams sitting in a flat directory structure.

This quickly turns into a "data swamp." Because there is no organization, every person who needs to run a query performs the same repetitive cleaning steps. One person might parse a timestamp as UTC, while another assumes local time. One might filter out null IDs, while another includes them. This leads to inconsistent reporting and unnecessary compute costs.

The medallion architecture solves this by organizing data into three distinct layers. Instead of treating your storage like a junk drawer, you treat it like a pipeline. Data flows from a raw state into a refined state, gaining quality and structure at each step.

## Bronze: The Raw Landing Zone

The Bronze layer is your source of truth. Its primary job is to store data exactly as it arrived from the source. If your web server emits a JSON blob, the Bronze layer contains that exact blob.

You do not modify, clean, or filter data here. If a record arrives with a missing field or a mangled format, you keep it that way. This is intentional. If you discover a bug in your transformation logic later, you need the original raw data to re-run your process. If you had modified the data in the first step, that original information would be lost.

In practice, your Bronze layer contains:
*   Full history of the data.
*   Metadata columns like `ingestion_timestamp` or `source_file_name`.
*   Data in its native format (JSON, Parquet, Avro).

Example: A raw log entry.
```json
{"event_id": "a1b2", "timestamp": "2023-10-27T10:00:00Z", "payload": {"user_id": 123, "action": "click"}}
```

## Silver: Cleaned and Conformed

The Silver layer is where data becomes useful for engineers and data scientists. You move from unstructured blobs to structured, typed tables. 

In this layer, you perform the heavy lifting:
*   **Parsing:** Extracting fields from JSON or XML into columns.
*   **Deduplication:** Removing duplicate events.
*   **Validation:** Ensuring `user_id` is an integer and timestamps follow a consistent format.
*   **Standardization:** Mapping different source names to a common convention.

The goal of Silver is to provide a "single version of the truth." By the time data reaches this layer, it should be clean enough that a developer can write a SQL query against it without worrying about type errors or missing values.

Example: A structured table row.
| event_id | event_time | user_id | action |
| :--- | :--- | :--- | :--- |
| a1b2 | 2023-10-27 10:00:00 | 123 | click |

## Gold: Business-Ready Aggregates

The Gold layer is designed for end-users. This isn't for raw analysis; it is for specific business questions, BI dashboards, or input features for machine learning models. 

While Silver tables are often wide and normalized, Gold tables are typically "denormalized" and optimized for read performance. You might join your user table with your sales table and aggregate the results by region and day. You aren't storing every single event; you are storing the *answers* to the questions the business asks most frequently.

Gold tables are usually project-specific. A marketing team might have a Gold table focused on customer churn, while a finance team has one focused on daily revenue.

Example: An aggregated table for a dashboard.
| date | region | total_active_users | total_revenue |
| :--- | :--- | :--- | :--- |
| 2023-10-27 | North America | 4500 | 12500.50 |

## Why This Pattern Matters

The primary advantage of the medallion architecture is incremental processing. Because each layer is structured as a table, you can write pipelines that only look for new data added since the last run. You don't have to re-process the entire history of your company’s data every time you update a dashboard. You simply process the delta—the new rows—and push them through the pipeline. 

This structure also makes debugging easier. If a dashboard in the Gold layer shows a strange number, you can verify if the issue exists in the Silver layer. If the data in Silver is correct, the bug is in your aggregation logic. If the data in Silver is wrong, you look at the Bronze layer. If the data is correct in Bronze, the issue is in your transformation code. If the data is wrong in Bronze, the issue is upstream at the source.

By separating your concerns into these three layers, you stop treating data as a monolithic pile and start treating it as a reliable product. You gain traceability, performance, and the ability to trust the numbers you show to stakeholders.


