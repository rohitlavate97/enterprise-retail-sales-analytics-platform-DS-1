"""Unit tests for synthetic dataset generators.

Tests seed reproducibility (exact byte equality across independent runs with seed=42),
relational referential integrity across all foreign keys, and Pareto distribution shape.
"""

from pandas.testing import assert_frame_equal

from data.generators.customer_generator import CustomerGenerator
from data.generators.orchestrator import DatasetOrchestrator
from data.generators.product_generator import CategoryGenerator, ProductGenerator


def test_seed_reproducibility() -> None:
    """Test that identical seeds produce byte-identical generated dataframes."""
    gen1 = CustomerGenerator(seed=42)
    gen2 = CustomerGenerator(seed=42)

    region_ids = ["REG-NORTH", "REG-SOUTH", "REG-EAST", "REG-WEST"]
    df1 = gen1.generate(num_customers=100, region_ids=region_ids)
    df2 = gen2.generate(num_customers=100, region_ids=region_ids)

    assert_frame_equal(df1, df2)


def test_product_pareto_reproducibility() -> None:
    """Test product generation seed reproducibility and popularity bounds."""
    cats_df = CategoryGenerator.generate()
    prod_gen1 = ProductGenerator(seed=123)
    prod_gen2 = ProductGenerator(seed=123)

    p_df1 = prod_gen1.generate(num_products=50, categories_df=cats_df)
    p_df2 = prod_gen2.generate(num_products=50, categories_df=cats_df)

    assert_frame_equal(p_df1, p_df2)
    assert p_df1["popularity_score"].min() >= 0.0001
    assert p_df1["popularity_score"].max() <= 1.0


def test_referential_integrity() -> None:
    """Test foreign keys in orders, returns, discounts, and shipping resolve valid keys."""
    orchestrator = DatasetOrchestrator(seed=999)
    # Generate small test dataset in memory
    datasets = orchestrator.generate_all(
        num_orders=1000, num_customers=100, num_products=50, num_stores=10
    )

    customers = set(datasets["customers"]["customer_id"])
    products = set(datasets["products"]["product_id"])
    stores = set(datasets["stores"]["store_id"])
    date_keys = set(datasets["time_dimension"]["date_key"])
    payments = set(datasets["payment_methods"]["payment_method_id"])
    orders = set(datasets["orders"]["order_id"])

    orders_df = datasets["orders"]

    # 1. Verify Orders FKs
    assert set(orders_df["customer_id"]).issubset(customers)
    assert set(orders_df["product_id"]).issubset(products)
    assert set(orders_df["store_id"]).issubset(stores)
    assert set(orders_df["date_key"]).issubset(date_keys)
    assert set(orders_df["payment_method_id"]).issubset(payments)

    # 2. Verify Auxiliary Tables FKs (Order ID references)
    returns_df = datasets["returns"]
    discounts_df = datasets["discounts"]
    shipping_df = datasets["shipping"]

    assert set(returns_df["order_id"]).issubset(orders)
    assert set(discounts_df["order_id"]).issubset(orders)
    assert set(shipping_df["order_id"]).issubset(orders)


def test_pareto_order_volume_concentration() -> None:
    """Test that product demand exhibits Pareto 80/20 concentration."""
    cats_df = CategoryGenerator.generate()
    prod_gen = ProductGenerator(seed=42)
    products_df = prod_gen.generate(num_products=100, categories_df=cats_df)

    orchestrator = DatasetOrchestrator(seed=42)
    datasets = orchestrator.generate_all(
        num_orders=5000, num_customers=500, num_products=100, num_stores=10
    )

    orders_df = datasets["orders"]
    top_20_products = set(products_df.nlargest(20, "popularity_score")["product_id"])

    top_20_orders_count = orders_df["product_id"].isin(top_20_products).sum()
    top_20_share = top_20_orders_count / len(orders_df)

    # Assert top 20% of products command significantly more demand than uniform 20%
    assert top_20_share > 0.35
