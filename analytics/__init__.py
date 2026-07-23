"""Analytics package — NumPy-powered KPI, statistical, and rolling computations."""

from analytics.kpi_calculator import KPICalculator
from analytics.rolling_stats import RollingStatistics
from analytics.statistical import StatisticalAnalyzer

__all__ = ["KPICalculator", "RollingStatistics", "StatisticalAnalyzer"]
