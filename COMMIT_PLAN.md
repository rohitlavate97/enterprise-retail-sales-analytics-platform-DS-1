# Commit-Wise Development Plan — Enterprise Retail Sales Analytics Platform

This translates the phase roadmap in `retail-analytics-platform-master-prompt-v2.md` into a concrete,
commit-by-commit build order. Each phase = one feature branch. Each numbered item below = one commit
on that branch, in sequence. Nothing in a later commit should be needed by an earlier one.

Conventions used throughout:
- Branch name: `phase-<NN>-<short-name>`
- Commit type prefixes follow Conventional Commits: `feat`, `fix`, `refactor`, `docs`, `test`, `chore`, `perf`, `ci`
- After the last commit on a phase branch: push branch → open PR into `main` → review → merge → tag `main`

---

## Phase 1 — Project Setup
Branch: `phase-01-project-setup` · Tag on merge: `v0.1-project-setup`

1. `chore: scaffold project directory structure and .gitignore`
   Create the full skeleton (`config/`, `core/`, `utils/`, `services/`, `data/{generators,raw,processed}/`,
   `pipelines/`, `analytics/`, `streaming/`, `dashboard/pages/`, `tests/`, `docs/`, `assets/`, `scripts/`,
   `docker/`, `.github/`), each with a `.gitkeep` or `__init__.py`. `.gitignore` excludes `data/raw/`,
   `data/processed/`, `.env`, venvs, `__pycache__`, `.mypy_cache`, build artifacts.
2. `chore: add pyproject.toml with pinned dependencies and tool configuration`
   Dependency list (numpy, pandas, polars, matplotlib, plotly, streamlit, pydantic, pyyaml, pytest, ruff,
   black, mypy), locked versions, Ruff/Black/MyPy config sections.
3. `chore: add pre-commit hooks mirroring CI checks`
   `.pre-commit-config.yaml` running Ruff, Black, MyPy on commit.
4. `ci: add GitHub Actions workflow for lint, type-check, and test`
   `.github/workflows/ci.yml` triggered on push/PR.
5. `chore: add Dockerfile and docker-compose.yml for reproducible environment`
6. `feat: add configuration module (Pydantic Settings + YAML loader)`
   `config/settings.py` — no hardcoded constants going forward; every later module reads from this.
7. `feat: add structured logging setup`
   `core/logging.py` — consistent logger factory used by every pipeline/service from Phase 3 onward.
8. `test: add tests for configuration loading and logging setup`
9. `docs: write initial README and CHANGELOG`
   Project purpose, setup instructions, branching convention. Initialize `CHANGELOG.md`.

**Checkpoint:** push branch, open PR to `main`, review, merge, tag `v0.1-project-setup`.

---

## Phase 2 — Synthetic Dataset Generator
Branch: `phase-02-data-generator` · Tag: `v0.2-data-generator`

1. `feat: define entity schemas for all dataset tables`
   Pydantic models for Customers, Products, Categories, Stores, Regions, Payment Methods, Time Dimension,
   Orders, Returns, Discounts, Shipping — with FK relationships expressed explicitly.
2. `feat: implement customer generator with seeded reproducibility`
3. `feat: implement product & category generator with Pareto-like popularity distribution`
4. `feat: implement store & region generator with regional variance`
5. `feat: implement time dimension generator with seasonality calendar`
6. `feat: implement order generator referencing customers/products/stores/time`
   Seasonality applied to order volume and per-category demand.
7. `feat: implement returns, discounts, and shipping generators referencing orders`
   Realistic per-category return rates, not uniform.
8. `feat: add dataset generation orchestrator script`
   `scripts/generate_dataset.py` — single entry point producing the full relational dataset to `data/raw/`.
9. `perf: benchmark dataset generation time and memory vs. row count`
   Results recorded under `docs/benchmarks/`.
10. `test: add seed-reproducibility and referential-integrity tests`
    Same seed → byte-identical dataset; every FK resolves.
11. `docs: document dataset schema and ER diagram`

**Checkpoint:** push, PR, review, merge, tag `v0.2-data-generator`.

---

## Phase 3 — Data Pipeline
Branch: `phase-03-data-pipeline` · Tag: `v0.3-data-pipeline`

1. `feat: add CSV and Parquet loader with format trade-off documented`
2. `feat: add schema validation with quarantine of malformed rows`
   Pydantic/pandera-based; rejected rows written to a quarantine location, not dropped silently.
3. `feat: add duplicate detection module`
4. `feat: add per-column null-handling strategy`
   Explicit drop/impute/flag decision documented per column — no blanket `fillna(0)`.
5. `feat: add outlier detection (IQR / z-score) per metric`
6. `feat: add type conversion and memory optimization pass`
   Categorical dtypes, numeric downcasting; before/after memory measured and logged.
7. `feat: wire structured logging and exception handling through all pipeline stages`
8. `perf: benchmark Pandas vs. Polars on load, groupby, join, filter at full scale`
   Chart output, not just printed numbers.
9. `feat: add pipeline orchestrator tying stages into one runnable flow`
   `pipelines/run_pipeline.py`.
10. `test: add unit tests per pipeline stage using fixture data`
11. `docs: document pipeline architecture and data-quality report format`

**Checkpoint:** push, PR, review, merge, tag `v0.3-data-pipeline`.

---

## Phase 4 — NumPy KPI & Statistical Layer
Branch: `phase-04-numpy-kpis` · Tag: `v0.4-numpy-kpis`

1. `perf: benchmark vectorization/broadcasting against equivalent Python loop`
2. `feat: implement vectorized business KPI calculations`
   Revenue, margin, YoY growth at scale.
3. `feat: implement moving averages and rolling computations`
4. `feat: implement normalization, standardization, and correlation calculations`
5. `perf: optimize hot paths with before/after benchmarks`
6. `test: add correctness tests for KPI calculations against hand-computed fixtures`
7. `docs: write NumPy usage rationale (why vectorized, where, and the measured speedup)`

**Checkpoint:** push, PR, review, merge, tag `v0.4-numpy-kpis`.

---

## Phase 5 — Pandas Advanced Analytics Layer
Branch: `phase-05-pandas-analytics` · Tag: `v0.5-pandas-analytics`

Each commit is one Pandas capability tied to a specific business question.

1. `feat: add groupby/agg/transform sales aggregation by region and category`
2. `feat: add pivot_table region-by-category sales matrix`
3. `feat: add merge/join-based customer-order-product enrichment views`
4. `feat: add resample-based monthly/weekly revenue rollups`
5. `feat: add rolling/window trailing-KPI functions`
6. `feat: add melt/explode/crosstab reporting utilities`
7. `feat: add MultiIndex and categorical-dtype reporting views`
8. `feat: add custom aggregation functions (weighted averages, cohort-based aggregation)`
9. `test: add correctness tests for each analytics function`
10. `docs: map each Pandas function used to its business question`

**Checkpoint:** push, PR, review, merge, tag `v0.5-pandas-analytics`.

---

## Phase 6 — Polars Advanced Analytics + LazyFrame/Streaming
Branch: `phase-06-polars-analytics` · Tag: `v0.6-polars-analytics`

1. `feat: add LazyFrame-based query layer mirroring the Pandas analytics API`
2. `feat: implement complex transformations via the Expression API`
3. `feat: add streaming execution path for out-of-core dataset scenario`
4. `perf: inspect and document Polars query plan optimization`
5. `perf: demonstrate and measure parallel execution`
6. `perf: run head-to-head Polars vs. Pandas benchmark suite with chart output`
7. `test: add parity tests asserting Polars results match Pandas results`
8. `docs: write Polars usage rationale citing this project's own benchmark numbers`

**Checkpoint:** push, PR, review, merge, tag `v0.6-polars-analytics`.

---

## Phase 7 — Visualization Layer
Branch: `phase-07-visualization` · Tag: `v0.7-visualization`

1. `feat: add Matplotlib static charts (sales trend, revenue, profit)`
2. `feat: add Plotly interactive charts (drill-down, heatmaps)`
3. `feat: add customer segmentation, cohort, and retention visualizations`
4. `feat: add Pareto and ABC analysis visualizations`
5. `feat: add seasonality and forecast visualizations`
6. `feat: add regional and top/bottom product visualizations`
7. `test: add chart-generation smoke tests against fixture data`
8. `docs: map each chart to the business question it answers`

**Checkpoint:** push, PR, review, merge, tag `v0.7-visualization`.

---

## Phase 8 — Real-Time Simulation Layer
Branch: `phase-08-realtime-simulation` · Tag: `v0.8-realtime-simulation`

1. `feat: add simulated live POS/transaction feed generator`
   Background process emitting synthetic orders on a defined interval.
2. `feat: add in-memory live-order buffer`
3. `feat: add incremental aggregation for live KPIs`
   Polars streaming or true incremental aggregation — explicitly not a full batch rerun per tick.
4. `feat: add live KPI service reading from the buffer`
5. `test: add tests for feed generator and incremental aggregation correctness`
6. `docs: document the batch-vs-streaming architectural distinction and its honest limitations`
   States plainly what a real production system would need (Kafka/RabbitMQ, real POS integration).

**Checkpoint:** push, PR, review, merge, tag `v0.8-realtime-simulation`.

---

## Phase 9 — Streamlit Dashboard
Branch: `phase-09-dashboard` · Tag: `v0.9-dashboard-mvp`

1. `feat: scaffold multipage dashboard shell (theme, sidebar filters, session state, mock auth)`
2. `feat: add caching layer with explicit invalidation reasoning`
3. `feat: add Executive Dashboard page`
4. `feat: add Sales Analytics page`
5. `feat: add Customer Analytics page`
6. `feat: add Product Analytics page`
7. `feat: add Regional Analytics page`
8. `feat: add Performance Comparison page (Pandas vs. Polars benchmarks, visual)`
9. `feat: add Data Quality page (validation results, rejected-row summaries)`
10. `feat: add Raw Data Explorer page (search, pagination)`
11. `feat: add Settings and About pages`
12. `feat: add downloadable report export (CSV, Excel, PDF)`
13. `feat: integrate live KPI panel into Executive Dashboard`
14. `test: add dashboard page-render smoke tests`
15. `docs: draft user guide`

**Checkpoint:** push, PR, review, merge, tag `v0.9-dashboard-mvp`.

---

## Phase 10 — Testing Hardening
Branch: `phase-10-testing-hardening` · Tag: `v0.9.1-testing-hardened`

1. `test: close coverage gaps in core/`
2. `test: close coverage gaps in pipelines/`
3. `test: close coverage gaps in analytics/`
4. `test: verify benchmark scripts run cleanly and produce comparison artifacts`
5. `ci: enforce minimum coverage threshold in CI`
6. `docs: write testing strategy document`

**Checkpoint:** push, PR, review, merge, tag `v0.9.1-testing-hardened`.

---

## Phase 11 — Documentation & Interview Section
Branch: `phase-11-documentation` · Tag: `v0.9.9-documentation`

1. `docs: rewrite README to professional standard`
2. `docs: add architecture diagram and data flow diagram`
3. `docs: add ER diagram`
4. `docs: write installation guide`
5. `docs: write developer guide`
6. `docs: finalize user guide`
7. `docs: write Interview Section`
   NumPy/Pandas/Polars rationale with this project's benchmark numbers, memory-optimization
   before/after figures, complexity analysis, business use cases, interview Q&A, real production
   challenges actually hit while building this.

**Checkpoint:** push, PR, review, merge, tag `v0.9.9-documentation`.

---

## Phase 12 — Final Production Polish
Branch: `phase-12-production-polish` · Tag: `v1.0-production-hardening`

1. `perf: profile and optimize remaining hotspots end-to-end`
2. `ci: get CI fully green end-to-end`
3. `docs: write deployment guide`
4. `chore: final dependency audit and version pin review`
5. `chore: final CHANGELOG update and v1.0 release prep`

**Checkpoint:** push, PR, review, merge, tag `v1.0-production-hardening`.

---

## How to Use This Plan Day to Day

- Work one commit at a time, in order, on the current phase branch.
- For every commit, before writing code: state the business objective and the library/architecture
  decision in your own words (per the master prompt's per-commit process) — this plan tells you *what*
  and *in what order*, not the *why*, which you still reason through per commit.
- Don't jump ahead to a later phase's commit even if it looks easy — later phases depend on earlier
  ones being real and tested, not stubbed.
- After each phase's last commit: push the branch, open the PR, review it yourself against the
  Definition of Done checklist in the master prompt, merge, tag.
