"""
This module provides functions to generate a visualization context from an SQL query result.
The visualization context is a structured dictionary that includes:
- list of compatible plot configurations
- summary of the dataset (row count, column types, and sample values).

In plain English, it prepares the necessary information
so that a plotting system or language model can later
decide which plot to create and how to map data columns
to the plot’s arguments.
"""

# Third-party
import pandas as pd

# Visualization
from app.backend.visualization.generator import plots_list
from app.backend.visualization.plot_filter import filter_compatible_plots
from app.backend.visualization.plot_details_extractor import (
    retrieve_plot_function_details,
)


def build_visualization_context(execution_result: dict) -> dict:
    """
    Build a comprehensive context for visualization generation from an SQL query result.

    The function extracts compatible plot configurations, filters the available
    plot functions based on compatibility, and summarizes dataset information.

    Args:
        execution_result (dict): A dictionary containing 'columns' and 'data' from an SQL query.

    Returns:
        dict: A context dictionary that includes:
            - 'compatible_plots': A list of available and compatible plot configurations.
            - 'data_context': Information about the dataset including row count,
                              column types, and sample values.
            - 'error': An error message if context generation fails.
    """
    context = {"compatible_plots": [], "data_context": {}, "error": None}

    try:
        # Get compatible plot names from previous filtering
        compatible_plots = filter_plots_for_dataset(execution_result)
        compatible_names = set(compatible_plots)

        # Get all available plot functions from the codebase
        all_plots = retrieve_plot_function_details()

        # Filter to only include compatible plots
        filtered_plots = [
            plot for plot in all_plots if plot["name"] in compatible_names
        ]

        # Trim the plot metadata for LLM consumption
        context["compatible_plots"] = [
            {
                "name": plot["name"],
                "interface": plot.get("interface", ""),
                "description": plot.get("description", ""),
                "dict_args": plot.get("dict_args", {}),
            }
            for plot in filtered_plots
        ]

        # Add dataset context
        df = pd.DataFrame(execution_result["data"], columns=execution_result["columns"])
        context["data_context"] = {
            "row_count": len(df),
            "columns": {col: str(df[col].dtype) for col in df.columns},
            "sample_3_values": {
                col: df[col].dropna().head(3).tolist() for col in df.columns
            },
        }

    except Exception as e:
        context["error"] = f"Context generation failed:\n{str(e)}"

    return context


def filter_plots_for_dataset(execution_result: dict) -> list[dict]:
    """
    Identify plot configurations that are compatible with the given SQL query result.

    This function converts the query execution result into a DataFrame and uses
    a filtering utility to determine which plot types can be used with the data.

    Args:
        execution_result (dict): A dictionary containing 'columns' and 'data' from an SQL query.

    Returns:
        list[dict]: A list of plot configurations that are compatible with the dataset.

    Raises:
        ValueError: If the execution result format is invalid.
    """
    if (
        not execution_result
        or "data" not in execution_result
        or "columns" not in execution_result
    ):
        raise ValueError(f"Invalid execution result format.\n{execution_result}")

    try:
        df = pd.DataFrame(execution_result["data"], columns=execution_result["columns"])
        return filter_compatible_plots(plots_list, df)
    except Exception as e:
        return []
