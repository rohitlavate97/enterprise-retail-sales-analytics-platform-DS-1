"""Schema validation and malformed data quarantine pipeline stage.

Validates Pandas/Polars DataFrames against business domain constraints (non-null keys,
valid numeric boundaries). Isolates invalid records into a quarantine data store.
"""

from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from config.settings import get_settings
from core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class ValidationSummary:
    """Dataclass holding pipeline schema validation metrics."""

    table_name: str
    total_rows: int
    valid_rows: int
    quarantined_rows: int
    rejection_reasons: dict[str, int]


class SchemaValidator:
    """Production validator quarantining records failing structural constraints."""

    def __init__(self, quarantine_dir: Path | str | None = None) -> None:
        settings = get_settings()
        self.quarantine_dir = (
            Path(quarantine_dir) if quarantine_dir else settings.data.quarantine_dir
        )
        self.quarantine_dir.mkdir(parents=True, exist_ok=True)

    def validate_orders(
        self, df: pd.DataFrame
    ) -> tuple[pd.DataFrame, pd.DataFrame, ValidationSummary]:
        """Validates order transactions against schema boundaries.

        Validation rules:
        1. Non-null order_id, customer_id, product_id, store_id.
        2. quantity > 0
        3. unit_price > 0.0
        4. total_amount >= 0.0

        Args:
            df: Orders DataFrame to validate.

        Returns:
            Tuple of (valid_df, quarantined_df, summary).
        """
        logger.info("Running schema validation on %d order records...", len(df))

        invalid_mask = pd.Series(False, index=df.index)
        reasons: dict[str, int] = {}

        # Rule 1: Null Primary/Foreign keys
        null_pk = df["order_id"].isna() | df["customer_id"].isna() | df["product_id"].isna()
        if null_pk.any():
            invalid_mask |= null_pk
            reasons["null_primary_foreign_key"] = int(null_pk.sum())

        # Rule 2: Invalid quantity (<= 0)
        invalid_qty = df["quantity"] <= 0
        if invalid_qty.any():
            invalid_mask |= invalid_qty
            reasons["non_positive_quantity"] = int(invalid_qty.sum())

        # Rule 3: Invalid price (<= 0.0)
        invalid_price = df["unit_price"] <= 0.0
        if invalid_price.any():
            invalid_mask |= invalid_price
            reasons["non_positive_unit_price"] = int(invalid_price.sum())

        # Rule 4: Negative total amount (< 0.0)
        invalid_total = df["total_amount"] < 0.0
        if invalid_total.any():
            invalid_mask |= invalid_total
            reasons["negative_total_amount"] = int(invalid_total.sum())

        valid_df = df[~invalid_mask].copy()
        quarantined_df = df[invalid_mask].copy()

        if len(quarantined_df) > 0:
            quarantine_path = self.quarantine_dir / "orders_quarantine.parquet"
            quarantined_df.to_parquet(quarantine_path, index=False)
            logger.warning(
                "Quarantined %d malformed order records to %s",
                len(quarantined_df),
                quarantine_path,
            )

        summary = ValidationSummary(
            table_name="orders",
            total_rows=len(df),
            valid_rows=len(valid_df),
            quarantined_rows=len(quarantined_df),
            rejection_reasons=reasons,
        )

        logger.info(
            "Validation completed: %d valid, %d quarantined.",
            summary.valid_rows,
            summary.quarantined_rows,
        )
        return valid_df, quarantined_df, summary
