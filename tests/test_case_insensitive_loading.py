"""Tests for case-insensitive Excel loading functionality."""

import os
import tempfile

import pandas as pd
import pytest

from roadmap_analyzer.capacity_loader import load_capacity_data
from roadmap_analyzer.config import load_config
from roadmap_analyzer.config_loader import load_config_from_excel
from roadmap_analyzer.data_loader import load_project_data
from roadmap_analyzer.loader_utils import create_column_mapping, find_sheet_name_case_insensitive


@pytest.fixture
def app_config():
    """Create a test app configuration."""
    return load_config()


def create_test_excel_with_case_variations(temp_path, sheet_name_case, column_name_case):
    """Create a test Excel file with specified case variations.

    Args:
        temp_path: Path to create the Excel file
        sheet_name_case: Case style for sheet names ('lower', 'upper', 'mixed')
        column_name_case: Case style for column names ('lower', 'upper', 'mixed')
    """
    # Define sheet names with specified case
    if sheet_name_case == "lower":
        items_sheet = "items"
        config_sheet = "config"
        capacity_sheet = "capacity"
    elif sheet_name_case == "upper":
        items_sheet = "ITEMS"
        config_sheet = "CONFIG"
        capacity_sheet = "CAPACITY"
    else:  # mixed
        items_sheet = "Items"
        config_sheet = "ConFig"
        capacity_sheet = "CaPaciTy"

    # Define column names with specified case
    if column_name_case == "lower":
        # Items sheet columns
        position_col = "position"
        item_col = "item"
        due_date_col = "due date"
        dependency_col = "dependency"
        best_col = "best"
        likely_col = "likely"
        worst_col = "worst"

        # Config sheet columns
        config_col = "config"
        value_col = "value"

        # Capacity sheet columns
        period_col = "period"
        capacity_col = "capacity"
    elif column_name_case == "upper":
        # Items sheet columns
        position_col = "POSITION"
        item_col = "ITEM"
        due_date_col = "DUE DATE"
        dependency_col = "DEPENDENCY"
        best_col = "BEST"
        likely_col = "LIKELY"
        worst_col = "WORST"

        # Config sheet columns
        config_col = "CONFIG"
        value_col = "VALUE"

        # Capacity sheet columns
        period_col = "PERIOD"
        capacity_col = "CAPACITY"
    else:  # mixed
        # Items sheet columns
        position_col = "Position"
        item_col = "iTem"
        due_date_col = "Due Date"
        dependency_col = "DepenDency"
        best_col = "bEst"
        likely_col = "LiKely"
        worst_col = "woRST"

        # Config sheet columns
        config_col = "ConFig"
        value_col = "VaLue"

        # Capacity sheet columns
        period_col = "PeRiod"
        capacity_col = "CaPaCity"

    # Create test data for Items sheet
    items_data = pd.DataFrame(
        {
            position_col: [1, 2, 3],
            item_col: ["Project A", "Project B", "Project C"],
            due_date_col: ["2025-11-30", "2025-11-30", "2026-05-30"],
            dependency_col: [None, 1, None],
            best_col: [2400, 250, 1400],
            likely_col: [2832, 295, 1652],
            worst_col: [3120, 325, 1820],
        }
    )

    # Create test data for Config sheet
    config_data = pd.DataFrame(
        {
            config_col: ["Start date", "Time period", "Capacity", "Iterations"],
            value_col: ["2025-01-15", "quarterly", 1500, 20000],
        }
    )

    # Create test data for Capacity sheet
    capacity_data = pd.DataFrame(
        {
            period_col: ["2025.Q1", "2025.Q2", "2025.Q3", "2025.Q4"],
            capacity_col: [1500, 1600, 1200, 1400],
        }
    )

    # Write to Excel file with multiple sheets
    with pd.ExcelWriter(temp_path, engine="openpyxl") as writer:
        items_data.to_excel(writer, sheet_name=items_sheet, index=False)
        config_data.to_excel(writer, sheet_name=config_sheet, index=False)
        capacity_data.to_excel(writer, sheet_name=capacity_sheet, index=False)


def test_case_insensitive_sheet_names(app_config):
    """Test that sheet names are found regardless of case."""
    # Test with lowercase sheet names
    with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as temp_file:
        temp_path = temp_file.name

    try:
        create_test_excel_with_case_variations(temp_path, "lower", "mixed")

        # Test data loader with lowercase sheet name
        df = load_project_data(temp_path, app_config)
        assert df is not None
        assert len(df) == 3

        # Test config loader with lowercase sheet name
        config_dict = load_config_from_excel(temp_path, app_config)
        assert config_dict is not None
        assert "Start date" in config_dict

        # Test capacity loader with lowercase sheet name
        capacity_dict = load_capacity_data(temp_path)
        assert capacity_dict is not None
        assert len(capacity_dict) == 4
    finally:
        # Clean up
        os.unlink(temp_path)

    # Test with uppercase sheet names
    with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as temp_file:
        temp_path = temp_file.name

    try:
        create_test_excel_with_case_variations(temp_path, "upper", "mixed")

        # Test data loader with uppercase sheet name
        df = load_project_data(temp_path, app_config)
        assert df is not None
        assert len(df) == 3

        # Test config loader with uppercase sheet name
        config_dict = load_config_from_excel(temp_path, app_config)
        assert config_dict is not None
        assert "Start date" in config_dict

        # Test capacity loader with uppercase sheet name
        capacity_dict = load_capacity_data(temp_path)
        assert capacity_dict is not None
        assert len(capacity_dict) == 4
    finally:
        # Clean up
        os.unlink(temp_path)


def test_case_insensitive_column_names(app_config):
    """Test that column names are found regardless of case."""
    # Test with lowercase column names
    with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as temp_file:
        temp_path = temp_file.name

    try:
        create_test_excel_with_case_variations(temp_path, "mixed", "lower")

        # Test data loader with lowercase column names
        df = load_project_data(temp_path, app_config)
        assert df is not None
        assert len(df) == 3

        # Verify column access works
        column_mapping = create_column_mapping(df.columns)
        assert "position" in column_mapping
        assert "due date" in column_mapping

        # Test config loader with lowercase column names
        config_dict = load_config_from_excel(temp_path, app_config)
        assert config_dict is not None
        assert "Start date" in config_dict

        # Test capacity loader with lowercase column names
        capacity_dict = load_capacity_data(temp_path)
        assert capacity_dict is not None
        assert len(capacity_dict) == 4
    finally:
        # Clean up
        os.unlink(temp_path)

    # Test with uppercase column names
    with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as temp_file:
        temp_path = temp_file.name

    try:
        create_test_excel_with_case_variations(temp_path, "mixed", "upper")

        # Test data loader with uppercase column names
        df = load_project_data(temp_path, app_config)
        assert df is not None
        assert len(df) == 3

        # Verify column access works
        column_mapping = create_column_mapping(df.columns)
        assert "position" in column_mapping
        assert "due date" in column_mapping

        # Test config loader with uppercase column names
        config_dict = load_config_from_excel(temp_path, app_config)
        assert config_dict is not None
        assert "Start date" in config_dict

        # Test capacity loader with uppercase column names
        capacity_dict = load_capacity_data(temp_path)
        assert capacity_dict is not None
        assert len(capacity_dict) == 4
    finally:
        # Clean up
        os.unlink(temp_path)


def test_mixed_case_variations(app_config):
    """Test with mixed case variations for both sheet names and column names."""
    with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as temp_file:
        temp_path = temp_file.name

    try:
        create_test_excel_with_case_variations(temp_path, "mixed", "mixed")

        # Test data loader
        df = load_project_data(temp_path, app_config)
        assert df is not None
        assert len(df) == 3

        # Test config loader
        config_dict = load_config_from_excel(temp_path, app_config)
        assert config_dict is not None
        assert "Start date" in config_dict

        # Test capacity loader
        capacity_dict = load_capacity_data(temp_path)
        assert capacity_dict is not None
        assert len(capacity_dict) == 4

        # Verify that the helper functions work correctly
        excel_file = pd.ExcelFile(temp_path)
        items_sheet = find_sheet_name_case_insensitive(excel_file.sheet_names, "items")
        assert items_sheet is not None
        assert items_sheet.lower() == "items"

        # Read the sheet and verify column mapping works
        sheet_df = pd.read_excel(temp_path, sheet_name=items_sheet)
        column_mapping = create_column_mapping(sheet_df.columns)
        assert "position" in column_mapping
        assert "item" in column_mapping
        assert "due date" in column_mapping
    finally:
        # Clean up
        os.unlink(temp_path)
