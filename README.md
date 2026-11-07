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

[![Open in Hugging Face Spaces](https://huggingface.co/datasets/huggingface/badges/raw/main/open-in-hf-spaces-sm.svg)](https://huggingface.co/spaces/Kalletlamadhav/sql_optimized_env_new)
[![OpenEnv Compliant](https://img.shields.io/badge/OpenEnv-Compliant-blue.svg)](https://github.com/MadhavKalletla/sql-optimization-env)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

An **OpenEnv-compliant Reinforcement Learning environment** for training agents to automatically optimize SQL queries on **real-world Indian government-scale datasets** (GST, PDS, Railways, and MGNREGA).

---

## 🚀 Why This Project?

Modern relational databases running complex production workloads often suffer from:
- Slow queries due to missing or suboptimal indexes
- Inefficient cartesian products and unnecessary joins
- High latency and excessive resource usage on large-scale datasets
- Query anti-patterns (e.g., `SELECT *`, wildcards, unindexed filters)

This environment provides a standard RL gym interface enabling:
- 🎯 Training AI agents to **detect and fix SQL inefficiencies automatically**  
- 📊 Benchmarking query optimization policies against deterministic cost-based metrics
- 🏆 Progressive curriculum learning from single-table anti-patterns to complex multi-join workloads

---

## 🏛️ Data Domains (Realistic Scale)

| Domain | Tables | Description |
|---|---|---|
| **GST** | `gst_invoice_records`, `gst_invoice_items` | B2B invoices, HSN items, tax splits |
| **PDS** | `ration_card_beneficiaries`, `pds_allotments` | Public distribution and ration distribution system |
| **Railway** | `railway_trains`, `railway_pnr_bookings` | High-frequency ticket booking & Tatkal workloads |
| **MGNREGA** | `mgnrega_workers`, `mgnrega_attendance`, `mgnrega_payments` | Rural employment and worker wage disbursement data |

---

## 🎯 Task Design (9 Tasks × 5 Curriculum Levels)

| Level | Tasks | Primary Anti-Patterns | Focus |
|---|---|---|---|
| **1 Intro** | `pds_select_star` | `SELECT_STAR` | Column pruning & projection |
| **2 Easy** | `gst_missing_index`, `railway_simple_filter` | `MISSING_INDEX` | Index creation & filter selectivity |
| **3 Medium** | `gst_n_plus_one`, `pds_cartesian`, `mgnrega_wildcard` | `N+1`, `CARTESIAN`, `WILDCARD` | Join optimization & prefix indexing |
| **4 Hard** | `gst_multi_join`, `railway_tatkal_workload` | Multi-pattern | Multi-table joins & concurrent workload tuning |
| **5 Expert** | `mgnrega_schema_e` | `UNBOUNDED_AGG` + `CAST` | Aggregation pushdown & type compatibility |

---

## ⚙️ System Architecture

```text
Agent (LLM / RL Policy)
        │
        ▼ (Action: rewrite, indexes, pattern)
   OpenEnv API (FastAPI / REST)
        │
        ▼
SQL Execution Engine (SQLite)
        │
        ▼
Execution Plan + Timing Metrics
        │
        ▼
Reward Function (5 Weighted Factors)
```

### 🏆 5-Factor Reward Function

The environment computes a normalized scalar reward $\in (0.01, 0.99)$ based on:

$$\text{Reward} = 0.35 \cdot R_{\text{speedup}} + 0.25 \cdot R_{\text{equiv}} + 0.20 \cdot R_{\text{pattern}} + 0.10 \cdot R_{\text{index}} + 0.10 \cdot R_{\text{simplicity}}$$

- **Speedup (35%)**: Execution time reduction compared to the unoptimized baseline.
- **Equivalence (25%)**: Semantic parity test verifying row count and column results match ground truth.
- **Pattern Detection (20%)**: Correct identification of the underlying SQL anti-pattern.
- **Index Quality (10%)**: Efficiency and necessity of proposed indexes without bloat.
- **Simplicity (10%)**: Query readability and minimal AST overhead.

---

## 📦 Observation & Action Space

### Observation Space
- `current_query`: Original unoptimized SQL query string
- `goal`: Natural language description of query objective
- `schema_ddl`: Complete schema definitions for relevant tables
- `execution_plan`: Detailed SQLite `EXPLAIN QUERY PLAN` JSON tree
- `execution_time_ms`: Baseline latency measurement
- `curriculum_level`: Current difficulty level (1–5)
- `anti_pattern_hint`: Contextual hint for guided learning

### Action Space
- `optimized_query`: The rewritten, optimized SQL query
- `identified_pattern`: Anti-pattern category label
- `explanation`: Agent reasoning explaining the optimization logic
- `index_statements`: Optional array of `CREATE INDEX` statements

---

## 🛠️ Quickstart & Local Setup

### Option 1: Docker (Recommended)
```bash
# Clone the repository
git clone https://github.com/MadhavKalletla/sql-optimization-env.git
cd sql-optimization-env

# Build and run the container
docker build -t sql-optimization-env .
docker run -p 7860:7860 sql-optimization-env
```
Visit `http://localhost:7860` to access the interactive web interface and API docs (`/docs`).

### Option 2: Python Virtual Environment
```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# Linux/macOS:
source .venv/bin/activate

pip install -r requirements.txt
uvicorn server.main:app --host 0.0.0.0 --port 7860 --reload
```

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
