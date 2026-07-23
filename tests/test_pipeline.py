"""Unit tests for data pipeline stages and orchestrator.

Tests loaders, schema validation & quarantine, duplicate detection, per-column null strategies,
statistical outlier detection (IQR & Z-score), and memory optimization pass.
"""

from pathlib import Path

import pandas as pd
import pytest

from pipelines.duplicates import DuplicateDetector
from pipelines.loaders import DataLoader
from pipelines.null_handler import NullHandler
from pipelines.optimizer import MemoryOptimizer
from pipelines.outliers import OutlierDetector
from pipelines.run_pipeline import DataPipelineOrchestrator
from pipelines.validation import SchemaValidator


@pytest.fixture
def sample_orders_df() -> pd.DataFrame:
    """Fixture producing a sample orders dataframe with deliberate anomalies."""
    data = {
        "order_id": ["ORD-001", "ORD-002", "ORD-003", "ORD-003", "ORD-005", "ORD-006", None],
        "customer_id": ["CUST-01", "CUST-02", "CUST-03", "CUST-03", "CUST-05", "CUST-06", "CUST-07"],
        "product_id": ["PRD-01", "PRD-02", "PRD-03", "PRD-03", "PRD-05", "PRD-06", "PRD-07"],
        "store_id": ["STR-01", "STR-01", "STR-02", "STR-02", "STR-01", "STR-02", "STR-01"],
        "date_key": [20230101, 20230102, 20230103, 20230103, 20230105, 20230106, 20230107],
        "quantity": [2, -1, 5, 5, 1, 100, 3],  # -1 invalid, 100 outlier
        "unit_price": [10.0, 20.0, 15.0, 15.0, -5.0, 50.0, 30.0],  # -5.0 invalid
        "discount_amount": [0.0, 5.0, None, None, 1.0, 0.0, 2.0],  # null discount
        "total_amount": [20.0, 0.0, 75.0, 75.0, 0.0, 5000.0, 88.0],  # 5000 outlier
        "cost_amount": [12.0, 15.0, 45.0, 45.0, 3.0, 3000.0, 50.0],
        "profit_amount": [8.0, -15.0, 30.0, 30.0, -3.0, 2000.0, 38.0],
        "payment_method_id": ["PM-CC", "PM-DC", "PM-CC", "PM-CC", "PM-UPI", "PM-PP", "PM-CC"],
    }
    return pd.DataFrame(data)


def test_loader_parquet_and_csv(tmp_path: Path, sample_orders_df: pd.DataFrame) -> None:
    """Test DataLoader read operations for CSV and Parquet."""
    csv_file = tmp_path / "test_orders.csv"
    parquet_file = tmp_path / "test_orders.parquet"

    sample_orders_df.to_csv(csv_file, index=False)
    sample_orders_df.to_parquet(parquet_file, index=False)

    df_csv = DataLoader.load_pandas(csv_file)
    df_parquet = DataLoader.load_pandas(parquet_file)

    assert len(df_csv) == len(sample_orders_df)
    assert len(df_parquet) == len(sample_orders_df)


def test_schema_validator_quarantine(tmp_path: Path, sample_orders_df: pd.DataFrame) -> None:
    """Test schema validation separates valid records from malformed records."""
    validator = SchemaValidator(quarantine_dir=tmp_path / "quarantine")
    valid_df, quarantined_df, summary = validator.validate_orders(sample_orders_df)

    # ORD-002 has quantity -1, ORD-005 has unit_price -5.0, last row has null order_id
    assert len(quarantined_df) == 3
    assert len(valid_df) == 4
    assert summary.quarantined_rows == 3


def test_duplicate_detection(sample_orders_df: pd.DataFrame) -> None:
    """Test duplicate detection isolates collision rows."""
    dedup_df, dupes_df = DuplicateDetector.deduplicate(sample_orders_df, subset=["order_id"])

    # ORD-003 appears twice
    assert len(dupes_df) == 1
    assert len(dedup_df) == len(sample_orders_df) - 1


def test_null_handler_strategies() -> None:
    """Test explicit per-column null strategies (fill_value, impute_median, drop)."""
    df = pd.DataFrame(
        {
            "order_id": ["O1", "O2", None],
            "discount_amount": [10.0, None, 5.0],
            "profit_amount": [100.0, None, 200.0],
        }
    )

    strategies = {
        "order_id": {"action": "drop"},
        "discount_amount": {"action": "fill_value", "value": 0.0},
        "profit_amount": {"action": "impute_median"},
    }

    handler = NullHandler(strategies)
    cleaned_df = handler.process(df)

    assert len(cleaned_df) == 2
    assert cleaned_df["discount_amount"].isna().sum() == 0
    assert cleaned_df.loc[cleaned_df["order_id"] == "O2", "discount_amount"].values[0] == 0.0
    assert cleaned_df.loc[cleaned_df["order_id"] == "O2", "profit_amount"].values[0] == 100.0


def test_outlier_detector_iqr_and_zscore(sample_orders_df: pd.DataFrame) -> None:
    """Test statistical outlier detection via IQR and Z-Score."""
    detector = OutlierDetector()

    # IQR test
    df_flagged, mask = detector.detect_iqr(sample_orders_df, column="total_amount", action="flag")
    assert "total_amount_is_outlier" in df_flagged.columns
    assert mask.sum() >= 1  # 5000.0 total amount is an outlier

    # Z-Score test with threshold=1.5
    df_clipped, _ = detector.detect_zscore(
        sample_orders_df, column="total_amount", threshold=1.5, action="clip"
    )
    assert df_clipped["total_amount"].max() < 5000.0


def test_memory_optimizer_downcasting() -> None:
    """Test numeric downcasting and categorical conversion RAM reduction."""
    df = pd.DataFrame(
        {
            "int_col": pd.Series([1, 2, 3, 4, 5], dtype="int64"),
            "float_col": pd.Series([1.5, 2.5, 3.5, 4.5, 5.5], dtype="float64"),
            "str_col": pd.Series(["A", "B", "A", "B", "A"], dtype="object"),
        }
    )

    optimized_df, report = MemoryOptimizer.optimize(df)

    assert optimized_df["int_col"].dtype == "uint8"
    assert optimized_df["float_col"].dtype == "float32"
    assert str(optimized_df["str_col"].dtype) == "category"
    assert report["savings_mb"] >= 0.0


def test_pipeline_orchestrator_end_to_end(tmp_path: Path) -> None:
    """Test end-to-end DataPipelineOrchestrator execution."""
    raw_dir = tmp_path / "raw"
    processed_dir = tmp_path / "processed"
    raw_dir.mkdir()

    # Create dummy raw orders parquet file
    data = {
        "order_id": [f"ORD-{i:03d}" for i in range(50)],
        "customer_id": [f"CUST-{i%10:02d}" for i in range(50)],
        "product_id": [f"PRD-{i%5:02d}" for i in range(50)],
        "store_id": ["STR-01"] * 50,
        "date_key": [20230101] * 50,
        "quantity": [2] * 50,
        "unit_price": [25.0] * 50,
        "discount_amount": [0.0] * 50,
        "total_amount": [50.0] * 50,
        "cost_amount": [30.0] * 50,
        "profit_amount": [20.0] * 50,
        "payment_method_id": ["PM-CC"] * 50,
    }
    pd.DataFrame(data).to_parquet(raw_dir / "orders.parquet", index=False)

    orchestrator = DataPipelineOrchestrator(raw_dir=raw_dir, processed_dir=processed_dir)
    report = orchestrator.run_pipeline()

    assert report["processed_rows"] == 50
    assert report["quarantined_rows"] == 0
    assert (processed_dir / "orders_processed.parquet").exists()
