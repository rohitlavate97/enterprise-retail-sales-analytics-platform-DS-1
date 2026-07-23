"""Performance benchmark script for dataset generation scale testing.

Measures memory consumption (tracemalloc) and execution time across multiple scale thresholds
and writes benchmark findings to docs/benchmarks/data_generator.md.
"""

from pathlib import Path
import sys
import time
import tracemalloc

# Ensure root workspace is on python path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.logging import get_logger
from data.generators.orchestrator import DatasetOrchestrator

logger = get_logger("scripts.benchmark_generator")


def run_benchmarks() -> None:
    scales = [10_000, 50_000, 100_000, 250_000]
    results: list[dict[str, float | int]] = []

    doc_dir = Path("docs/benchmarks")
    doc_dir.mkdir(parents=True, exist_ok=True)
    temp_raw = Path("data/raw_benchmark_temp")

    logger.info("Starting Dataset Generation Performance Benchmarks...")

    for num_orders in scales:
        tracemalloc.start()
        start_time = time.perf_counter()

        num_cust = max(1000, num_orders // 10)
        num_prod = max(100, num_orders // 200)

        orchestrator = DatasetOrchestrator(seed=42, output_dir=temp_raw)
        _ = orchestrator.generate_all(
            num_orders=num_orders,
            num_customers=num_cust,
            num_products=num_prod,
            num_stores=20,
        )

        elapsed = time.perf_counter() - start_time
        _, peak_mem = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        peak_mb = peak_mem / (1024 * 1024)
        throughput = num_orders / elapsed

        logger.info(
            "Scale %d orders | Time: %.3fs | Peak Memory: %.2f MB | Throughput: %.0f rows/s",
            num_orders,
            elapsed,
            peak_mb,
            throughput,
        )

        results.append(
            {
                "num_orders": num_orders,
                "elapsed_seconds": round(elapsed, 3),
                "peak_memory_mb": round(peak_mb, 2),
                "throughput_rows_per_sec": round(throughput, 1),
            }
        )

    # Clean up benchmark temp files
    if temp_raw.exists():
        for file_path in temp_raw.glob("*"):
            file_path.unlink()
        temp_raw.rmdir()

    # Generate Markdown documentation artifact
    md_content = ["# Dataset Generator Benchmark Results\n"]
    md_content.append("Benchmark performed across dataset scale thresholds (seed=42).\n")
    md_content.append("| Orders Count | Generation Time (s) | Peak Memory (MB) | Throughput (rows/s) |")
    md_content.append("| :--- | :--- | :--- | :--- |")

    for r in results:
        orders_fmt = f"{r['num_orders']:,}"
        time_fmt = f"{r['elapsed_seconds']}s"
        mem_fmt = f"{r['peak_memory_mb']} MB"
        tput_fmt = f"{r['throughput_rows_per_sec']:,}"
        md_content.append(f"| {orders_fmt} | {time_fmt} | {mem_fmt} | {tput_fmt} |")

    md_path = doc_dir / "data_generator.md"
    with open(md_path, "w", encoding="utf-8") as file_handle:
        file_handle.write("\n".join(md_content) + "\n")

    logger.info("Benchmark report written to %s", md_path)


if __name__ == "__main__":
    run_benchmarks()
