# Hot-Path Optimization Benchmark Results

Benchmarked on 200,000 elements, median of 5 runs.

| Optimization | Before (s) | After (s) | Speedup |
| :--- | :--- | :--- | :--- |
| **EMA (list-append vs pre-alloc)** | 0.055725s | 0.071859s | **0.8x** |
| **Rolling Std (naive vs cumsum, 20k)** | 0.205497s | 0.021462s | **9.6x** |
| **Safe Division (loop vs broadcast)** | 0.071867s | 0.001263s | **56.9x** |

> All speedups are measured on this project's data.
