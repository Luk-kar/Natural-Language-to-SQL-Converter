"""
Filters compatible plot types based on DataFrame's column structure.

A logic to determine which plot types are compatible
with a given DataFrame based on its column structure.
It checks for the presence of numeric and categorical columns
as required by each plot type,
ensuring that only
plots with matching data requirements
are considered for visualization generation.
"""

# Third-party
import pandas as pd

# Visualization
from app.backend.visualization.plot_router import validate_plot_function_names


def has_numeric_columns(df: pd.DataFrame, min_count: int = 1) -> bool:
    """Check if DataFrame contains at least min_count numeric columns."""
    return len(df.select_dtypes(include=["number"]).columns) >= min_count


def has_categorical_columns(df: pd.DataFrame, min_count: int = 1) -> bool:
    """Check if DataFrame contains at least min_count non-numeric columns."""
    return len(df.select_dtypes(exclude=["number"]).columns) >= min_count


def filter_compatible_plots(plot_list: list[str], df: pd.DataFrame) -> list[dict]:
    """
    Filters plot items based on DataFrame's column structure requirements.

    Requirements for each plot type:
    - plot_bar: 1+ categorical, 1+ numeric
    - plot_heatmap: 2+ categorical, 1+ numeric
    - plot_treemap: 2+ categorical, 1+ numeric
    - plot_scatter: 2+ numeric
    - plot_stacked_area: 1+ numeric
    - plot_ridge: All columns numeric
    - plot_histogram: 1+ numeric
    - plot_pie: 1+ categorical, 1+ numeric
    - plot_donut: 1+ categorical, 1+ numeric
    - plot_box: 1+ categorical, 1+ numeric
    """
    plot_requirements = {
        "plot_bar": lambda: has_categorical_columns(df, 1)
        and has_numeric_columns(df, 1),
        "plot_heatmap": lambda: has_categorical_columns(df, 2)
        and has_numeric_columns(df, 1),
        "plot_treemap": lambda: has_categorical_columns(df, 2)
        and has_numeric_columns(df, 1),
        "plot_scatter": lambda: has_numeric_columns(df, 2),
        "plot_stacked_area": lambda: has_numeric_columns(df, 1),
        "plot_ridge": lambda: len(df.columns) >= 2
        and all(pd.api.types.is_numeric_dtype(df[col]) for col in df.columns),
        "plot_histogram": lambda: has_numeric_columns(df, 1),
        "plot_pie": lambda: has_categorical_columns(df, 1)
        and has_numeric_columns(df, 1),
        "plot_donut": lambda: has_categorical_columns(df, 1)
        and has_numeric_columns(df, 1),
        "plot_box": lambda: has_categorical_columns(df, 1)
        and has_numeric_columns(df, 1),
    }

    validate_plot_function_names(plot_requirements.keys())

    return [
        plot
        for plot in plot_list
        if plot in plot_requirements and plot_requirements[plot]()
    ]
