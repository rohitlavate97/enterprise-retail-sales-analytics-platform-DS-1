"""Correctness tests for Pandas advanced analytics layer.

Tests verify aggregations, joins, pivot operations, and resampling
logic using deterministic, small fixture datasets.
"""

import pandas as pd
import pytest

from analytics.aggregation import SalesAggregator
from analytics.enrichment import DataEnricher
from analytics.pivot_analytics import PivotAnalytics
from analytics.temporal import TemporalAnalytics


@pytest.fixture
def sample_data() -> dict[str, pd.DataFrame]:
    """Provides small, deterministic retail datasets for testing."""
    orders = pd.DataFrame(
        {
            "order_id": ["ORD-1", "ORD-2", "ORD-3", "ORD-4"],
            "customer_id": ["CUST-1", "CUST-2", "CUST-1", "CUST-3"],
            "product_id": ["PRD-1", "PRD-2", "PRD-1", "PRD-3"],
            "store_id": ["STR-1", "STR-2", "STR-1", "STR-1"],
            "date_key": [20230101, 20230102, 20230115, 20230201],
            "quantity": [2, 1, 3, 5],
            "unit_price": [10.0, 20.0, 10.0, 5.0],
            "discount_amount": [1.0, 0.0, 2.0, 0.0],
            "total_amount": [19.0, 20.0, 28.0, 25.0],
            "cost_amount": [12.0, 15.0, 18.0, 20.0],
            "profit_amount": [7.0, 5.0, 10.0, 5.0],
            "payment_method_id": ["PM-1", "PM-2", "PM-1", "PM-1"],
        }
    )

    customers = pd.DataFrame(
        {
            "customer_id": ["CUST-1", "CUST-2", "CUST-3"],
            "name": ["Alice", "Bob", "Charlie"],
            "segment": ["Consumer", "Corporate", "Consumer"],
            "region_id": ["REG-N", "REG-S", "REG-N"],
        }
    )

    products = pd.DataFrame(
        {
            "product_id": ["PRD-1", "PRD-2", "PRD-3"],
            "product_name": ["Widget A", "Widget B", "Widget C"],
            "category_id": ["CAT-1", "CAT-2", "CAT-1"],
        }
    )

    categories = pd.DataFrame(
        {
            "category_id": ["CAT-1", "CAT-2"],
            "category_name": ["Electronics", "Apparel"],
        }
    )

    stores = pd.DataFrame(
        {
            "store_id": ["STR-1", "STR-2"],
            "store_name": ["Store North", "Store South"],
            "region_id": ["REG-N", "REG-S"],
        }
    )

    regions = pd.DataFrame(
        {
            "region_id": ["REG-N", "REG-S"],
            "region_name": ["North", "South"],
        }
    )

    time_dim = pd.DataFrame(
        {
            "date_key": [20230101, 20230102, 20230115, 20230201],
            "full_date": pd.to_datetime(
                ["2023-01-01", "2023-01-02", "2023-01-15", "2023-02-01"]
            ),
        }
    )

    return {
        "orders": orders,
        "customers": customers,
        "products": products,
        "categories": categories,
        "stores": stores,
        "regions": regions,
        "time_dim": time_dim,
    }


class TestSalesAggregator:
    """Tests for SalesAggregator."""

    def test_aggregate_by_store(self, sample_data: dict[str, pd.DataFrame]) -> None:
        orders = sample_data["orders"]
        res = SalesAggregator.aggregate_by_store(orders)

        assert "total_revenue" in res.columns
        assert "total_profit" in res.columns
        assert "avg_order_value" in res.columns
        assert res.index.name == "store_id"
        # Store 1 has 3 orders: total revenue = 19 + 28 + 25 = 72
        assert res.loc["STR-1", "total_revenue"] == 72.0
        # Store 2 has 1 order: total revenue = 20
        assert res.loc["STR-2", "total_revenue"] == 20.0

    def test_aggregate_by_category(self, sample_data: dict[str, pd.DataFrame]) -> None:
        orders = sample_data["orders"]
        products = sample_data["products"]
        categories = sample_data["categories"]
        res = SalesAggregator.aggregate_by_category(orders, products, categories)

        assert "total_revenue" in res.columns
        assert res.index.name == "category_name"
        # CAT-1 (Electronics) has orders: ORD-1 (PRD-1), ORD-3 (PRD-1),
        # ORD-4 (PRD-3) -> 19 + 28 + 25 = 72
        assert res.loc["Electronics", "total_revenue"] == 72.0

        # CAT-2 (Apparel) has order: ORD-2 (Widget B) -> 20
        assert res.loc["Apparel", "total_revenue"] == 20.0

    def test_store_deviation_transform(self, sample_data: dict[str, pd.DataFrame]) -> None:
        orders = sample_data["orders"]
        res = SalesAggregator.store_deviation_transform(orders)

        assert "store_avg_revenue" in res.columns
        assert "revenue_vs_store_avg" in res.columns
        # STR-1 orders: total_amount = [19, 28, 25], mean = 24.0
        # For ORD-1 (STR-1), store_avg = 24.0, dev = 19 - 24 = -5.0
        row1 = res[res["order_id"] == "ORD-1"].iloc[0]
        assert row1["store_avg_revenue"] == 24.0
        assert row1["revenue_vs_store_avg"] == -5.0


class TestPivotAnalytics:
    """Tests for PivotAnalytics."""

    def test_region_by_category_revenue(self, sample_data: dict[str, pd.DataFrame]) -> None:
        orders = sample_data["orders"]
        products = sample_data["products"]
        categories = sample_data["categories"]
        stores = sample_data["stores"]
        regions = sample_data["regions"]

        pivot = PivotAnalytics.region_by_category_revenue(
            orders, products, categories, stores, regions
        )
        assert pivot.shape == (2, 2)  # North/South by Electronics/Apparel
        assert pivot.loc["North", "Electronics"] == 72.0
        assert pivot.loc["North", "Apparel"] == 0.0
        assert pivot.loc["South", "Apparel"] == 20.0

    def test_region_category_share(self, sample_data: dict[str, pd.DataFrame]) -> None:
        orders = sample_data["orders"]
        products = sample_data["products"]
        categories = sample_data["categories"]
        stores = sample_data["stores"]
        regions = sample_data["regions"]

        pivot = PivotAnalytics.region_by_category_revenue(
            orders, products, categories, stores, regions
        )
        share = PivotAnalytics.region_category_share(pivot)
        assert share.loc["North", "Electronics"] == 100.0
        assert share.loc["South", "Apparel"] == 100.0

    def test_region_by_category_profit(self, sample_data: dict[str, pd.DataFrame]) -> None:
        orders = sample_data["orders"]
        products = sample_data["products"]
        categories = sample_data["categories"]
        stores = sample_data["stores"]
        regions = sample_data["regions"]

        pivot = PivotAnalytics.region_by_category_profit(
            orders, products, categories, stores, regions
        )
        # North Electronics revenue = 72, profit = 7 + 10 + 5 = 22. Margin = 22 / 72 * 100 = 30.56%
        assert pivot.loc["North", "Electronics"] == pytest.approx(30.56, abs=1e-2)


class TestDataEnricher:
    """Tests for DataEnricher."""

    def test_build_denormalized_view(self, sample_data: dict[str, pd.DataFrame]) -> None:
        orders = sample_data["orders"]
        customers = sample_data["customers"]
        products = sample_data["products"]
        categories = sample_data["categories"]
        stores = sample_data["stores"]
        regions = sample_data["regions"]

        res = DataEnricher.build_denormalized_view(
            orders, customers, products, categories, stores, regions
        )
        assert "customer_name" not in res.columns  # only name is mapped to segment etc.
        assert "segment" in res.columns
        assert "category_name" in res.columns
        assert "store_name" in res.columns
        assert "region_name" in res.columns

    def test_customer_lifetime_value(self, sample_data: dict[str, pd.DataFrame]) -> None:
        orders = sample_data["orders"]
        res = DataEnricher.customer_lifetime_value(orders)

        assert "total_spend" in res.columns
        assert "total_orders" in res.columns
        assert res.loc["CUST-1", "total_spend"] == 47.0
        assert res.loc["CUST-1", "total_orders"] == 2

    def test_product_store_performance(self, sample_data: dict[str, pd.DataFrame]) -> None:
        orders = sample_data["orders"]
        products = sample_data["products"]
        stores = sample_data["stores"]

        res = DataEnricher.product_store_performance(orders, products, stores)
        assert "units_sold" in res.columns
        # Store North, Widget A: units sold = 2 + 3 = 5
        assert res.loc[("Store North", "Widget A"), "units_sold"] == 5


class TestTemporalAnalytics:
    """Tests for TemporalAnalytics."""

    def test_resample_sales(self, sample_data: dict[str, pd.DataFrame]) -> None:
        orders = sample_data["orders"]
        time_dim = sample_data["time_dim"]

        res = TemporalAnalytics.resample_sales(orders, time_dim, rule="ME")
        assert len(res) == 2  # Jan 2023, Feb 2023
        assert "total_revenue" in res.columns
        # Jan 2023 orders: ORD-1, ORD-2, ORD-3 -> 19 + 20 + 28 = 67.0
        # Feb 2023 orders: ORD-4 -> 25.0
        assert res.iloc[0]["total_revenue"] == 67.0
        assert res.iloc[1]["total_revenue"] == 25.0
