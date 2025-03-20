"""
Plotting function based on a provided JSON/dict configuration.

It maps a plot type specified in the configuration
to a corresponding plotting function,
validates the input data (ensuring it is a pandas DataFrame),
and executes the plot function
with the supplied arguments.

In plain English,
the module acts as a dispatcher that selects
the appropriate plot from a collection of visualization functions
and then runs it.
"""

# Python
import re
import inspect

# Third-party
import pandas as pd

from app.backend.visualization import plots
from app.backend.visualization.plots import (
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

# Bokeh
from bokeh.plotting import figure

plots_list = [
    name
    for name, obj in inspect.getmembers(plots, inspect.isfunction)
    if re.match(r"plot_.+", name)
]


def get_plot_function(config: dict) -> figure:
    """
    Returns a plot based on the provided data and configuration.

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
        plot = get_plot_function(config)
    """
    # Mapping of plot types to their corresponding functions.
    plot_functions = {
        "bar": plot_bar,
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

    validate_plot_function_names("plot_" + name for name in plot_functions)

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


def validate_plot_function_names(plot_functions: list[str]):
    """
    Validate that the plot function names match the expected
    """

    expected_keys = set(plot_functions)
    actual_keys = set(plots_list)

    if expected_keys != actual_keys:
        diff = {
            "missing_in_module": list(expected_keys - actual_keys),
            "unexpected_in_module": list(actual_keys - expected_keys),
        }
        raise ValueError(
            "Plot function names mismatch:\n"
            f"missing_in_module:    {diff['missing_in_module']}\n"
            f"unexpected_in_module: {diff['unexpected_in_module']}"
        )
