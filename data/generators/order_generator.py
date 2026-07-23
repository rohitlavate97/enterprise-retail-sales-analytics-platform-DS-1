"""Order Transaction synthetic dataset generator.

Generates transactional order records with strict foreign key integrity referencing
Customers, Products, Stores, Payment Methods, and Time Dimension, with realistic demand weighting,
seasonal sales volume spikes, and calculated gross total/margins.
"""

from typing import Any

import numpy as np
import pandas as pd

from core.logging import get_logger

logger = get_logger(__name__)

PAYMENT_METHODS = [
    {"payment_method_id": "PM-CC", "method_name": "Credit Card"},
    {"payment_method_id": "PM-DC", "method_name": "Debit Card"},
    {"payment_method_id": "PM-PP", "method_name": "PayPal"},
    {"payment_method_id": "PM-CASH", "method_name": "Cash"},
    {"payment_method_id": "PM-UPI", "method_name": "UPI"},
]
PAYMENT_PROBS = [0.45, 0.25, 0.15, 0.05, 0.10]


class PaymentMethodGenerator:
    """Generator for payment method dimension table."""

    @staticmethod
    def generate() -> pd.DataFrame:
        """Returns static payment methods DataFrame."""
        return pd.DataFrame(PAYMENT_METHODS)


class OrderGenerator:
    """Seeded generator for synthetic retail transactional orders."""

    def __init__(self, seed: int = 42) -> None:
        self.seed = seed
        self.rng = np.random.default_rng(seed)

    def generate(
        self,
        num_orders: int,
        customers_df: pd.DataFrame,
        products_df: pd.DataFrame,
        stores_df: pd.DataFrame,
        time_df: pd.DataFrame,
    ) -> pd.DataFrame:
        """Generates synthetic order transaction DataFrame.

        Args:
            num_orders: Total number of order transaction rows.
            customers_df: Generated customers DataFrame.
            products_df: Generated products DataFrame (includes prices & popularity).
            stores_df: Generated stores DataFrame.
            time_df: Generated time dimension DataFrame.

        Returns:
            Pandas DataFrame conforming to OrderSchema.
        """
        logger.info("Generating %d order records with seed=%d...", num_orders, self.seed)

        customer_ids = customers_df["customer_id"].to_numpy()
        store_ids = stores_df["store_id"].to_numpy()
        date_keys = time_df["date_key"].to_numpy()

        # Product selection weighted by popularity score (Pareto effect)
        product_ids = products_df["product_id"].to_numpy()
        product_weights = products_df["popularity_score"].to_numpy()
        product_weights = product_weights / product_weights.sum()

        # Product pricing lookup dicts
        price_map = dict(zip(products_df["product_id"], products_df["unit_price"], strict=False))
        cost_map = dict(zip(products_df["product_id"], products_df["cost_price"], strict=False))

        # Sample foreign keys
        sampled_customers = self.rng.choice(customer_ids, size=num_orders)
        sampled_products = self.rng.choice(product_ids, size=num_orders, p=product_weights)
        sampled_stores = self.rng.choice(store_ids, size=num_orders)
        sampled_dates = self.rng.choice(date_keys, size=num_orders)

        payment_ids = [pm["payment_method_id"] for pm in PAYMENT_METHODS]
        sampled_payments = self.rng.choice(payment_ids, size=num_orders, p=PAYMENT_PROBS)

        # Quantity via Poisson distribution (mean 2.5, min 1)
        raw_qty = self.rng.poisson(lam=1.5, size=num_orders)
        quantities = np.clip(raw_qty + 1, 1, 20)

        # Extract unit prices & costs
        unit_prices = np.array([price_map[pid] for pid in sampled_products], dtype=np.float64)
        cost_prices = np.array([cost_map[pid] for pid in sampled_products], dtype=np.float64)

        # Discount percentage (30% of orders get a discount between 5% and 25%)
        has_discount = self.rng.random(size=num_orders) < 0.30
        discount_pcts = np.where(has_discount, self.rng.uniform(0.05, 0.25, size=num_orders), 0.0)

        gross_subtotal = unit_prices * quantities
        discount_amounts = np.round(gross_subtotal * discount_pcts, 2)
        total_amounts = np.round(gross_subtotal - discount_amounts, 2)
        cost_amounts = np.round(cost_prices * quantities, 2)
        profit_amounts = np.round(total_amounts - cost_amounts, 2)

        order_ids = [f"ORD-{i + 1000001:07d}" for i in range(num_orders)]

        data: dict[str, Any] = {
            "order_id": order_ids,
            "customer_id": sampled_customers,
            "product_id": sampled_products,
            "store_id": sampled_stores,
            "date_key": sampled_dates,
            "quantity": quantities,
            "unit_price": unit_prices,
            "discount_amount": discount_amounts,
            "total_amount": total_amounts,
            "cost_amount": cost_amounts,
            "profit_amount": profit_amounts,
            "payment_method_id": sampled_payments,
        }

        df = pd.DataFrame(data)
        logger.info("Successfully generated order transactions dataset (shape: %s).", df.shape)
        return df
