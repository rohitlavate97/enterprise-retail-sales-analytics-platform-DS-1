"""Merge/join-based data enrichment views.

Business Questions Answered:
- What is each customer's lifetime value and purchase frequency?
- Which products generate the most revenue per store-region?
- Full denormalized order view for downstream BI dashboards.
"""

import pandas as pd

from core.logging import get_logger

logger = get_logger(__name__)


class DataEnricher:
    """Merge/join engine for building enriched analytical views."""

    @staticmethod
    def build_denormalized_view(
        orders: pd.DataFrame,
        customers: pd.DataFrame,
        products: pd.DataFrame,
        categories: pd.DataFrame,
        stores: pd.DataFrame,
        regions: pd.DataFrame,
    ) -> pd.DataFrame:
        """Build fully denormalized order-level analytical view.

        Business question: *Provide a single wide table joining
        all dimensions for ad-hoc BI analysis.*

        Uses: chained ``merge`` (left joins) on foreign keys.

        Args:
            orders: Orders fact table.
            customers: Customers dimension.
            products: Products dimension.
            categories: Categories dimension.
            stores: Stores dimension.
            regions: Regions dimension.

        Returns:
            Wide DataFrame with all dimension attributes joined.
        """
        logger.info("Building denormalized analytical view...")
        result = (
            orders.merge(
                customers[
                    ["customer_id", "name", "segment", "region_id"]
                ],
                on="customer_id",
                how="left",
                suffixes=("", "_cust"),
            )
            .merge(
                products[
                    [
                        "product_id",
                        "product_name",
                        "category_id",
                    ]
                ],
                on="product_id",
                how="left",
            )
            .merge(
                categories[["category_id", "category_name"]],
                on="category_id",
                how="left",
            )
            .merge(
                stores[["store_id", "store_name", "region_id"]],
                on="store_id",
                how="left",
                suffixes=("", "_store"),
            )
            .merge(
                regions[["region_id", "region_name"]],
                left_on="region_id_store",
                right_on="region_id",
                how="left",
                suffixes=("", "_region"),
            )
        )
        logger.info(
            "Denormalized view: %d rows × %d cols",
            len(result),
            len(result.columns),
        )
        return result

    @staticmethod
    def customer_lifetime_value(
        orders: pd.DataFrame,
    ) -> pd.DataFrame:
        """Compute customer lifetime value (CLV) summary.

        Business question: *Who are the highest-value customers
        by total spend and purchase frequency?*

        Uses: ``groupby`` + ``agg`` with named aggregation,
        then ``join`` to enrich.

        Args:
            orders: Orders fact table.

        Returns:
            DataFrame indexed by customer_id with CLV metrics.
        """
        logger.info("Computing customer lifetime value...")
        clv = (
            orders.groupby("customer_id", observed=True)
            .agg(
                total_spend=("total_amount", "sum"),
                total_orders=("order_id", "count"),
                avg_order_value=("total_amount", "mean"),
                total_profit=("profit_amount", "sum"),
                first_order_date=("date_key", "min"),
                last_order_date=("date_key", "max"),
            )
            .sort_values("total_spend", ascending=False)
        )
        return clv

    @staticmethod
    def product_store_performance(
        orders: pd.DataFrame,
        products: pd.DataFrame,
        stores: pd.DataFrame,
    ) -> pd.DataFrame:
        """Product performance per store.

        Business question: *Which products sell best at which
        stores, and where are there revenue gaps?*

        Uses: ``merge`` + ``groupby`` + ``agg``.

        Args:
            orders: Orders fact table.
            products: Products dimension.
            stores: Stores dimension.

        Returns:
            DataFrame with product × store performance metrics.
        """
        logger.info("Computing product × store performance...")
        enriched = orders.merge(
            products[["product_id", "product_name"]],
            on="product_id",
            how="left",
        ).merge(
            stores[["store_id", "store_name"]],
            on="store_id",
            how="left",
        )
        result = (
            enriched.groupby(
                ["store_name", "product_name"], observed=True
            )
            .agg(
                units_sold=("quantity", "sum"),
                revenue=("total_amount", "sum"),
                profit=("profit_amount", "sum"),
            )
            .sort_values(
                ["store_name", "revenue"], ascending=[True, False]
            )
        )
        return result
