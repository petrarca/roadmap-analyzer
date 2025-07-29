"""Configuration settings for the roadmap analyzer using Pydantic models."""

from typing import List

from pydantic import BaseModel, ConfigDict, Field

__all__ = ["AppConfig", "SimulationConfig", "UIConfig", "DataConfig", "load_config"]


class SimulationConfig(BaseModel):
    """Configuration for Monte Carlo simulation with validation."""

    default_capacity_per_quarter: int = Field(default=1300, ge=1, description="Default quarterly capacity in person-days")
    default_num_simulations: int = Field(default=20000, ge=100, le=100000, description="Default number of simulation runs")
    simulation_options: List[int] = Field(default=[5000, 10000, 20000], description="Available simulation count options")


class UIConfig(BaseModel):
    """Configuration for the user interface."""

    page_title: str = Field(default="Project Roadmap Monte Carlo Analysis", description="Application page title")
    page_icon: str = Field(default="📊", description="Page icon for browser tab")
    layout: str = Field(default="wide", description="Streamlit layout mode")


class DataConfig(BaseModel):
    """Configuration for data processing."""

    required_columns: List[str] = Field(
        default=["Position", "Item", "Due date", "Dependency", "Best", "Likely", "Worst"], description="Required columns in Excel input"
    )


class AppConfig(BaseModel):
    """Main application configuration combining all sub-configurations."""

    simulation: SimulationConfig = Field(default_factory=SimulationConfig, description="Simulation settings")
    ui: UIConfig = Field(default_factory=UIConfig, description="UI settings")
    data: DataConfig = Field(default_factory=DataConfig, description="Data processing settings")

    # Pydantic configuration
    model_config = ConfigDict(validate_assignment=True, extra="forbid")


def load_config() -> AppConfig:
    """Load and return the application configuration.

    Returns:
        AppConfig: The application configuration instance
    """
    return AppConfig()
