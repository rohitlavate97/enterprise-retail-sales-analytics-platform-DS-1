"""Unit tests for configuration loading and validation."""

from pathlib import Path
import tempfile
import yaml
from config.settings import Settings, get_settings


def test_default_settings_loading() -> None:
    """Test loading default application settings from YAML."""
    settings = get_settings()
    assert settings.app.name == "Enterprise Retail Sales Analytics Platform"
    assert settings.data.seed == 42
    assert settings.data.default_num_orders == 100000
    assert settings.analytics.pareto_top_percent == 0.20


def test_custom_yaml_loading() -> None:
    """Test loading settings from a custom YAML configuration file."""
    custom_data = {
        "app": {"name": "Custom Platform Test", "env": "testing", "debug": False},
        "data": {"seed": 99, "default_num_orders": 500},
    }
    with tempfile.NamedTemporaryFile("w", suffix=".yaml", delete=False) as tmp:
        yaml.dump(custom_data, tmp)
        tmp_path = Path(tmp.name)

    try:
        settings = Settings.load_from_yaml(tmp_path)
        assert settings.app.name == "Custom Platform Test"
        assert settings.app.env == "testing"
        assert settings.data.seed == 99
        assert settings.data.default_num_orders == 500
    finally:
        if tmp_path.exists():
            tmp_path.unlink()


def test_environment_variable_override(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test environment variable overriding configuration values."""
    import pytest  # imported here for type hinting if needed

    monkeypatch.setenv("RETAIL_DATA__SEED", "777")
    monkeypatch.setenv("RETAIL_APP__NAME", "Overridden App")

    settings = Settings.load_from_yaml()
    assert settings.data.seed == 777
    assert settings.app.name == "Overridden App"
