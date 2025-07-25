"""Data loading functionality for the roadmap analyzer."""

from typing import List

import pandas as pd
import streamlit as st
from pydantic import ValidationError

from roadmap_analyzer.models import WorkItem


def load_project_data(file_path):
    """Load project data from Excel file.

    Args:
        file_path (str): Path to the Excel file containing project data

    Returns:
        pd.DataFrame or None: DataFrame with project data if successful, None if failed
    """
    try:
        df = pd.read_excel(file_path)

        # Ensure required columns exist
        required_cols = ["Position", "Initiative", "Due date", "Dependency", "Best", "Most likely", "Worst"]
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


def convert_to_work_items(df: pd.DataFrame) -> List[WorkItem]:
    """Convert DataFrame to a list of WorkItem objects.

    Args:
        df (pd.DataFrame): DataFrame with work item data

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
                
            item_data = {
                "position": row["Position"],
                "initiative": row["Initiative"],
                "due_date": row["Due date"],
                "dependency": dependency,
                "Best": row["Best"],
                "Most likely": row["Most likely"],
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


def load_work_items(file_path: str) -> List[WorkItem]:
    """Load and convert work items from Excel file.

    This is a convenience function that combines load_project_data and convert_to_work_items.

    Args:
        file_path (str): Path to the Excel file

    Returns:
        List[WorkItem]: List of validated WorkItem objects
    """
    df = load_project_data(file_path)
    return convert_to_work_items(df)


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
    required_cols = ["Position", "Initiative", "Due date", "Dependency", "Best", "Most likely", "Worst"]
    missing_cols = [col for col in required_cols if col not in df.columns]

    if missing_cols:
        st.error(f"Missing required columns: {missing_cols}")
        return False

    # Check for valid estimation values
    estimation_cols = ["Best", "Most likely", "Worst"]
    for col in estimation_cols:
        if not pd.api.types.is_numeric_dtype(df[col]):
            st.error(f"Column '{col}' must contain numeric values")
            return False

        if (df[col] <= 0).any():
            st.error(f"Column '{col}' must contain positive values")
            return False

    # Check that Best <= Most likely <= Worst
    invalid_estimates = df[(df["Best"] > df["Most likely"]) | (df["Most likely"] > df["Worst"])]
    if not invalid_estimates.empty:
        st.error("Invalid estimates found: Best must be <= Most likely <= Worst")
        st.error(f"Invalid rows: {invalid_estimates.index.tolist()}")
        return False

    return True
