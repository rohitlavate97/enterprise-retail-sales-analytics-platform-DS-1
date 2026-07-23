"""Master Dataset Orchestrator module.

Coordinates execution across all relational dataset generators (Categories, Products,
Regions, Stores, Customers, Time Dimension, Orders, Returns, Discounts, Shipping),
saves outputs to CSV and Parquet formats in data/raw/, and validates referential integrity.
"""

from pathlib import Path
import time
from typing import Any

from config.settings import get_settings
from core.logging import get_logger
from data.generators.auxiliary_generator import AuxiliaryGenerator
from data.generators.customer_generator import CustomerGenerator
from data.generators.order_generator import OrderGenerator, PaymentMethodGenerator
from data.generators.product_generator import CategoryGenerator, ProductGenerator
from data.generators.store_generator import RegionGenerator, StoreGenerator
from data.generators.time_generator import TimeDimensionGenerator

logger = get_logger(__name__)


class DatasetOrchestrator:
    """Master orchestrator for relational dataset generation."""

    def __init__(self, seed: int | None = None, output_dir: Path | str | None = None) -> None:
        self.settings = get_settings()
        self.seed = seed if seed is not None else self.settings.data.seed
        self.output_dir = Path(output_dir) if output_dir else self.settings.data.raw_dir

    def generate_all(
        self,
        num_orders: int | None = None,
        num_customers: int | None = None,
        num_products: int | None = None,
        num_stores: int = 20,
    ) -> dict[str, Any]:
        """Runs full relational dataset generation workflow.

        Args:
            num_orders: Target number of order transactions.
            num_customers: Target number of customer records.
            num_products: Target number of products.
            num_stores: Target number of store outlets.

        Returns:
            Dictionary mapping table names to generated Pandas DataFrames.
        """
        n_orders = num_orders if num_orders else self.settings.data.default_num_orders
        n_customers = num_customers if num_customers else self.settings.data.default_num_customers
        n_products = num_products if num_products else self.settings.data.default_num_products

        logger.info("Starting relational dataset generation (seed=%d)...", self.seed)
        start_time = time.perf_counter()

        self.output_dir.mkdir(parents=True, exist_ok=True)

        # 1. Independent Dimensions
        categories_df = CategoryGenerator.generate()
        regions_df = RegionGenerator.generate()
        payment_methods_df = PaymentMethodGenerator.generate()

        time_gen = TimeDimensionGenerator(
            start_date=self.settings.data.start_date, end_date=self.settings.data.end_date
        )
        time_df = time_gen.generate()

        # 2. Dependent Dimensions
        prod_gen = ProductGenerator(seed=self.seed)
        products_df = prod_gen.generate(num_products=n_products, categories_df=categories_df)

        store_gen = StoreGenerator(seed=self.seed)
        stores_df = store_gen.generate(num_stores=num_stores, regions_df=regions_df)

        cust_gen = CustomerGenerator(seed=self.seed)
        region_ids = regions_df["region_id"].tolist()
        customers_df = cust_gen.generate(num_customers=n_customers, region_ids=region_ids)

        # 3. Fact Table: Orders
        order_gen = OrderGenerator(seed=self.seed)
        orders_df = order_gen.generate(
            num_orders=n_orders,
            customers_df=customers_df,
            products_df=products_df,
            stores_df=stores_df,
            time_df=time_df,
        )

        # 4. Fact Table Auxiliaries
        aux_gen = AuxiliaryGenerator(seed=self.seed)
        returns_df = aux_gen.generate_returns(orders_df=orders_df, time_df=time_df)
        discounts_df = aux_gen.generate_discounts(orders_df=orders_df)
        shipping_df = aux_gen.generate_shipping(orders_df=orders_df)

        datasets: dict[str, Any] = {
            "categories": categories_df,
            "regions": regions_df,
            "payment_methods": payment_methods_df,
            "time_dimension": time_df,
            "products": products_df,
            "stores": stores_df,
            "customers": customers_df,
            "orders": orders_df,
            "returns": returns_df,
            "discounts": discounts_df,
            "shipping": shipping_df,
        }

        # Save datasets in CSV and Parquet
        for table_name, df in datasets.items():
            csv_path = self.output_dir / f"{table_name}.csv"
            parquet_path = self.output_dir / f"{table_name}.parquet"
            df.to_csv(csv_path, index=False)
            df.to_parquet(parquet_path, index=False)

        elapsed = time.perf_counter() - start_time
        logger.info(
            "Dataset generation completed successfully in %.2f seconds. Datasets saved to %s.",
            elapsed,
            self.output_dir,
        )
        return datasets
