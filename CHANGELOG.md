# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

### Added
- Completed Phase 2 Synthetic Dataset Generator (`v0.2-data-generator`):
  - Strongly-typed Pydantic entity schemas for Customers, Products, Categories, Stores, Regions, Payment Methods, Time Dimension, Orders, Returns, Discounts, and Shipping (`data/generators/schemas.py`).
  - Seeded, reproducible Customer generator with market segment distribution and beta-distributed churn risk scores (`data/generators/customer_generator.py`).
  - Product & Category generator incorporating Pareto popularity weighting ($\alpha=1.16$, 80/20 demand distribution) (`data/generators/product_generator.py`).
  - Store & Region generator with regional demand multipliers and store format sizing (`data/generators/store_generator.py`).
  - Time Dimension generator supporting calendar attributes, weekend flags, and major retail holiday indicators (`data/generators/time_generator.py`).
  - Transactional Order generator maintaining strict referential integrity across all entities with Poisson quantity distributions and gross/net margin calculations (`data/generators/order_generator.py`).
  - Auxiliary generators for order Returns, Discount promo tracking, and Shipping logistics (`data/generators/auxiliary_generator.py`).
  - Dataset generation orchestrator module (`data/generators/orchestrator.py`) and CLI entry point (`scripts/generate_dataset.py`) saving outputs to CSV and Parquet formats in `data/raw/`.
  - Generator performance benchmark script (`scripts/benchmark_generator.py`) and benchmark results documentation (`docs/benchmarks/data_generator.md`) demonstrating ~8,700 rows/s generation throughput.
  - Unit test suite for seed reproducibility, Pareto demand concentration, and relational referential integrity (`tests/test_data_generator.py`).
  - Comprehensive relational ER diagram (Mermaid) and data dictionary documentation (`docs/schemas_and_er.md`).

- Phase 1 Project Setup:
  - Directory skeleton, pinned dependencies in `pyproject.toml`, `.pre-commit-config.yaml`, GitHub Actions CI (`.github/workflows/ci.yml`), Docker containerization (`Dockerfile`, `docker-compose.yml`), Pydantic Settings configuration (`config/settings.py`), structured logging (`core/logging.py`), and test suite.
