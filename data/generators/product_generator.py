"""Product and Category synthetic dataset generator.

Generates product categories and individual product entities adhering to a Pareto-like
popularity distribution (80/20 rule), realistic cost/unit prices, and stock levels.
"""

from typing import Any

import numpy as np
import pandas as pd

from core.logging import get_logger

logger = get_logger(__name__)

CATEGORIES_DATA = [
    {"category_id": "CAT-001", "category_name": "Electronics", "department": "Technology"},
    {"category_id": "CAT-002", "category_name": "Apparel", "department": "Fashion"},
    {"category_id": "CAT-003", "category_name": "Home & Kitchen", "department": "Home"},
    {"category_id": "CAT-004", "category_name": "Furniture", "department": "Home"},
    {
        "category_id": "CAT-005",
        "category_name": "Beauty & Personal Care",
        "department": "Personal Care",
    },
    {"category_id": "CAT-006", "category_name": "Sports & Outdoors", "department": "Outdoors"},
    {"category_id": "CAT-007", "category_name": "Books & Stationery", "department": "Media"},
]

PRODUCT_ADJECTIVES = [
    "Premium",
    "Ultra",
    "Ergonomic",
    "Smart",
    "Eco-Friendly",
    "Pro",
    "Compact",
    "Deluxe",
]
PRODUCT_NOUNS = {
    "CAT-001": [
        "Wireless Headphones",
        "4K Monitor",
        "Smartphone",
        "Bluetooth Speaker",
        "Laptop Stand",
        "Smartwatch",
    ],
    "CAT-002": [
        "Cotton T-Shirt",
        "Denim Jeans",
        "Running Shoes",
        "Leather Jacket",
        "Wool Sweater",
        "Sports Socks",
    ],
    "CAT-003": [
        "Coffee Maker",
        "Blender",
        "Non-Stick Frying Pan",
        "Air Fryer",
        "Chef Knife Set",
        "Stainless Water Bottle",
    ],
    "CAT-004": [
        "Office Chair",
        "Standing Desk",
        "Bookshelf",
        "Dining Table",
        "Sofa Bed",
        "Table Lamp",
    ],
    "CAT-005": [
        "Facial Cleanser",
        "Moisturizing Cream",
        "Electric Toothbrush",
        "Hair Dryer",
        "Sunscreen SPF50",
    ],
    "CAT-006": [
        "Yoga Mat",
        "Dumbbell Set",
        "Camping Tent",
        "Treadmill",
        "Bicycle Helmet",
        "Resistance Bands",
    ],
    "CAT-007": [
        "Hardcover Notebook",
        "Fountain Pen",
        "Desk Organizer",
        "Ergonomic Pen Set",
        "Planner 2024",
    ],
}


class CategoryGenerator:
    """Generator for retail product categories."""

    @staticmethod
    def generate() -> pd.DataFrame:
        """Returns static catalog of product categories."""
        return pd.DataFrame(CATEGORIES_DATA)


class ProductGenerator:
    """Seeded generator for synthetic products with Pareto popularity weighting."""

    def __init__(self, seed: int = 42) -> None:
        self.seed = seed
        self.rng = np.random.default_rng(seed)

    def generate(self, num_products: int, categories_df: pd.DataFrame) -> pd.DataFrame:
        """Generates synthetic product inventory dataframe.

        Args:
            num_products: Total number of products to generate.
            categories_df: Categories DataFrame containing category_id column.

        Returns:
            Pandas DataFrame conforming to ProductSchema.
        """
        logger.info("Generating %d product records with seed=%d...", num_products, self.seed)

        category_ids = categories_df["category_id"].tolist()
        product_ids = [f"PRD-{i + 1001:05d}" for i in range(num_products)]

        assigned_cats = self.rng.choice(category_ids, size=num_products)
        product_names: list[str] = []
        cost_prices: list[float] = []
        unit_prices: list[float] = []

        for cat in assigned_cats:
            adj = self.rng.choice(PRODUCT_ADJECTIVES)
            noun = self.rng.choice(PRODUCT_NOUNS.get(cat, ["Generic Item"]))
            name = f"{adj} {noun}"
            product_names.append(name)

            # Cost price range per category
            base_cost = float(self.rng.uniform(10.0, 500.0))
            markup_multiplier = float(self.rng.uniform(1.2, 2.5))
            unit_price = round(base_cost * markup_multiplier, 2)
            cost_price = round(base_cost, 2)

            cost_prices.append(cost_price)
            unit_prices.append(unit_price)

        # Pareto distribution for product popularity (alpha = 1.16 gives ~80/20 ratio)
        pareto_raw = self.rng.pareto(a=1.16, size=num_products)
        # Normalize between 0.0001 and 1.0
        popularity = np.round(
            (pareto_raw - pareto_raw.min()) / (pareto_raw.max() - pareto_raw.min() + 1e-8), 4
        )
        popularity = np.clip(popularity, 0.001, 1.0)

        stock_quantities = self.rng.integers(10, 1000, size=num_products)

        data: dict[str, Any] = {
            "product_id": product_ids,
            "product_name": product_names,
            "category_id": assigned_cats,
            "cost_price": cost_prices,
            "unit_price": unit_prices,
            "popularity_score": popularity,
            "stock_quantity": stock_quantities,
        }

        df = pd.DataFrame(data)
        logger.info("Successfully generated product dataset (shape: %s).", df.shape)
        return df
