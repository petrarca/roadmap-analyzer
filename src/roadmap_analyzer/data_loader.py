"""Data loading functionality for the roadmap analyzer."""

from typing import List

import pandas as pd
import streamlit as st
from pydantic import ValidationError

from roadmap_analyzer.components import add_notification
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
            add_notification("✅ Successfully loaded data from 'Items' sheet", "success")
        except ValueError as e:
            # If "Items" sheet doesn't exist, try default sheet
            if "Worksheet named 'Items' not found" in str(e) or "Items" in str(e):
                add_notification("⚠️ 'Items' sheet not found, trying default sheet...", "warning")
                df = pd.read_excel(file_path)
                add_notification("✅ Successfully loaded data from default sheet", "success")
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

        # Convert start dates to datetime if the column exists
        if "Start date" in df.columns:
            df["Start date"] = pd.to_datetime(df["Start date"], errors="coerce")

        # Clean up dependency column for PyArrow compatibility
        # Convert to nullable integer type to avoid mixed type issues
        df["Dependency"] = df["Dependency"].astype("Int64")  # Nullable integer type

        return df

    except FileNotFoundError:
        add_notification(f"File not found: {file_path}", "error")
        return None
    except Exception as e:
        add_notification(f"Error loading file: {str(e)}", "error")
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
                "Start date": start_date,  # Uses alias for start_date field
                "Priority": priority,  # Uses alias for priority field
                "dependency": dependency,
                "Best": row["Best"],  # Uses alias for best_estimate field
                "Likely": row["Likely"],  # Uses alias for most_likely_estimate field
                "Worst": row["Worst"],  # Uses alias for worst_estimate field
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
