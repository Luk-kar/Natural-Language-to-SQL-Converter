"""
This module contains a function that runs a plotting function based on the
provided JSON/dict configuration.
"""

# Third-party
import pandas as pd

from backend.visualization.plots import (
    plot_bar,
    plot_heatmap,
    plot_treemap,
    plot_scatter,
    plot_stacked_area,
    plot_ridge,
    plot_histogram,
    plot_pie,
    plot_donut,
    plot_box,
)


def run_plot_function(config: dict):
    """
    Runs a plotting function based on the provided configuration.

    Args:
        config (dict): A dictionary with keys:
            - "plot_type": A string identifying the type of plot.
              Valid options: "plot_bar", "heatmap", "treemap", "scatter",
              "stacked_area", "ridge", "histogram", "pie", "donut", "box".
            - "arguments": A dictionary of keyword arguments to pass to the
              selected plotting function.

    Returns:
        The plot object returned by the selected plotting function.

    Example:
        config = {
            "plot_type": "treemap",
            "arguments": {
                "data": df,
                "group_columns": ["Region", "City"],
                "value_column": "Sales",
                "title": "Treemap Test"
            }
        }
        plot = run_plot_function(config)
    """
    # Mapping of plot types to their corresponding functions.
    plot_functions = {
        "plot_bar": plot_bar,
        "heatmap": plot_heatmap,
        "treemap": plot_treemap,
        "scatter": plot_scatter,
        "stacked_area": plot_stacked_area,
        "ridge": plot_ridge,
        "histogram": plot_histogram,
        "pie": plot_pie,
        "donut": plot_donut,
        "box": plot_box,
    }

    plot_type = config.get("plot_type")

    try:
        arguments = config.get("arguments")
        data = arguments.get("data")

        if not isinstance(data, pd.DataFrame):
            raise ValueError("Data must be a pandas DataFrame.")
    except AttributeError as e:
        raise ValueError(f"Invalid arguments provided:\n{str(e)}") from e

    if plot_type not in plot_functions:
        raise ValueError(f"Invalid plot type specified: {plot_type}")

    # Call the selected function using the provided keyword arguments.
    return plot_functions[plot_type](**arguments)
