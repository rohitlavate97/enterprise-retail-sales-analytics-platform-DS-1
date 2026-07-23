"""NumPy vectorization vs. Python loop benchmark suite.

Benchmarks identical computations implemented via pure-Python
loops and via NumPy vectorized operations on 100,000+ element
arrays, producing a markdown report with measured speedup factors.
"""

import sys
import time
from pathlib import Path
from typing import Any

import numpy as np

# Ensure root workspace is on python path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.logging import get_logger

logger = get_logger("scripts.benchmark_numpy")

NUM_ELEMENTS = 200_000
NUM_ITERATIONS = 5


def _median_time(times: list[float]) -> float:
    """Return the median of a list of timing measurements."""
    s = sorted(times)
    n = len(s)
    if n % 2 == 1:
        return s[n // 2]
    return (s[n // 2 - 1] + s[n // 2]) / 2


# ── Benchmark helpers ──────────────────────────────────────────


def bench_revenue_loop(qty: np.ndarray, price: np.ndarray, disc: np.ndarray) -> float:
    """Revenue calc via Python loop."""
    times: list[float] = []
    for _ in range(NUM_ITERATIONS):
        t0 = time.perf_counter()
        result = [0.0] * len(qty)
        for i in range(len(qty)):
            result[i] = qty[i] * price[i] - disc[i]
        times.append(time.perf_counter() - t0)
    return _median_time(times)


def bench_revenue_numpy(qty: np.ndarray, price: np.ndarray, disc: np.ndarray) -> float:
    """Revenue calc via NumPy vectorization."""
    times: list[float] = []
    for _ in range(NUM_ITERATIONS):
        t0 = time.perf_counter()
        _ = qty * price - disc
        times.append(time.perf_counter() - t0)
    return _median_time(times)


def bench_margin_loop(profit: np.ndarray, revenue: np.ndarray) -> float:
    """Profit margin via Python loop."""
    times: list[float] = []
    for _ in range(NUM_ITERATIONS):
        t0 = time.perf_counter()
        result = [0.0] * len(profit)
        for i in range(len(profit)):
            if revenue[i] != 0:
                result[i] = (profit[i] / revenue[i]) * 100
        times.append(time.perf_counter() - t0)
    return _median_time(times)


def bench_margin_numpy(profit: np.ndarray, revenue: np.ndarray) -> float:
    """Profit margin via NumPy where."""
    times: list[float] = []
    for _ in range(NUM_ITERATIONS):
        t0 = time.perf_counter()
        _ = np.where(revenue != 0, (profit / revenue) * 100, 0.0)
        times.append(time.perf_counter() - t0)
    return _median_time(times)


def bench_zscore_loop(arr: np.ndarray) -> float:
    """Z-score normalization via Python loop."""
    times: list[float] = []
    for _ in range(NUM_ITERATIONS):
        t0 = time.perf_counter()
        total = 0.0
        for v in arr:
            total += v
        mean = total / len(arr)
        sq_sum = 0.0
        for v in arr:
            sq_sum += (v - mean) ** 2
        std = (sq_sum / len(arr)) ** 0.5
        result = [0.0] * len(arr)
        for i in range(len(arr)):
            result[i] = (arr[i] - mean) / std if std else 0.0
        times.append(time.perf_counter() - t0)
    return _median_time(times)


def bench_zscore_numpy(arr: np.ndarray) -> float:
    """Z-score normalization via NumPy."""
    times: list[float] = []
    for _ in range(NUM_ITERATIONS):
        t0 = time.perf_counter()
        mean = arr.mean()
        std = arr.std()
        _ = (arr - mean) / std if std else np.zeros_like(arr)
        times.append(time.perf_counter() - t0)
    return _median_time(times)


def bench_moving_avg_loop(arr: np.ndarray, window: int) -> float:
    """7-day moving average via Python loop."""
    times: list[float] = []
    for _ in range(NUM_ITERATIONS):
        t0 = time.perf_counter()
        result = [float("nan")] * len(arr)
        for i in range(window - 1, len(arr)):
            total = 0.0
            for j in range(i - window + 1, i + 1):
                total += arr[j]
            result[i] = total / window
        times.append(time.perf_counter() - t0)
    return _median_time(times)


def bench_moving_avg_numpy(arr: np.ndarray, window: int) -> float:
    """7-day moving average via np.convolve."""
    times: list[float] = []
    kernel = np.ones(window) / window
    for _ in range(NUM_ITERATIONS):
        t0 = time.perf_counter()
        _ = np.convolve(arr, kernel, mode="valid")
        times.append(time.perf_counter() - t0)
    return _median_time(times)


def bench_correlation_loop(x: np.ndarray, y: np.ndarray) -> float:
    """Pearson correlation via Python loop."""
    times: list[float] = []
    for _ in range(NUM_ITERATIONS):
        t0 = time.perf_counter()
        n = len(x)
        sum_x = sum_y = sum_xy = sum_x2 = sum_y2 = 0.0
        for i in range(n):
            sum_x += x[i]
            sum_y += y[i]
            sum_xy += x[i] * y[i]
            sum_x2 += x[i] ** 2
            sum_y2 += y[i] ** 2
        num = n * sum_xy - sum_x * sum_y
        den = ((n * sum_x2 - sum_x**2) * (n * sum_y2 - sum_y**2)) ** 0.5
        _ = num / den if den else 0.0
        times.append(time.perf_counter() - t0)
    return _median_time(times)


def bench_correlation_numpy(x: np.ndarray, y: np.ndarray) -> float:
    """Pearson correlation via np.corrcoef."""
    times: list[float] = []
    for _ in range(NUM_ITERATIONS):
        t0 = time.perf_counter()
        _ = np.corrcoef(x, y)[0, 1]
        times.append(time.perf_counter() - t0)
    return _median_time(times)


# ── Main ───────────────────────────────────────────────────────


def run_benchmarks() -> None:
    """Execute all benchmarks and write report."""
    rng = np.random.default_rng(42)
    qty = rng.integers(1, 20, size=NUM_ELEMENTS).astype(np.float64)
    price = rng.uniform(5.0, 200.0, size=NUM_ELEMENTS)
    disc = rng.uniform(0.0, 10.0, size=NUM_ELEMENTS)
    profit = rng.uniform(1.0, 100.0, size=NUM_ELEMENTS)
    revenue = rng.uniform(10.0, 500.0, size=NUM_ELEMENTS)
    series = rng.uniform(0.0, 1000.0, size=NUM_ELEMENTS)
    x_corr = rng.normal(50, 10, size=NUM_ELEMENTS)
    y_corr = x_corr * 0.8 + rng.normal(0, 5, size=NUM_ELEMENTS)
    window = 7

    results: list[dict[str, Any]] = []

    # 1. Revenue calculation
    t_loop = bench_revenue_loop(qty, price, disc)
    t_np = bench_revenue_numpy(qty, price, disc)
    results.append(
        {
            "op": "Revenue Calculation",
            "loop": t_loop,
            "numpy": t_np,
        }
    )

    # 2. Profit margin
    t_loop = bench_margin_loop(profit, revenue)
    t_np = bench_margin_numpy(profit, revenue)
    results.append(
        {
            "op": "Profit Margin %",
            "loop": t_loop,
            "numpy": t_np,
        }
    )

    # 3. Z-Score normalization
    t_loop = bench_zscore_loop(series)
    t_np = bench_zscore_numpy(series)
    results.append(
        {
            "op": "Z-Score Normalization",
            "loop": t_loop,
            "numpy": t_np,
        }
    )

    # 4. 7-day Moving Average
    t_loop = bench_moving_avg_loop(series, window)
    t_np = bench_moving_avg_numpy(series, window)
    results.append(
        {
            "op": "7-Day Moving Average",
            "loop": t_loop,
            "numpy": t_np,
        }
    )

    # 5. Pearson Correlation
    t_loop = bench_correlation_loop(x_corr, y_corr)
    t_np = bench_correlation_numpy(x_corr, y_corr)
    results.append(
        {
            "op": "Pearson Correlation",
            "loop": t_loop,
            "numpy": t_np,
        }
    )

    # Print table
    print(
        f"\nNumPy vs Python Loop Benchmark"
        f" ({NUM_ELEMENTS:,} elements,"
        f" median of {NUM_ITERATIONS} runs)\n"
    )
    header = f"{'Operation':<25}{'Loop (s)':>12}{'NumPy (s)':>12}{'Speedup':>10}"
    print(header)
    print("-" * len(header))
    for r in results:
        sp = r["loop"] / max(r["numpy"], 1e-9)
        print(f"{r['op']:<25}{r['loop']:>12.6f}{r['numpy']:>12.6f}{sp:>9.1f}x")

    # Write markdown report
    doc_dir = Path("docs/benchmarks")
    doc_dir.mkdir(parents=True, exist_ok=True)
    md_path = doc_dir / "numpy_vectorization.md"

    lines = [
        "# NumPy Vectorization vs Python Loop Benchmark\n",
        (f"Benchmarked on {NUM_ELEMENTS:,} element arrays, median of {NUM_ITERATIONS} runs.\n"),
        ("| Operation | Python Loop (s) | NumPy (s) | Speedup |"),
        "| :--- | :--- | :--- | :--- |",
    ]

    for r in results:
        sp = r["loop"] / max(r["numpy"], 1e-9)
        lines.append(f"| **{r['op']}** | {r['loop']:.6f}s | {r['numpy']:.6f}s | **{sp:.1f}x** |")

    lines.append("")
    lines.append("> All speedups are measured, not asserted.")

    with open(md_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

    logger.info("Benchmark report written to %s", md_path)


if __name__ == "__main__":
    run_benchmarks()
