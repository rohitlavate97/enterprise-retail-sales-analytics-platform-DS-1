"""Head-to-head Pandas vs. Polars benchmark suite.

Benchmarks real analytics operations on production-scale data (100,000+ orders)
and writes comparative results to docs/benchmarks/pandas_vs_polars.md.
"""

import sys
import time
import tracemalloc
from pathlib import Path
from typing import Any

import pandas as pd
import polars as pl

# Ensure root workspace is on python path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.logging import get_logger
from data.generators.orchestrator import DatasetOrchestrator

logger = get_logger("scripts.benchmark_pipeline")


def run_benchmarks() -> None:
    raw_dir = Path("data/raw")

    # Ensure dataset exists, generate if needed
    orders_path = raw_dir / "orders.parquet"
    cust_path = raw_dir / "customers.parquet"

    if not (orders_path.exists() and cust_path.exists()):
        logger.info("Raw dataset missing. Generating 100,000 orders for benchmark...")
        orchestrator = DatasetOrchestrator(seed=42)
        _ = orchestrator.generate_all(num_orders=100000, num_customers=10000)

    results: list[dict[str, Any]] = []

    # 1. File Ingestion (Parquet Load)
    tracemalloc.start()
    t0 = time.perf_counter()
    df_pd_orders = pd.read_parquet(orders_path)
    df_pd_cust = pd.read_parquet(cust_path)
    pd_load_time = time.perf_counter() - t0
    _, pd_load_mem = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    tracemalloc.start()
    t0 = time.perf_counter()
    df_pl_orders = pl.read_parquet(orders_path)
    df_pl_cust = pl.read_parquet(cust_path)
    pl_load_time = time.perf_counter() - t0
    _, pl_load_mem = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    results.append(
        {
            "operation": "1. File Load (Parquet)",
            "pandas_time_s": round(pd_load_time, 4),
            "polars_time_s": round(pl_load_time, 4),
            "speedup": round(pd_load_time / max(pl_load_time, 1e-6), 2),
            "pandas_mem_mb": round(pd_load_mem / (1024 * 1024), 2),
            "polars_mem_mb": round(pl_load_mem / (1024 * 1024), 2),
        }
    )

    # 2. Predicate Filter
    tracemalloc.start()
    t0 = time.perf_counter()
    _ = df_pd_orders[(df_pd_orders["total_amount"] > 100.0) & (df_pd_orders["quantity"] >= 2)]
    pd_filter_time = time.perf_counter() - t0
    _, pd_filter_mem = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    tracemalloc.start()
    t0 = time.perf_counter()
    _ = df_pl_orders.filter((pl.col("total_amount") > 100.0) & (pl.col("quantity") >= 2))
    pl_filter_time = time.perf_counter() - t0
    _, pl_filter_mem = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    results.append(
        {
            "operation": "2. Predicate Filter",
            "pandas_time_s": round(pd_filter_time, 4),
            "polars_time_s": round(pl_filter_time, 4),
            "speedup": round(pd_filter_time / max(pl_filter_time, 1e-6), 2),
            "pandas_mem_mb": round(pd_filter_mem / (1024 * 1024), 2),
            "polars_mem_mb": round(pl_filter_mem / (1024 * 1024), 2),
        }
    )

    # 3. GroupBy Aggregation
    tracemalloc.start()
    t0 = time.perf_counter()
    _ = (
        df_pd_orders.groupby("store_id")
        .agg(
            total_revenue=("total_amount", "sum"),
            total_profit=("profit_amount", "sum"),
            avg_quantity=("quantity", "mean"),
        )
        .reset_index()
    )
    pd_grp_time = time.perf_counter() - t0
    _, pd_grp_mem = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    tracemalloc.start()
    t0 = time.perf_counter()
    _ = df_pl_orders.group_by("store_id").agg(
        pl.col("total_amount").sum().alias("total_revenue"),
        pl.col("profit_amount").sum().alias("total_profit"),
        pl.col("quantity").mean().alias("avg_quantity"),
    )
    pl_grp_time = time.perf_counter() - t0
    _, pl_grp_mem = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    results.append(
        {
            "operation": "3. GroupBy Aggregation",
            "pandas_time_s": round(pd_grp_time, 4),
            "polars_time_s": round(pl_grp_time, 4),
            "speedup": round(pd_grp_time / max(pl_grp_time, 1e-6), 2),
            "pandas_mem_mb": round(pd_grp_mem / (1024 * 1024), 2),
            "polars_mem_mb": round(pl_grp_mem / (1024 * 1024), 2),
        }
    )

    # 4. Relational Join
    tracemalloc.start()
    t0 = time.perf_counter()
    _ = pd.merge(df_pd_orders, df_pd_cust, on="customer_id", how="inner")
    pd_join_time = time.perf_counter() - t0
    _, pd_join_mem = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    tracemalloc.start()
    t0 = time.perf_counter()
    _ = df_pl_orders.join(df_pl_cust, on="customer_id", how="inner")
    pl_join_time = time.perf_counter() - t0
    _, pl_join_mem = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    results.append(
        {
            "operation": "4. Relational Join",
            "pandas_time_s": round(pd_join_time, 4),
            "polars_time_s": round(pl_join_time, 4),
            "speedup": round(pd_join_time / max(pl_join_time, 1e-6), 2),
            "pandas_mem_mb": round(pd_join_mem / (1024 * 1024), 2),
            "polars_mem_mb": round(pl_join_mem / (1024 * 1024), 2),
        }
    )

    # Output Markdown Documentation Artifact
    doc_dir = Path("docs/benchmarks")
    doc_dir.mkdir(parents=True, exist_ok=True)
    md_path = doc_dir / "pandas_vs_polars.md"

    header = (
        "| Operation | Pandas Time (s) | Polars Time (s) | Polars Speedup "
        "| Pandas RAM (MB) | Polars RAM (MB) |"
    )
    separator = "| :--- | :--- | :--- | :--- | :--- | :--- |"

    md_lines = [
        "# Pandas vs. Polars Performance Benchmark Results\n",
        "Benchmarked on 100,000 orders fact table + 10,000 customers dimension table.\n",
        header,
        separator,
    ]

    for r in results:
        op = r["operation"]
        pd_t = r["pandas_time_s"]
        pl_t = r["polars_time_s"]
        sp = r["speedup"]
        pd_m = r["pandas_mem_mb"]
        pl_m = r["polars_mem_mb"]
        row_str = f"| **{op}** | {pd_t}s | {pl_t}s | **{sp}x** | {pd_m} MB | {pl_m} MB |"
        md_lines.append(row_str)

    with open(md_path, "w", encoding="utf-8") as file_handle:
        file_handle.write("\n".join(md_lines) + "\n")

    logger.info("Benchmark report successfully written to %s", md_path)


if __name__ == "__main__":
    run_benchmarks()
