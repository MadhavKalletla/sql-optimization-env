---
title: SQL Optimization RL Environment
emoji: 🗄️
colorFrom: blue
colorTo: green
sdk: docker
app_port: 7860
tags:
  - openenv
  - sql
  - rl
  - optimization
---

# 🗄️ SQL Query Optimization RL Environment

An **OpenEnv-compliant Reinforcement Learning environment** for training agents to automatically optimize SQL queries on **real-world Indian government-scale datasets**.

---

## 🚀 Why This Project?

Modern databases often suffer from:
- Slow queries due to poor indexing
- Inefficient joins and anti-patterns
- High latency on large-scale datasets

This environment enables:
👉 Training AI agents to **detect and fix SQL inefficiencies automatically**  
👉 Benchmarking query optimization strategies in a **realistic setting**

---

## 🏛️ Data Domains (Realistic Scale)

| Domain  | Tables | Description |
|---------|--------|-------------|
| **GST** | `gst_invoice_records`, `gst_invoice_items` | B2B invoices, HSN items, tax splits |
| **PDS** | `ration_card_beneficiaries`, `pds_allotments` | Ration distribution system |
| **Railway** | `railway_trains`, `railway_pnr_bookings` | Ticket booking workloads |
| **MGNREGA** | `mgnrega_workers`, `mgnrega_attendance`, `mgnrega_payments` | Rural employment data |

---

## 🎯 Task Design (9 Tasks × 5 Levels)

| Level | Tasks | Anti-Patterns |
|-------|-------|---------------|
| 1 Intro | `pds_select_star` | SELECT_STAR |
| 2 Easy | `gst_missing_index`, `railway_simple_filter` | MISSING_INDEX |
| 3 Medium | `gst_n_plus_one`, `pds_cartesian`, `mgnrega_wildcard` | N+1, CARTESIAN, WILDCARD |
| 4 Hard | `gst_multi_join`, `railway_tatkal_workload` | Multi-pattern |
| 5 Expert | `mgnrega_schema_e` | UNBOUNDED_AGG + CAST |

---

## ⚙️ System Architecture

```text
Agent (LLM / RL Policy)
        ↓
   OpenEnv API
        ↓
SQL Execution Engine (SQLite)
        ↓
Execution Plan + Metrics
        ↓
Reward Function (5 factors)