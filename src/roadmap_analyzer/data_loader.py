"""Data loading functionality for the roadmap analyzer."""

from typing import List

import pandas as pd
import streamlit as st
from pydantic import ValidationError

from roadmap_analyzer.config import AppConfig
from roadmap_analyzer.models import WorkItem


def load_project_data(file_path: str, config: AppConfig) -> pd.DataFrame:
    """Load project data from Excel file.

    Attempts to read from "Items" sheet first, falls back to default sheet if not found.

    Args:
        file_path (str): Path to the Excel file containing project data
        config (AppConfig): Application configuration

    Returns:
        pd.DataFrame or None: DataFrame with project data if successful, None if failed
    """
    try:
        # First try to read from "Items" sheet
        try:
            df = pd.read_excel(file_path, sheet_name="Items")
            st.info("✅ Successfully loaded data from 'Items' sheet")
        except ValueError as e:
            # If "Items" sheet doesn't exist, try default sheet
            if "Worksheet named 'Items' not found" in str(e) or "Items" in str(e):
                st.warning("⚠️ 'Items' sheet not found, trying default sheet...")
                df = pd.read_excel(file_path)
                st.info("✅ Successfully loaded data from default sheet")
            else:
                raise e

        # Ensure required columns exist using config
        required_cols = config.data.required_columns
        missing_cols = [col for col in required_cols if col not in df.columns]

        if missing_cols:
            st.error(f"Missing required columns: {missing_cols}")
            return None

        # Convert due dates to datetime
        df["Due date"] = pd.to_datetime(df["Due date"])

        # Clean up dependency column (convert to int or None)
        # Make sure to handle NaN values properly
        df["Dependency"] = df["Dependency"].apply(lambda x: int(x) if pd.notna(x) else None)

        return df

    except FileNotFoundError:
        st.error(f"File not found: {file_path}")
        return None
    except Exception as e:
        st.error(f"Error loading file: {str(e)}")
        return None


def convert_to_work_items(df: pd.DataFrame, config: AppConfig) -> List[WorkItem]:
    """Convert DataFrame to a list of WorkItem objects.

    Args:
        df (pd.DataFrame): DataFrame with work item data
        config (AppConfig): Application configuration

    Returns:
        List[WorkItem]: List of validated WorkItem objects
    """
    if df is None or df.empty:
        return []

    work_items = []
    validation_errors = []

    # Convert each row to a WorkItem
    for _, row in df.iterrows():
        try:
            # Convert row to dict and create WorkItem
            # Handle NaN values for dependency field
            dependency = row["Dependency"]
            if pd.isna(dependency):
                dependency = None
            
            # Handle optional Start date field
            start_date = row.get("Start date")
            if pd.isna(start_date):
                start_date = None
            
            # Handle optional Priority field
            priority = row.get("Priority")
            if pd.isna(priority):
                priority = None

            item_data = {
                "position": row["Position"],
                "Item": row["Item"],
                "due_date": row["Due date"],
                "Start date": start_date,
                "Priority": priority,
                "dependency": dependency,
                "Best": row["Best"],
                "Likely": row["Likely"],
                "Worst": row["Worst"],
            }
            work_item = WorkItem(**item_data)
            work_items.append(work_item)

        except ValidationError as e:
            # Collect validation errors
            error_msg = f"Error in row {row['Position']}: {str(e)}"
            validation_errors.append(error_msg)

    # Display validation errors if any
    if validation_errors:
        st.error("Validation errors in work items:")
        for error in validation_errors:
            st.error(error)

    return work_items


def load_work_items(file_path: str, config: AppConfig) -> List[WorkItem]:
    """Load and convert work items from Excel file.

    This is a convenience function that combines load_project_data and convert_to_work_items.

    Args:
        file_path (str): Path to the Excel file
        config (AppConfig): Application configuration

    Returns:
        List[WorkItem]: List of validated WorkItem objects
    """
    df = load_project_data(file_path, config)
    return convert_to_work_items(df, config)


def validate_project_data(df):
    """Validate that the project data has the correct structure and content.

    Args:
        df (pd.DataFrame): DataFrame to validate

    Returns:
        bool: True if data is valid, False otherwise
    """
    if df is None or df.empty:
        st.error("No data to validate")
        return False

    # Check for required columns
    required_cols = ["Position", "Item", "Due date", "Dependency", "Best", "Likely", "Worst"]
    missing_cols = [col for col in required_cols if col not in df.columns]

    if missing_cols:
        st.error(f"Missing required columns: {missing_cols}")
        return False

    # Check for valid estimation values
    estimation_cols = ["Best", "Likely", "Worst"]
    for col in estimation_cols:
        if not pd.api.types.is_numeric_dtype(df[col]):
            st.error(f"Column '{col}' must contain numeric values")
            return False

        if (df[col] <= 0).any():
            st.error(f"Column '{col}' must contain positive values")
            return False

    # Check that Best <= Likely <= Worst
    invalid_estimates = df[(df["Best"] > df["Likely"]) | (df["Likely"] > df["Worst"])]
    if not invalid_estimates.empty:
        st.error("Invalid estimates found: Best must be <= Likely <= Worst")
        st.error(f"Invalid rows: {invalid_estimates.index.tolist()}")
        return False

    return True
