# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

### Added
- Completed Phase 4 NumPy KPI & Statistical Layer (`v0.4-numpy-kpis`):
  - Vectorized business KPI calculator: revenue, profit margin, gross margin, YoY growth, AOV, discount depth, return rate (`analytics/kpi_calculator.py`).
  - Rolling statistics engine: SMA, EMA, WMA, rolling std, rolling min/max, cumulative sum, cumulative growth rate (`analytics/rolling_stats.py`).
  - Statistical analyzer: z-score, min-max, robust normalization, Pearson correlation, correlation/covariance matrices, full descriptive statistics with skewness/kurtosis (`analytics/statistical.py`).
  - NumPy vectorization vs Python loop benchmark (47x–379x measured speedups) (`scripts/benchmark_numpy.py` → `docs/benchmarks/numpy_vectorization.md`).
  - Hot-path optimization benchmark with before/after measurements (`scripts/benchmark_hot_paths.py` → `docs/benchmarks/hot_path_optimizations.md`).
  - 24 correctness tests verifying KPI, rolling, and statistical computations against hand-calculated fixtures (`tests/test_numpy_kpis.py`).
  - NumPy usage rationale documentation (`docs/numpy_rationale.md`).

- Completed Phase 3 Data Pipeline (`v0.3-data-pipeline`):
  - Ingestion module supporting CSV and Parquet formats in both Pandas and Polars with format trade-off documentation (`pipelines/loaders.py`).
  - Schema validator quarantining invalid records to `data/quarantine/` (`pipelines/validation.py`).
  - Duplicate detection and deduplication stage (`pipelines/duplicates.py`).
  - Per-column explicit missing value strategies (`pipelines/null_handler.py`).
  - Statistical outlier detection module with IQR and Z-score methods (`pipelines/outliers.py`).
  - Memory optimization pass downcasting numeric types and converting string columns to categories (`pipelines/optimizer.py`), achieving 64% RAM reduction (14.04 MB -> 5.05 MB).
  - Pipeline stage abstractions and context manager exception handling (`pipelines/base.py`).
  - Master pipeline orchestrator (`pipelines/run_pipeline.py`) outputting cleaned datasets to `data/processed/orders_processed.parquet`.
  - Head-to-head Pandas vs. Polars benchmark script (`scripts/benchmark_pipeline.py`) and report (`docs/benchmarks/pandas_vs_polars.md`) showing Polars up to 330x faster on file load and 26x faster on joins.
  - Comprehensive unit test suite for all pipeline stages (`tests/test_pipeline.py`).
  - Pipeline architecture flow diagram and quality rules documentation (`docs/pipeline_architecture.md`).

- Phase 2 Synthetic Dataset Generator (`v0.2-data-generator`):
  - Seeded relational generator for Customers, Products, Stores, Regions, Time Dimension, Orders, Returns, Discounts, Shipping.

- Phase 1 Project Setup (`v0.1-project-setup`):
  - Directory skeleton, Pydantic Settings config, structured logging, Docker setup, CI workflow.
