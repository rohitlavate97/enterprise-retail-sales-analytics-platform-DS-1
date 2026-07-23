"""Store and Region synthetic dataset generator.

Generates geographic regions and retail store outlets with regional demand multipliers,
store format classifications, and physical floor space specifications.
"""

from typing import Any

import numpy as np
import pandas as pd

from core.logging import get_logger

logger = get_logger(__name__)

REGIONS_DATA = [
    {"region_id": "REG-NORTH", "region_name": "North", "country": "USA", "manager_name": "Alice Vance"},
    {"region_id": "REG-SOUTH", "region_name": "South", "country": "USA", "manager_name": "Bob Miller"},
    {"region_id": "REG-EAST", "region_name": "East", "country": "USA", "manager_name": "Carol Danvers"},
    {"region_id": "REG-WEST", "region_name": "West", "country": "USA", "manager_name": "David Banner"},
    {"region_id": "REG-CENTRAL", "region_name": "Central", "country": "USA", "manager_name": "Eve Polastri"},
]

STORE_TYPES = ["Superstore", "Express", "Flagship", "Online"]
STORE_TYPE_PROBS = [0.40, 0.30, 0.10, 0.20]


class RegionGenerator:
    """Generator for geographic sales regions."""

    @staticmethod
    def generate() -> pd.DataFrame:
        """Returns static catalog of geographic regions."""
        return pd.DataFrame(REGIONS_DATA)


class StoreGenerator:
    """Seeded generator for synthetic retail store locations."""

    def __init__(self, seed: int = 42) -> None:
        self.seed = seed
        self.rng = np.random.default_rng(seed)

    def generate(self, num_stores: int, regions_df: pd.DataFrame) -> pd.DataFrame:
        """Generates synthetic store locations dataframe.

        Args:
            num_stores: Total number of retail stores to generate.
            regions_df: Regions DataFrame containing region_id column.

        Returns:
            Pandas DataFrame conforming to StoreSchema.
        """
        logger.info(
            "Generating %d store records with seed=%d...", num_stores, self.seed
        )

        region_ids = regions_df["region_id"].tolist()
        store_ids = [f"STR-{i+1:03d}" for i in range(num_stores)]
        assigned_regions = self.rng.choice(region_ids, size=num_stores)
        store_types = self.rng.choice(STORE_TYPES, size=num_stores, p=STORE_TYPE_PROBS)

        store_names: list[str] = []
        sqft_areas: list[int] = []

        for idx, (r_id, st_type) in enumerate(zip(assigned_regions, store_types, strict=False)):
            region_code = r_id.split("-")[1]
            store_names.append(f"Store {idx+1:03d} ({region_code} {st_type})")

            if st_type == "Superstore":
                sqft = int(self.rng.integers(50000, 120000))
            elif st_type == "Flagship":
                sqft = int(self.rng.integers(80000, 150000))
            elif st_type == "Express":
                sqft = int(self.rng.integers(10000, 30000))
            else:  # Online fulfillment
                sqft = int(self.rng.integers(100000, 300000))

            sqft_areas.append(sqft)

        data: dict[str, Any] = {
            "store_id": store_ids,
            "store_name": store_names,
            "region_id": assigned_regions,
            "store_type": store_types,
            "sqft_area": sqft_areas,
        }

        df = pd.DataFrame(data)
        logger.info("Successfully generated store dataset (shape: %s).", df.shape)
        return df
