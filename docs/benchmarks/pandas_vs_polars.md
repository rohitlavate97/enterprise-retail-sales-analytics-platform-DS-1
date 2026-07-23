# Pandas vs. Polars Performance Benchmark Results

Benchmarked on 100,000 orders fact table + 10,000 customers dimension table.

| Operation | Pandas Time (s) | Polars Time (s) | Polars Speedup | Pandas RAM (MB) | Polars RAM (MB) |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **1. File Load (Parquet)** | 5.4782s | 0.0166s | **330.11x** | 3.58 MB | 0.0 MB |
| **2. Predicate Filter** | 0.0163s | 0.0049s | **3.29x** | 5.47 MB | 0.02 MB |
| **3. GroupBy Aggregation** | 0.0208s | 0.0033s | **6.37x** | 1.56 MB | 0.01 MB |
| **4. Relational Join** | 0.1838s | 0.007s | **26.18x** | 11.38 MB | 0.0 MB |
