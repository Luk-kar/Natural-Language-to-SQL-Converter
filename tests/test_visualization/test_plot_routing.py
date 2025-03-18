"""
Tests for routing plot configurations to the appropriate plot functions.

This module validates the system's ability to:
- Correctly route valid configurations to their corresponding plot functions.
- Handle errors for invalid plot types or configurations.
- Enforce argument validation and provide clear error messages.

Tests ensure that the routing logic is robust, user-friendly, and handles edge cases effectively.
"""

# Python
import unittest

# Visualization
from app.backend.visualization.plot_context_selector import (
    filter_plots_for_dataset,
)


class TestPlotContextSelector(unittest.TestCase):
    """
    Test suite for validating plot recommendation based on data characteristics.

    This class tests:
    - Detection of numeric/categorical column combinations
    - Appropriate plot type suggestions for different data patterns
    - Handling of malformed or incomplete dataset inputs
    - Special case handling for hierarchical and relational data
    """

    def test_two_numeric_columns(self):
        """Test that plots requiring numeric data are identified correctly."""
        execution_result = {"columns": ["age", "score"], "data": [[25, 85], [30, 90]]}
        compatible_plots = set(filter_plots_for_dataset(execution_result))

        expected_plots = {
            "plot_histogram",
            "plot_stacked_area",
            "plot_scatter",
            "plot_ridge",
        }
        self.assertTrue(
            compatible_plots.issuperset(expected_plots),
            f"Expected plots include:\n{expected_plots}\ngot:\n{compatible_plots}",
        )

    def test_one_categorical_one_numeric(self):
        """Test that plots requiring one categorical and one numeric column are identified."""
        execution_result = {
            "columns": ["category", "count"],
            "data": [["A", 10], ["B", 20]],
        }
        compatible_plots = set(filter_plots_for_dataset(execution_result))

        expected_plots = {
            "plot_histogram",
            "plot_donut",
            "plot_stacked_area",
            "plot_box",
            "plot_bar",
            "plot_pie",
        }
        self.assertTrue(
            compatible_plots.issuperset(expected_plots),
            f"Expected plots include:\n{expected_plots}\ngot:\n{compatible_plots}",
        )

    def test_heatmap_compatible_data(self):
        """Test that heatmap is identified as compatible for two categorical and one numeric column."""
        execution_result = {
            "columns": ["region", "product", "sales"],
            "data": [["North", "Widget", 150], ["South", "Gadget", 200]],
        }
        compatible_plots = filter_plots_for_dataset(execution_result)

        self.assertIn(
            "plot_heatmap",
            compatible_plots,
            f"Heatmap should be compatible with two categorical and one numeric column, got:\n{compatible_plots}",
        )

    def test_empty_data(self):
        """Test that no plots are returned for empty data."""
        execution_result = {"columns": [], "data": []}
        compatible_plots = filter_plots_for_dataset(execution_result)
        self.assertEqual(
            len(compatible_plots),
            0,
            f"Expected no compatible plots for empty data, got:\n{compatible_plots}",
        )

    def test_missing_keys(self):
        """Test that a ValueError is raised when required keys are missing."""

        execution_result = {"error": "Invalid query"}
        with self.assertRaises(ValueError) as context:
            filter_plots_for_dataset(execution_result)

        self.assertIn("Invalid execution result format", str(context.exception))
