"""Analytics package — NumPy-powered KPI, statistical, and rolling computations."""

from analytics.kpi_calculator import KPICalculator
from analytics.rolling_stats import RollingStatistics
from analytics.statistical import StatisticalAnalyzer
from analytics.aggregation import SalesAggregator
from analytics.pivot_analytics import PivotAnalytics
from analytics.enrichment import DataEnricher
from analytics.temporal import TemporalAnalytics

__all__ = [
    "KPICalculator",
    "RollingStatistics",
    "StatisticalAnalyzer",
    "SalesAggregator",
    "PivotAnalytics",
    "DataEnricher",
    "TemporalAnalytics",
]

