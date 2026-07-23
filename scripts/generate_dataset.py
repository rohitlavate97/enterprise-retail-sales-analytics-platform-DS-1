"""CLI entry script for generating relational retail analytics datasets.

Usage:
    python scripts/generate_dataset.py --orders 100000 --customers 10000 --seed 42
"""

import argparse
from pathlib import Path
import sys

# Ensure root workspace is on python path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from data.generators.orchestrator import DatasetOrchestrator
from core.logging import get_logger

logger = get_logger("scripts.generate_dataset")


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate synthetic retail analytics dataset.")
    parser.add_argument("--orders", type=int, default=100000, help="Number of order transactions to generate")
    parser.add_argument("--customers", type=int, default=10000, help="Number of customer entities to generate")
    parser.add_argument("--products", type=int, default=500, help="Number of product catalog items to generate")
    parser.add_argument("--stores", type=int, default=20, help="Number of retail store outlets to generate")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for reproducibility")
    parser.add_argument("--output-dir", type=str, default="data/raw", help="Target output directory")

    args = parser.parse_args()

    orchestrator = DatasetOrchestrator(seed=args.seed, output_dir=args.output_dir)
    datasets = orchestrator.generate_all(
        num_orders=args.orders,
        num_customers=args.customers,
        num_products=args.products,
        num_stores=args.stores,
    )

    logger.info("Generated tables summary:")
    for name, df in datasets.items():
        logger.info("  - %-15s: %8d rows", name, len(df))


if __name__ == "__main__":
    main()
