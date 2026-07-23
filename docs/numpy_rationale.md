# NumPy Usage Rationale: Why Vectorized, Where, and the Measured Speedup

This document explains the engineering decisions behind the NumPy-powered analytics layer, citing measured benchmarks from this project's own codebase.

---

## Why NumPy Vectorization?

Python `for` loops over arrays are inherently slow due to per-element interpreter overhead (bytecode dispatch, dynamic type checking, reference counting). NumPy offloads computation to pre-compiled C/Fortran routines operating on contiguous memory, eliminating that overhead entirely.

**This is not asserted from general knowledge — it is measured on this project's data.**

### Measured Speedups (200,000 elements, median of 5 runs)

| Operation | Python Loop | NumPy Vectorized | Speedup |
| :--- | :--- | :--- | :--- |
| Revenue Calculation | 0.067s | 0.001s | **64.8x** |
| Profit Margin % | 0.072s | 0.002s | **47.0x** |
| Z-Score Normalization | 0.101s | 0.002s | **54.2x** |
| 7-Day Moving Average | 0.225s | 0.001s | **378.8x** |
| Pearson Correlation | 0.182s | 0.003s | **58.3x** |

> Source: [`scripts/benchmark_numpy.py`](../scripts/benchmark_numpy.py) → [`docs/benchmarks/numpy_vectorization.md`](benchmarks/numpy_vectorization.md)

---

## Where NumPy Is Used

### 1. Business KPI Calculations (`analytics/kpi_calculator.py`)

Every KPI is expressed as a single vectorized expression:

```python
# Revenue = quantity * unit_price - discount
revenue = q * p - d  # single NumPy broadcast, no loop

# Safe division with np.where (avoids div-by-zero)
margin = np.where(revenue != 0, (profit / revenue) * 100, 0.0)
```

**Why not Pandas?** KPI formulas are pure element-wise arithmetic on homogeneous numeric arrays. NumPy avoids the overhead of DataFrame indexing, alignment checks, and nullable dtype handling that Pandas introduces. For this workload, NumPy is the right abstraction level.

### 2. Rolling Window Computations (`analytics/rolling_stats.py`)

| Function | Technique | Why NumPy |
| :--- | :--- | :--- |
| SMA | `np.convolve` with uniform kernel | **378x** faster than nested Python loop |
| EMA | Pre-allocated `np.empty` + single pass | Eliminates Python list `.append()` overhead |
| WMA | `np.convolve` with normalized weight kernel | Same O(n) vectorized path as SMA |
| Rolling Std | Cumulative-sum trick via `np.cumsum` | **10x** faster than naive window recalculation |

### 3. Statistical Analysis (`analytics/statistical.py`)

| Function | NumPy API Used | Business Application |
| :--- | :--- | :--- |
| Z-Score | `arr.mean()`, `arr.std()`, broadcasting | Normalize revenue distributions for cross-store comparison |
| Min-Max | `arr.min()`, `arr.max()`, broadcasting | Scale metrics to [0, 1] for ML feature engineering |
| Robust Norm | `np.percentile`, `np.median` | Outlier-resistant normalization for skewed price data |
| Pearson r | `np.corrcoef` | Measure price-demand elasticity, discount-revenue correlation |
| Corr Matrix | `np.corrcoef` on stacked arrays | Multi-variable correlation heatmaps for dashboards |
| Descriptive | `np.mean`, `np.median`, `np.var`, manual skew/kurt | Automated data quality profiling per metric |

---

## Hot-Path Optimization Results

Three specific optimizations were benchmarked with before/after measurements:

| Optimization | Before | After | Speedup |
| :--- | :--- | :--- | :--- |
| Rolling Std (naive window → cumsum trick) | 0.205s | 0.021s | **9.6x** |
| Safe Division (Python loop → np.where broadcast) | 0.072s | 0.001s | **56.9x** |
| EMA (list-append → pre-alloc ndarray) | 0.056s | 0.072s | 0.8x (no gain) |

> The EMA result is instructive: the bottleneck is the sequential recurrence, not the data structure. This demonstrates the importance of benchmarking rather than assuming.

> Source: [`scripts/benchmark_hot_paths.py`](../scripts/benchmark_hot_paths.py) → [`docs/benchmarks/hot_path_optimizations.md`](benchmarks/hot_path_optimizations.md)

---

## Design Principles

1. **Measure, don't assert.** Every performance claim is backed by a timed comparison in the codebase.
2. **Right tool for the job.** NumPy for homogeneous numeric computation; Pandas for heterogeneous tabular operations; Polars for I/O-bound and parallel workloads.
3. **Safe division everywhere.** `np.where` + `np.errstate` pattern prevents NaN/Inf propagation in production KPI pipelines.
4. **Accept both NumPy and Pandas.** All analytics functions use `np.asarray()` to transparently accept Pandas Series, ensuring composability across layers.
