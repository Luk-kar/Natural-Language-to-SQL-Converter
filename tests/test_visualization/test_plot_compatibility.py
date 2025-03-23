"""
Tests for determining plot compatibility based on dataset characteristics.

This module validates the logic for matching datasets to compatible plot types, including:
- Automatic derivation of plot arguments based on column types (numeric, categorical, etc.).
- Validation of plot viability for different data shapes (e.g., empty datasets, single-column datasets).
- End-to-end compatibility checks for hierarchical and relational data.

Tests ensure that the system suggests appropriate plot types for different data patterns and handles edge cases gracefully.
"""

# Python
import unittest

# Third-party
import pandas as pd

# Visualization
from app.backend.visualization.plot_filter import filter_compatible_plots
from app.backend.visualization.plot_router import validate_plot_function_names
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
)  # It has to be imported to be used in globals()


class TestPlotCompatibilityMatrix(unittest.TestCase):
    """
    Test suite for validating plot compatibility determination logic.

    This class tests the matching of DataFrame structures to compatible plots:
    - Automatic argument derivation based on column types
    - Validation of plot viability across data shapes
    - End-to-end plot generation for compatible matches
    - Edge case handling for empty/single-column datasets
    """

    @classmethod
    def setUpClass(cls):

        _plot_list = [
            "plot_bar",
            "plot_heatmap",
            "plot_treemap",
            "plot_scatter",
            "plot_stacked_area",
            "plot_ridge",
            "plot_histogram",
            "plot_pie",
            "plot_donut",
            "plot_box",
        ]

        validate_plot_function_names(_plot_list)

        cls.plot_list = _plot_list

    def validate_plot_selection(self, df, expected_plots):
        """Validate plot selection and actual plot generation"""

        compatible = filter_compatible_plots(self.plot_list, df)
        selected_names = {p for p in compatible}

        self.assertEqual(selected_names, expected_plots)

        # Validate plot generation for compatible plots
        for plot_name in selected_names:

            plot_func = globals()[plot_name]
            args = self._get_plot_arguments(plot_name, df)

            try:
                plot_func(data=df, **args)
            except (ValueError, TypeError) as e:
                self.fail(f"Plot {plot_name} failed with arguments {args}: {str(e)}")

    def _get_plot_arguments(self, plot_name, df):
        """Generate required arguments for each plot type"""
        numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()
        cat_cols = df.select_dtypes(exclude=["number"]).columns.tolist()

        arg_mapping = {
            "plot_bar": {
                "category_column": cat_cols[0] if cat_cols else None,
                "value_column": numeric_cols[0] if numeric_cols else None,
            },
            "plot_heatmap": {
                "x_column": cat_cols[0] if len(cat_cols) >= 1 else None,
                "y_column": cat_cols[1] if len(cat_cols) >= 2 else None,
                "value_column": numeric_cols[0] if numeric_cols else None,
            },
            "plot_treemap": {
                "group_columns": cat_cols[:2] if len(cat_cols) >= 2 else None,
                "value_column": numeric_cols[0] if numeric_cols else None,
            },
            "plot_scatter": {
                "x_column": numeric_cols[0] if len(numeric_cols) >= 1 else None,
                "y_column": numeric_cols[1] if len(numeric_cols) >= 2 else None,
            },
            "plot_pie": {
                "category_column": cat_cols[0] if cat_cols else None,
                "value_column": numeric_cols[0] if numeric_cols else None,
            },
            "plot_donut": {
                "category_column": cat_cols[0] if cat_cols else None,
                "value_column": numeric_cols[0] if numeric_cols else None,
            },
            "plot_box": {
                "x_column": cat_cols[0] if cat_cols else None,
                "y_column": numeric_cols[0] if numeric_cols else None,
            },
            "plot_ridge": {
                "to_include_only": df.columns.tolist() if not df.empty else None
            },
            "plot_stacked_area": {
                "to_include_only": numeric_cols if numeric_cols else None
            },
            "plot_histogram": {
                "value_column": numeric_cols[0] if numeric_cols else None
            },
        }

        validate_plot_function_names(arg_mapping.keys())

        return arg_mapping.get(plot_name, {})

    def test_single_numeric_column(self):
        df = pd.DataFrame({"value": [1, 2, 3]})
        expected = {"plot_stacked_area", "plot_histogram"}
        self.validate_plot_selection(df, expected)

    def test_mixed_column_types(self):
        df = pd.DataFrame(
            {"category": ["A", "B", "C"], "value": [1, 2, 3], "other_num": [4, 5, 6]}
        )
        expected = {
            "plot_bar",
            "plot_scatter",
            "plot_stacked_area",
            "plot_histogram",
            "plot_pie",
            "plot_donut",
            "plot_box",
        }
        self.validate_plot_selection(df, expected)

    def test_full_compatibility(self):
        df = pd.DataFrame(
            {
                "cat1": ["A", "B", "C"],
                "cat2": ["X", "Y", "Z"],
                "num1": [1, 2, 3],
                "num2": [4, 5, 6],
            }
        )
        expected = {
            "plot_bar",
            "plot_heatmap",
            "plot_treemap",
            "plot_scatter",
            "plot_stacked_area",
            "plot_histogram",
            "plot_pie",
            "plot_donut",
            "plot_box",
        }
        self.validate_plot_selection(df, expected)

    def test_edge_cases(self):
        # Empty DataFrame
        empty_df = pd.DataFrame()
        self.assertEqual(len(filter_compatible_plots(self.plot_list, empty_df)), 0)

        # Single column DataFrame
        single_cat = pd.DataFrame({"cat": ["A", "B"]})
        self.assertEqual(len(filter_compatible_plots(self.plot_list, single_cat)), 0)

        # All numeric ridge plot
        ridge_df = pd.DataFrame({"a": [1, 2], "b": [3, 4]})
        self.assertIn(
            "plot_ridge",
            [p for p in filter_compatible_plots(self.plot_list, ridge_df)],
        )
