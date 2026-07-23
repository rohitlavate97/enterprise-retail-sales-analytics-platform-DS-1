# NumPy Vectorization vs Python Loop Benchmark

Benchmarked on 200,000 element arrays, median of 5 runs.

| Operation | Python Loop (s) | NumPy (s) | Speedup |
| :--- | :--- | :--- | :--- |
| **Revenue Calculation** | 0.066974s | 0.001033s | **64.8x** |
| **Profit Margin %** | 0.071723s | 0.001525s | **47.0x** |
| **Z-Score Normalization** | 0.100797s | 0.001861s | **54.2x** |
| **7-Day Moving Average** | 0.225262s | 0.000595s | **378.8x** |
| **Pearson Correlation** | 0.181843s | 0.003117s | **58.3x** |

> All speedups are measured, not asserted.
