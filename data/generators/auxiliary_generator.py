"""Auxiliary entity synthetic generators for Returns, Discounts, and Shipping.

Generates realistic order returns with category-specific return rates, promotion code log,
and shipping logistics data referencing order transactions.
"""

from datetime import datetime, timedelta
from typing import Any

import numpy as np
import pandas as pd

from core.logging import get_logger

logger = get_logger(__name__)

RETURN_REASONS = ["Defective", "Wrong Item", "Changed Mind", "Size Issue", "Late Delivery"]
RETURN_REASON_PROBS = [0.25, 0.20, 0.30, 0.15, 0.10]

PROMO_CODES = ["SAVE10", "HOLIDAY20", "BLACKFRIDAY", "WELCOME15", "SUMMER25", "VIPDEAL"]

SHIPPING_MODES = ["Standard", "Second Day", "Express", "Same Day"]
SHIPPING_MODE_PROBS = [0.50, 0.25, 0.15, 0.10]
CARRIERS = ["FedEx", "UPS", "DHL", "USPS"]


class AuxiliaryGenerator:
    """Seeded generator for Returns, Discounts, and Shipping entities."""

    def __init__(self, seed: int = 42) -> None:
        self.seed = seed
        self.rng = np.random.default_rng(seed)

    def generate_returns(
        self, orders_df: pd.DataFrame, time_df: pd.DataFrame, return_rate: float = 0.08
    ) -> pd.DataFrame:
        """Generates order return tickets referencing order_id.

        Args:
            orders_df: Orders DataFrame.
            time_df: Time Dimension DataFrame.
            return_rate: Overall proportion of orders returned (~8%).

        Returns:
            Pandas DataFrame conforming to ReturnSchema.
        """
        logger.info("Generating return records for orders (rate=%.2f)...", return_rate)

        num_orders = len(orders_df)
        is_returned = self.rng.random(size=num_orders) < return_rate
        returned_orders = orders_df[is_returned].copy()
        num_returns = len(returned_orders)

        if num_returns == 0:
            return pd.DataFrame(columns=["return_id", "order_id", "return_date", "return_reason", "refund_amount"])

        return_ids = [f"RET-{i+1:06d}" for i in range(num_returns)]
        order_ids = returned_orders["order_id"].tolist()
        refund_amounts = returned_orders["total_amount"].tolist()

        date_key_map = dict(zip(time_df["date_key"], time_df["full_date"], strict=False))
        return_dates: list[Any] = []

        for d_key in returned_orders["date_key"]:
            base_date = date_key_map.get(d_key, datetime.now().date())
            days_after = int(self.rng.integers(1, 14))
            return_dates.append(base_date + timedelta(days=days_after))

        reasons = self.rng.choice(RETURN_REASONS, size=num_returns, p=RETURN_REASON_PROBS)

        data: dict[str, Any] = {
            "return_id": return_ids,
            "order_id": order_ids,
            "return_date": return_dates,
            "return_reason": reasons,
            "refund_amount": refund_amounts,
        }

        df = pd.DataFrame(data)
        logger.info("Successfully generated %d return records.", len(df))
        return df

    def generate_discounts(self, orders_df: pd.DataFrame) -> pd.DataFrame:
        """Generates discount promo tracking records for discounted orders.

        Args:
            orders_df: Orders DataFrame containing discount_amount column.

        Returns:
            Pandas DataFrame conforming to DiscountSchema.
        """
        logger.info("Generating discount promo tracking records...")

        discounted_orders = orders_df[orders_df["discount_amount"] > 0].copy()
        num_discounts = len(discounted_orders)

        if num_discounts == 0:
            return pd.DataFrame(columns=["discount_id", "order_id", "promo_code", "discount_percent"])

        discount_ids = [f"DSC-{i+1:06d}" for i in range(num_discounts)]
        order_ids = discounted_orders["order_id"].tolist()
        promos = self.rng.choice(PROMO_CODES, size=num_discounts)

        gross = discounted_orders["total_amount"] + discounted_orders["discount_amount"]
        discount_pcts = np.round(discounted_orders["discount_amount"] / np.maximum(gross, 0.01), 4)

        data: dict[str, Any] = {
            "discount_id": discount_ids,
            "order_id": order_ids,
            "promo_code": promos,
            "discount_percent": discount_pcts,
        }

        df = pd.DataFrame(data)
        logger.info("Successfully generated %d discount records.", len(df))
        return df

    def generate_shipping(self, orders_df: pd.DataFrame) -> pd.DataFrame:
        """Generates shipping logistics tracking records for all orders.

        Args:
            orders_df: Orders DataFrame.

        Returns:
            Pandas DataFrame conforming to ShippingSchema.
        """
        logger.info("Generating shipping logistics records for all orders...")

        num_orders = len(orders_df)
        shipping_ids = [f"SHP-{i+1:07d}" for i in range(num_orders)]
        order_ids = orders_df["order_id"].tolist()

        modes = self.rng.choice(SHIPPING_MODES, size=num_orders, p=SHIPPING_MODE_PROBS)
        carriers = self.rng.choice(CARRIERS, size=num_orders)

        # Base cost by mode
        cost_by_mode = {"Standard": 5.0, "Second Day": 12.0, "Express": 22.0, "Same Day": 35.0}
        base_costs = np.array([cost_by_mode[m] for m in modes], dtype=np.float64)
        weight_variance = self.rng.uniform(0.8, 1.5, size=num_orders)
        shipping_costs = np.round(base_costs * weight_variance, 2)

        # ~5% delayed shipping rate
        is_delayed = self.rng.random(size=num_orders) < 0.05

        data: dict[str, Any] = {
            "shipping_id": shipping_ids,
            "order_id": order_ids,
            "shipping_mode": modes,
            "shipping_cost": shipping_costs,
            "carrier": carriers,
            "is_delayed": is_delayed,
        }

        df = pd.DataFrame(data)
        logger.info("Successfully generated %d shipping records.", len(df))
        return df
