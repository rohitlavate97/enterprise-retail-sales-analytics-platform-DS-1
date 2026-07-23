"""Production Data Pipeline Orchestrator.

Ties together all pipeline stages into a single runnable flow:
Load -> Validate & Quarantine -> Deduplicate -> Handle Nulls -> Detect Outliers -> Optimize.
"""

import sys
from pathlib import Path
from typing import Any

# Ensure root workspace is on python path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config.settings import get_settings
from core.logging import get_logger
from pipelines.base import stage_execution_context
from pipelines.duplicates import DuplicateDetector
from pipelines.loaders import DataLoader
from pipelines.null_handler import NullHandler
from pipelines.optimizer import MemoryOptimizer
from pipelines.outliers import OutlierDetector
from pipelines.validation import SchemaValidator

logger = get_logger(__name__)


class DataPipelineOrchestrator:
    """Production orchestrator executing end-to-end data ETL & quality pipeline."""

    def __init__(
        self,
        raw_dir: Path | str | None = None,
        processed_dir: Path | str | None = None,
    ) -> None:
        settings = get_settings()
        self.raw_dir = Path(raw_dir) if raw_dir else settings.data.raw_dir
        self.processed_dir = Path(processed_dir) if processed_dir else settings.data.processed_dir
        self.processed_dir.mkdir(parents=True, exist_ok=True)

        self.validator = SchemaValidator()
        self.outlier_detector = OutlierDetector()

    def run_pipeline(self) -> dict[str, Any]:
        """Runs complete end-to-end pipeline across raw data tables.

        Returns:
            Dictionary containing processed DataFrames and data quality summaries.
        """
        logger.info("Starting Data Pipeline execution...")

        # 1. Load Raw Datasets
        with stage_execution_context("1. Load Raw Datasets"):
            orders_path = self.raw_dir / "orders.parquet"
            if not orders_path.exists():
                orders_path = self.raw_dir / "orders.csv"
            raw_orders = DataLoader.load_pandas(orders_path)

        # 2. Schema Validation & Quarantine
        with stage_execution_context("2. Schema Validation & Quarantine"):
            clean_orders, quarantined_orders, validation_summary = self.validator.validate_orders(
                raw_orders
            )

        # 3. Deduplication
        with stage_execution_context("3. Deduplication"):
            dedup_orders, _ = DuplicateDetector.deduplicate(clean_orders, subset=["order_id"])

        # 4. Explicit Null Handling Strategy
        with stage_execution_context("4. Per-Column Null Handling"):
            null_strategies: dict[str, dict[str, Any]] = {
                "order_id": {"action": "drop"},
                "customer_id": {"action": "drop"},
                "discount_amount": {"action": "fill_value", "value": 0.0},
                "profit_amount": {"action": "impute_median"},
            }
            null_handler = NullHandler(null_strategies)
            null_cleaned_orders = null_handler.process(dedup_orders)

        # 5. Outlier Detection & Treatment
        with stage_execution_context("5. Outlier Detection"):
            outlier_treated_orders, _ = self.outlier_detector.detect_iqr(
                null_cleaned_orders, column="total_amount", action="flag"
            )

        # 6. Memory Optimization Pass
        with stage_execution_context("6. Memory Optimization Pass"):
            optimized_orders, memory_report = MemoryOptimizer.optimize(outlier_treated_orders)

        # 7. Save Processed Dataset
        with stage_execution_context("7. Save Processed Parquet"):
            output_path = self.processed_dir / "orders_processed.parquet"
            optimized_orders.to_parquet(output_path, index=False)
            logger.info("Saved processed orders dataset to %s", output_path)

        pipeline_report = {
            "validation": validation_summary,
            "memory": memory_report,
            "processed_rows": len(optimized_orders),
            "quarantined_rows": len(quarantined_orders),
        }

        logger.info("Data Pipeline executed successfully.")
        return pipeline_report


def main() -> None:
    """CLI entry point for running the data pipeline."""
    orchestrator = DataPipelineOrchestrator()
    report = orchestrator.run_pipeline()
    saved = report["memory"]["savings_mb"]
    pct = report["memory"]["reduction_percent"]
    print("Pipeline Execution Report:")
    print(f"  Processed Rows: {report['processed_rows']:,}")
    print(f"  Quarantined Rows: {report['quarantined_rows']:,}")
    print(f"  RAM Saved: {saved} MB ({pct}%)")


if __name__ == "__main__":
    main()
