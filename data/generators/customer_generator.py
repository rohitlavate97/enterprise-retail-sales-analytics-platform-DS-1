"""Customer synthetic dataset generator.

Generates reproducible customer master data with seeded RNG, market segments,
regional assignments, signup dates, and statistical churn risk scores.
"""

from datetime import date, timedelta
from typing import Any

import numpy as np
import pandas as pd

from core.logging import get_logger

logger = get_logger(__name__)

FIRST_NAMES = [
    "James",
    "Mary",
    "John",
    "Patricia",
    "Robert",
    "Jennifer",
    "Michael",
    "Linda",
    "William",
    "Elizabeth",
    "David",
    "Barbara",
    "Richard",
    "Susan",
    "Joseph",
    "Jessica",
    "Thomas",
    "Sarah",
    "Charles",
    "Karen",
    "Christopher",
    "Nancy",
    "Daniel",
    "Lisa",
    "Matthew",
    "Betty",
    "Anthony",
    "Margaret",
    "Mark",
    "Sandra",
    "Donald",
    "Ashley",
]

LAST_NAMES = [
    "Smith",
    "Johnson",
    "Williams",
    "Brown",
    "Jones",
    "Garcia",
    "Miller",
    "Davis",
    "Rodriguez",
    "Martinez",
    "Hernandez",
    "Lopez",
    "Gonzalez",
    "Wilson",
    "Anderson",
    "Thomas",
    "Taylor",
    "Moore",
    "Jackson",
    "Martin",
    "Lee",
    "Perez",
    "Thompson",
]

DOMAINS = ["gmail.com", "yahoo.com", "outlook.com", "corp.net", "enterprise.org"]
SEGMENTS = ["Consumer", "Corporate", "Home Office"]
SEGMENT_PROBS = [0.50, 0.30, 0.20]


class CustomerGenerator:
    """Seeded generator for synthetic customer entities."""

    def __init__(self, seed: int = 42) -> None:
        self.seed = seed
        self.rng = np.random.default_rng(seed)

    def generate(self, num_customers: int, region_ids: list[str]) -> pd.DataFrame:
        """Generates a Pandas DataFrame of synthetic customers.

        Args:
            num_customers: Number of customer records to generate.
            region_ids: Available foreign key region IDs.

        Returns:
            Pandas DataFrame conforming to CustomerSchema.
        """
        logger.info("Generating %d customer records with seed=%d...", num_customers, self.seed)

        customer_ids = [f"CUST-{i+1:06d}" for i in range(num_customers)]
        firsts = self.rng.choice(FIRST_NAMES, size=num_customers)
        lasts = self.rng.choice(LAST_NAMES, size=num_customers)
        names = [f"{fst} {lst}" for fst, lst in zip(firsts, lasts, strict=False)]

        domains = self.rng.choice(DOMAINS, size=num_customers)
        emails = [
            f"{fst.lower()}.{lst.lower()}{self.rng.integers(10, 999)}@{d}"
            for fst, lst, d in zip(firsts, lasts, domains, strict=False)
        ]

        segments = self.rng.choice(SEGMENTS, size=num_customers, p=SEGMENT_PROBS)
        regions = self.rng.choice(region_ids, size=num_customers)

        # Signup dates over past 3 years (1095 days)
        start_signup = date(2021, 1, 1)
        day_offsets = self.rng.integers(0, 1095, size=num_customers)
        signup_dates = [start_signup + timedelta(days=int(offset)) for offset in day_offsets]

        # Churn risk using Beta distribution (alpha=2, beta=5) skewed towards lower churn
        churn_risk = np.round(self.rng.beta(a=2.0, b=5.0, size=num_customers), 4)

        data: dict[str, Any] = {
            "customer_id": customer_ids,
            "name": names,
            "email": emails,
            "segment": segments,
            "region_id": regions,
            "signup_date": signup_dates,
            "churn_risk_score": churn_risk,
        }

        df = pd.DataFrame(data)
        logger.info("Successfully generated customer dataset (shape: %s).", df.shape)
        return df
