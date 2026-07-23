"""Vectorized business KPI calculations using NumPy.

All computations use NumPy broadcasting and vectorized operations
for O(n) throughput on production-scale datasets (100k+ rows).
No Python-level loops are used in hot paths.
"""

import numpy as np
from numpy.typing import ArrayLike

from core.logging import get_logger

logger = get_logger(__name__)


class KPICalculator:
    """Production vectorized KPI engine for retail analytics."""

    @staticmethod
    def calculate_revenue(
        quantity: ArrayLike,
        unit_price: ArrayLike,
        discount: ArrayLike,
    ) -> np.ndarray:
        """Compute net revenue per order line.

        Formula: revenue = quantity * unit_price - discount

        Args:
            quantity: Array of order quantities.
            unit_price: Array of per-unit prices.
            discount: Array of discount amounts.

        Returns:
            1-D ndarray of net revenue values.
        """
        q = np.asarray(quantity, dtype=np.float64)
        p = np.asarray(unit_price, dtype=np.float64)
        d = np.asarray(discount, dtype=np.float64)
        revenue = q * p - d
        logger.debug("Computed revenue for %d rows.", revenue.shape[0])
        return revenue

    @staticmethod
    def calculate_profit_margin(
        profit: ArrayLike,
        revenue: ArrayLike,
    ) -> np.ndarray:
        """Compute profit margin percentage per order.

        Formula: margin% = (profit / revenue) * 100
        Safe division: returns 0.0 where revenue == 0.

        Args:
            profit: Array of profit amounts.
            revenue: Array of revenue amounts.

        Returns:
            1-D ndarray of profit margin percentages.
        """
        p = np.asarray(profit, dtype=np.float64)
        r = np.asarray(revenue, dtype=np.float64)
        return np.where(r != 0, (p / r) * 100.0, 0.0)

    @staticmethod
    def calculate_gross_margin(
        revenue: ArrayLike,
        cost: ArrayLike,
    ) -> np.ndarray:
        """Compute gross margin percentage.

        Formula: gross_margin% = ((revenue - cost) / revenue) * 100
        Safe division: returns 0.0 where revenue == 0.

        Args:
            revenue: Array of revenue amounts.
            cost: Array of cost amounts.

        Returns:
            1-D ndarray of gross margin percentages.
        """
        r = np.asarray(revenue, dtype=np.float64)
        c = np.asarray(cost, dtype=np.float64)
        return np.where(r != 0, ((r - c) / r) * 100.0, 0.0)

    @staticmethod
    def calculate_yoy_growth(
        current_period: ArrayLike,
        previous_period: ArrayLike,
    ) -> np.ndarray:
        """Compute year-over-year growth rate percentage.

        Formula: yoy% = ((current - previous) / previous) * 100
        Safe division: returns 0.0 where previous == 0.

        Args:
            current_period: Array of current period metric values.
            previous_period: Array of previous period metric values.

        Returns:
            1-D ndarray of YoY growth percentages.
        """
        cur = np.asarray(current_period, dtype=np.float64)
        prev = np.asarray(previous_period, dtype=np.float64)
        return np.where(prev != 0, ((cur - prev) / prev) * 100.0, 0.0)

    @staticmethod
    def calculate_average_order_value(
        total_revenue: ArrayLike,
        num_orders: ArrayLike,
    ) -> np.ndarray:
        """Compute average order value (AOV).

        Formula: AOV = total_revenue / num_orders
        Safe division: returns 0.0 where num_orders == 0.

        Args:
            total_revenue: Array of aggregated revenue.
            num_orders: Array of order counts.

        Returns:
            1-D ndarray of AOV values.
        """
        rev = np.asarray(total_revenue, dtype=np.float64)
        n = np.asarray(num_orders, dtype=np.float64)
        return np.where(n != 0, rev / n, 0.0)

    @staticmethod
    def calculate_discount_depth(
        discount_amount: ArrayLike,
        original_price: ArrayLike,
    ) -> np.ndarray:
        """Compute discount depth as percentage of original price.

        Formula: depth% = (discount / original_price) * 100
        Safe division: returns 0.0 where original_price == 0.

        Args:
            discount_amount: Array of discount values.
            original_price: Array of original prices.

        Returns:
            1-D ndarray of discount depth percentages.
        """
        d = np.asarray(discount_amount, dtype=np.float64)
        p = np.asarray(original_price, dtype=np.float64)
        return np.where(p != 0, (d / p) * 100.0, 0.0)

    @staticmethod
    def calculate_return_rate(
        returns_count: ArrayLike,
        orders_count: ArrayLike,
    ) -> np.ndarray:
        """Compute return rate as percentage of orders returned.

        Formula: return_rate% = (returns / orders) * 100
        Safe division: returns 0.0 where orders == 0.

        Args:
            returns_count: Array of return counts.
            orders_count: Array of total order counts.

        Returns:
            1-D ndarray of return rate percentages.
        """
        ret = np.asarray(returns_count, dtype=np.float64)
        ord_ = np.asarray(orders_count, dtype=np.float64)
        return np.where(ord_ != 0, (ret / ord_) * 100.0, 0.0)
