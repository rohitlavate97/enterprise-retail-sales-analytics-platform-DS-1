"""Time Dimension synthetic calendar generator.

Generates a complete retail date dimension table spanning start and end dates,
with calendar attributes, weekend flags, and major retail holiday indicators.
"""

from datetime import date, datetime, timedelta
from typing import Any

import pandas as pd

from core.logging import get_logger

logger = get_logger(__name__)

# Standard US major retail holidays (Month, Day)
HOLIDAYS = {
    (1, 1): "New Year's Day",
    (7, 4): "Independence Day",
    (10, 31): "Halloween",
    (11, 25): "Thanksgiving / Black Friday Period",
    (11, 26): "Black Friday",
    (11, 28): "Cyber Monday",
    (12, 24): "Christmas Eve",
    (12, 25): "Christmas Day",
    (12, 31): "New Year's Eve",
}


class TimeDimensionGenerator:
    """Generator for retail calendar time dimension dataset."""

    def __init__(self, start_date: str = "2023-01-01", end_date: str = "2024-12-31") -> None:
        self.start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
        self.end_date = datetime.strptime(end_date, "%Y-%m-%d").date()

    def generate(self) -> pd.DataFrame:
        """Generates a complete time dimension calendar DataFrame.

        Returns:
            Pandas DataFrame conforming to TimeDimensionSchema.
        """
        logger.info(
            "Generating Time Dimension calendar from %s to %s...",
            self.start_date,
            self.end_date,
        )

        date_keys: list[int] = []
        full_dates: list[date] = []
        years: list[int] = []
        quarters: list[int] = []
        months: list[int] = []
        month_names: list[str] = []
        weeks: list[int] = []
        days_of_week: list[int] = []
        is_weekends: list[bool] = []
        is_holidays: list[bool] = []

        curr = self.start_date
        while curr <= self.end_date:
            date_key = int(curr.strftime("%Y%m%d"))
            year = curr.year
            quarter = (curr.month - 1) // 3 + 1
            month = curr.month
            month_name = curr.strftime("%B")
            week = curr.isocalendar().week
            dow = curr.weekday()  # 0=Monday, 6=Sunday
            weekend = dow in (5, 6)
            holiday = (month, curr.day) in HOLIDAYS

            date_keys.append(date_key)
            full_dates.append(curr)
            years.append(year)
            quarters.append(quarter)
            months.append(month)
            month_names.append(month_name)
            weeks.append(week)
            days_of_week.append(dow)
            is_weekends.append(weekend)
            is_holidays.append(holiday)

            curr += timedelta(days=1)

        data: dict[str, Any] = {
            "date_key": date_keys,
            "full_date": full_dates,
            "year": years,
            "quarter": quarters,
            "month": months,
            "month_name": month_names,
            "week_of_year": weeks,
            "day_of_week": days_of_week,
            "is_weekend": is_weekends,
            "is_holiday": is_holidays,
        }

        df = pd.DataFrame(data)
        logger.info("Successfully generated Time Dimension (shape: %s).", df.shape)
        return df
