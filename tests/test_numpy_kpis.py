"""Correctness tests for NumPy KPI, rolling, and statistical modules.

Each test verifies computed results against hand-calculated fixture values
to ensure mathematical correctness of vectorized implementations.
"""

import numpy as np
import pytest

from analytics.kpi_calculator import KPICalculator
from analytics.rolling_stats import RollingStatistics
from analytics.statistical import StatisticalAnalyzer

# ── KPI Calculator Tests ──────────────────────────────────


class TestKPICalculator:
    """Tests for vectorized KPI calculations."""

    def test_revenue_calculation(self) -> None:
        """revenue = qty * price - discount."""
        qty = np.array([2, 5, 10])
        price = np.array([10.0, 20.0, 5.0])
        discount = np.array([1.0, 0.0, 5.0])
        result = KPICalculator.calculate_revenue(qty, price, discount)
        expected = np.array([19.0, 100.0, 45.0])
        np.testing.assert_array_almost_equal(result, expected)

    def test_profit_margin(self) -> None:
        """margin% = (profit / revenue) * 100."""
        profit = np.array([10.0, 25.0, 0.0])
        revenue = np.array([100.0, 50.0, 0.0])
        result = KPICalculator.calculate_profit_margin(profit, revenue)
        expected = np.array([10.0, 50.0, 0.0])
        np.testing.assert_array_almost_equal(result, expected)

    def test_gross_margin(self) -> None:
        """gross_margin% = ((rev - cost) / rev) * 100."""
        revenue = np.array([100.0, 200.0, 0.0])
        cost = np.array([60.0, 150.0, 0.0])
        result = KPICalculator.calculate_gross_margin(revenue, cost)
        expected = np.array([40.0, 25.0, 0.0])
        np.testing.assert_array_almost_equal(result, expected)

    def test_yoy_growth(self) -> None:
        """yoy% = ((current - previous) / previous) * 100."""
        current = np.array([120.0, 80.0, 100.0])
        previous = np.array([100.0, 100.0, 0.0])
        result = KPICalculator.calculate_yoy_growth(current, previous)
        expected = np.array([20.0, -20.0, 0.0])
        np.testing.assert_array_almost_equal(result, expected)

    def test_average_order_value(self) -> None:
        """AOV = total_revenue / num_orders."""
        revenue = np.array([1000.0, 500.0, 0.0])
        orders = np.array([10.0, 5.0, 0.0])
        result = KPICalculator.calculate_average_order_value(revenue, orders)
        expected = np.array([100.0, 100.0, 0.0])
        np.testing.assert_array_almost_equal(result, expected)

    def test_discount_depth(self) -> None:
        """depth% = (discount / original_price) * 100."""
        discount = np.array([5.0, 0.0, 20.0])
        price = np.array([100.0, 50.0, 0.0])
        result = KPICalculator.calculate_discount_depth(discount, price)
        expected = np.array([5.0, 0.0, 0.0])
        np.testing.assert_array_almost_equal(result, expected)

    def test_return_rate(self) -> None:
        """return_rate% = (returns / orders) * 100."""
        returns = np.array([2.0, 0.0, 5.0])
        orders = np.array([100.0, 50.0, 0.0])
        result = KPICalculator.calculate_return_rate(returns, orders)
        expected = np.array([2.0, 0.0, 0.0])
        np.testing.assert_array_almost_equal(result, expected)

    def test_accepts_pandas_series(self) -> None:
        """KPIs accept pandas Series transparently."""
        import pandas as pd

        qty = pd.Series([3, 4])
        price = pd.Series([10.0, 20.0])
        disc = pd.Series([0.0, 5.0])
        result = KPICalculator.calculate_revenue(qty, price, disc)
        expected = np.array([30.0, 75.0])
        np.testing.assert_array_almost_equal(result, expected)


# ── Rolling Statistics Tests ──────────────────────────────


class TestRollingStatistics:
    """Tests for rolling window computations."""

    def test_simple_moving_average(self) -> None:
        """SMA(3) of [1,2,3,4,5] -> [nan, nan, 2, 3, 4]."""
        values = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        result = RollingStatistics.simple_moving_average(values, 3)
        assert np.isnan(result[0])
        assert np.isnan(result[1])
        np.testing.assert_almost_equal(result[2], 2.0)
        np.testing.assert_almost_equal(result[3], 3.0)
        np.testing.assert_almost_equal(result[4], 4.0)

    def test_exponential_moving_average(self) -> None:
        """EMA starts with first value and decays."""
        values = np.array([10.0, 10.0, 10.0, 10.0])
        result = RollingStatistics.exponential_moving_average(values, 3)
        # Constant input -> all EMA values should be 10.0
        np.testing.assert_array_almost_equal(result, np.array([10.0, 10.0, 10.0, 10.0]))

    def test_weighted_moving_average(self) -> None:
        """WMA with linear weights [1,2,3] on [1,2,3,4,5]."""
        values = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        weights = np.array([1.0, 2.0, 3.0])
        result = RollingStatistics.weighted_moving_average(values, weights)
        # WMA at index 2: (1*1 + 2*2 + 3*3) / 6 = 14/6 ≈ 2.333
        assert np.isnan(result[0])
        assert np.isnan(result[1])
        expected_2 = (1 * 1 + 2 * 2 + 3 * 3) / 6
        np.testing.assert_almost_equal(result[2], expected_2)

    def test_rolling_std(self) -> None:
        """Rolling std of constant array should be 0."""
        values = np.array([5.0, 5.0, 5.0, 5.0, 5.0])
        result = RollingStatistics.rolling_std(values, 3)
        assert np.isnan(result[0])
        assert np.isnan(result[1])
        np.testing.assert_almost_equal(result[2], 0.0)

    def test_rolling_min_max(self) -> None:
        """Rolling min/max of [1,3,2,5,4] window=3."""
        values = np.array([1.0, 3.0, 2.0, 5.0, 4.0])
        r_min, r_max = RollingStatistics.rolling_min_max(values, 3)
        np.testing.assert_almost_equal(r_min[2], 1.0)
        np.testing.assert_almost_equal(r_max[2], 3.0)
        np.testing.assert_almost_equal(r_min[3], 2.0)
        np.testing.assert_almost_equal(r_max[3], 5.0)

    def test_cumulative_sum(self) -> None:
        """Cumulative sum of [1,2,3] -> [1,3,6]."""
        values = np.array([1.0, 2.0, 3.0])
        result = RollingStatistics.cumulative_sum(values)
        np.testing.assert_array_almost_equal(result, np.array([1.0, 3.0, 6.0]))

    def test_cumulative_growth_rate(self) -> None:
        """Growth from 100 -> [0%, 10%, 20%]."""
        values = np.array([100.0, 110.0, 120.0])
        result = RollingStatistics.cumulative_growth_rate(values)
        expected = np.array([0.0, 10.0, 20.0])
        np.testing.assert_array_almost_equal(result, expected)


# ── Statistical Analyzer Tests ────────────────────────────


class TestStatisticalAnalyzer:
    """Tests for normalization and correlation functions."""

    def test_z_score_normalize(self) -> None:
        """Z-score of [1, 2, 3] -> mean=2, std=0.816..."""
        values = np.array([1.0, 2.0, 3.0])
        result = StatisticalAnalyzer.z_score_normalize(values)
        assert abs(result.mean()) < 1e-10
        assert abs(result.std() - 1.0) < 1e-10

    def test_z_score_constant_array(self) -> None:
        """Z-score of constant array -> all zeros."""
        values = np.array([5.0, 5.0, 5.0])
        result = StatisticalAnalyzer.z_score_normalize(values)
        np.testing.assert_array_equal(result, np.zeros(3))

    def test_min_max_normalize(self) -> None:
        """Min-max of [0, 50, 100] to [0, 1] -> [0, 0.5, 1]."""
        values = np.array([0.0, 50.0, 100.0])
        result = StatisticalAnalyzer.min_max_normalize(values)
        expected = np.array([0.0, 0.5, 1.0])
        np.testing.assert_array_almost_equal(result, expected)

    def test_min_max_custom_range(self) -> None:
        """Min-max to custom range [-1, 1]."""
        values = np.array([0.0, 50.0, 100.0])
        result = StatisticalAnalyzer.min_max_normalize(values, feature_range=(-1.0, 1.0))
        expected = np.array([-1.0, 0.0, 1.0])
        np.testing.assert_array_almost_equal(result, expected)

    def test_robust_normalize(self) -> None:
        """Robust norm uses median and IQR."""
        values = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        result = StatisticalAnalyzer.robust_normalize(values)
        # median=3, q1=2, q3=4, iqr=2
        expected = (values - 3.0) / 2.0
        np.testing.assert_array_almost_equal(result, expected)

    def test_pearson_correlation(self) -> None:
        """Perfect positive correlation -> r = 1.0."""
        x = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        y = np.array([2.0, 4.0, 6.0, 8.0, 10.0])
        r = StatisticalAnalyzer.pearson_correlation(x, y)
        assert abs(r - 1.0) < 1e-10

    def test_correlation_matrix_shape(self) -> None:
        """Correlation matrix of 3 vars -> 3x3 matrix."""
        data = {
            "a": np.array([1.0, 2.0, 3.0]),
            "b": np.array([4.0, 5.0, 6.0]),
            "c": np.array([7.0, 8.0, 9.0]),
        }
        corr, names = StatisticalAnalyzer.correlation_matrix(data)
        assert corr.shape == (3, 3)
        assert names == ["a", "b", "c"]
        # Diagonal should be 1.0
        np.testing.assert_array_almost_equal(np.diag(corr), np.ones(3))

    def test_covariance_matrix_shape(self) -> None:
        """Covariance matrix of 2 vars -> 2x2 matrix."""
        data = {
            "x": np.array([1.0, 2.0, 3.0]),
            "y": np.array([4.0, 5.0, 6.0]),
        }
        cov, names = StatisticalAnalyzer.covariance_matrix(data)
        assert cov.shape == (2, 2)
        assert names == ["x", "y"]

    def test_descriptive_statistics(self) -> None:
        """Descriptive stats of [1,2,3,4,5]."""
        values = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        stats = StatisticalAnalyzer.descriptive_statistics(values)
        assert stats["mean"] == pytest.approx(3.0)
        assert stats["median"] == pytest.approx(3.0)
        assert stats["min"] == pytest.approx(1.0)
        assert stats["max"] == pytest.approx(5.0)
        assert stats["range"] == pytest.approx(4.0)
        assert stats["skewness"] == pytest.approx(0.0, abs=1e-10)
