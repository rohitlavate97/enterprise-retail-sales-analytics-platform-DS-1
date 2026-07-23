# Data Pipeline Architecture & Data Quality Specifications

This document describes the high-performance ETL pipeline architecture and data quality enforcement standards for the Enterprise Retail Sales Analytics Platform.

---

## 🏗️ Pipeline Flow Diagram

```mermaid
flowchart TD
    A[Raw Datasets (data/raw/)] -->|Parquet / CSV| B[DataLoader]
    B --> C[SchemaValidator]
    C -->|Valid Records| D[DuplicateDetector]
    C -->|Malformed Records| Q[Quarantine Store (data/quarantine/)]

    D -->|Clean Unique Records| E[NullHandler]
    D -->|Duplicates Isolated| DQ[Duplicate Audit Log]

    E -->|Resolved Missing Values| F[OutlierDetector]
    F -->|IQR / Z-Score Treated| G[MemoryOptimizer]

    G -->|Downcasted & Categorized| H[Processed Parquet (data/processed/)]
    G --> I[Data Quality & RAM Report]
```

---

## ⚙️ Stage Descriptions & Data Quality Rules

### 1. Ingestion (`pipelines/loaders.py`)
- Reads raw transactional datasets from Parquet or CSV.
- Prefers Parquet columnar ingestion for $10\times - 300\times$ faster I/O speeds and column projection pushdown.

### 2. Schema Validation & Quarantine (`pipelines/validation.py`)
- Enforces strict domain constraints (non-null primary/foreign keys, $qty > 0$, $unit\_price > 0$, $total\_amount \ge 0$).
- Isolates malformed rows into `data/quarantine/<table_name>_quarantine.parquet` without swallowing errors.

### 3. Deduplication (`pipelines/duplicates.py`)
- Detects exact row collisions or primary-key collisions.
- Retains first valid instance and logs duplicate isolation counts.

### 4. Per-Column Null Handling (`pipelines/null_handler.py`)
- Executes explicit, documented strategies per column:
  - `drop`: Removes rows missing critical identifiers.
  - `fill_value`: Replaces nulls with explicit defaults ($0.0$ for discount, `'NONE'` for promo codes).
  - `impute_median` / `impute_mean`: Replaces missing numeric values with column statistics.

### 5. Outlier Detection (`pipelines/outliers.py`)
- **IQR (Interquartile Range)**: Bounds $[Q1 - 1.5 \cdot IQR, Q3 + 1.5 \cdot IQR]$. Best suited for skewed business metrics.
- **Z-Score**: Bounds $[\mu - 3.0 \cdot \sigma, \mu + 3.0 \cdot \sigma]$. Best suited for normally distributed variables.

### 6. Memory Optimization (`pipelines/optimizer.py`)
- Downcasts integer columns (`int64` $\rightarrow$ `uint8`/`int16`/`int32`).
- Downcasts floating point columns (`float64` $\rightarrow$ `float32`).
- Converts low-cardinality string columns to Pandas `category` dtypes.
- Achieves $\sim 64\%$ RAM footprint reduction.
