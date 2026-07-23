"""Configuration settings module using Pydantic Settings and PyYAML loader.

Provides strongly-typed, validated application settings with reproducible defaults,
environment variable overrides, and single-source-of-truth configuration management.
"""

import os
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class AppConfig(BaseModel):
    """General application metadata settings."""

    name: str = "Enterprise Retail Sales Analytics Platform"
    version: str = "1.0.0"
    env: str = "development"
    debug: bool = True


class DataConfig(BaseModel):
    """Data paths and synthetic data generator configuration."""

    raw_dir: Path = Path("data/raw")
    processed_dir: Path = Path("data/processed")
    quarantine_dir: Path = Path("data/quarantine")
    logs_dir: Path = Path("logs")
    seed: int = 42
    default_num_customers: int = 10000
    default_num_products: int = 500
    default_num_orders: int = 100000
    start_date: str = "2023-01-01"
    end_date: str = "2024-12-31"


class AnalyticsConfig(BaseModel):
    """Analytics parameters and statistical threshold configuration."""

    pareto_top_percent: float = 0.20
    abc_class_a_threshold: float = 0.70
    abc_class_b_threshold: float = 0.90
    outlier_iqr_multiplier: float = 1.5
    outlier_zscore_threshold: float = 3.0


class StreamingConfig(BaseModel):
    """Near-real-time streaming simulation parameters."""

    feed_interval_seconds: float = 2.0
    buffer_capacity: int = 1000
    batch_window_seconds: float = 10.0


class LoggingConfig(BaseModel):
    """Structured logging configuration."""

    level: str = "INFO"
    format: str = "json"
    log_file: Path = Path("logs/app.log")


def _deep_update(base: dict[str, Any], update: dict[str, Any]) -> dict[str, Any]:
    """Recursively update a dictionary."""
    for key, value in update.items():
        if isinstance(value, dict) and key in base and isinstance(base[key], dict):
            _deep_update(base[key], value)
        else:
            base[key] = value
    return base


def _get_env_overrides(prefix: str = "RETAIL_", delimiter: str = "__") -> dict[str, Any]:
    """Extract environment variable overrides matching prefix."""
    overrides: dict[str, Any] = {}
    for env_name, env_val in os.environ.items():
        if env_name.startswith(prefix):
            key_path = env_name[len(prefix) :].lower().split(delimiter)
            curr = overrides
            for part in key_path[:-1]:
                curr = curr.setdefault(part, {})
            curr[key_path[-1]] = env_val
    return overrides


class Settings(BaseSettings):
    """Master application settings model.

    Loads defaults from config/default.yaml if available, allowing environment
    variables with the prefix RETAIL_ to override individual parameters.
    """

    model_config = SettingsConfigDict(
        env_prefix="RETAIL_",
        env_nested_delimiter="__",
        case_sensitive=False,
    )

    app: AppConfig = Field(default_factory=AppConfig)
    data: DataConfig = Field(default_factory=DataConfig)
    analytics: AnalyticsConfig = Field(default_factory=AnalyticsConfig)
    streaming: StreamingConfig = Field(default_factory=StreamingConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)

    @classmethod
    def load_from_yaml(cls, yaml_path: Path | str | None = None) -> "Settings":
        """Factory method to instantiate Settings populated from YAML file and env overrides."""
        target_path = (
            Path(__file__).parent / "default.yaml" if yaml_path is None else Path(yaml_path)
        )

        data: dict[str, Any] = {}
        if target_path.is_file():
            with open(target_path, encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}

        env_overrides = _get_env_overrides()
        merged = _deep_update(data, env_overrides)
        return cls(**merged)


@lru_cache(maxsize=1)
def get_settings(config_file: str | Path | None = None) -> Settings:
    """Returns a cached singleton Settings instance."""
    return Settings.load_from_yaml(config_file)
