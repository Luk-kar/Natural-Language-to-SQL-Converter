"""
Tests for assembling and formatting visualization contexts.

This module validates the generation of comprehensive visualization contexts, including:
- Extraction of dataset metadata (e.g., row count, column types, sample values).
- Integration of plot compatibility results with dataset characteristics.
- Formatting of user-facing instructions for plot selection.

Tests ensure that the context assembly process is accurate, handles invalid inputs gracefully, and produces well-structured outputs.
"""

# Python
import unittest
from unittest.mock import patch

# Visualization
from app.backend.visualization.plot_context_selector import (
    build_visualization_context,
)
from app.backend.visualization.plot_instruction_prompt_formatter import (
    format_plot_selection_instructions,
)


class TestPlotContextBuilder(unittest.TestCase):
    """
    Test suite for validating the generation of a comprehensive visualization
    context from a dataset and compatible plots.

    This class tests the assembly of all necessary metadata for visualization,
    including:
    - Extraction of plot function details (name, interface, arguments, descriptions)
    - Construction of dataset context (row count, column types, sample values)
    - Error handling for invalid or incomplete input data
    - Integration of plot compatibility results with dataset metadata
    - Proper formatting of the final visualization context for downstream use
    """

    def setUp(self):
        self.valid_execution_result = {
            "columns": ["age", "score"],
            "data": [[25, 85], [30, 90], [35, 95]],
        }

        self.categorical_numeric_result = {
            "columns": ["category", "count"],
            "data": [["A", 10], ["B", 20]],
        }

        self.only_categorical_result = {
            "columns": ["category"],
            "data": [["A"], ["B"], ["C"]],
        }

    @patch("app.backend.visualization.plot_context_selector.filter_plots_for_dataset")
    @patch(
        "app.backend.visualization.plot_context_selector.retrieve_plot_function_details"
    )
    def test_valid_plot_extraction(self, mock_extract, filter_plots_for_dataset):
        """Test with valid data and compatible plots"""

        # Mock dependencies
        filter_plots_for_dataset.return_value = ["plot_scatter"]
        mock_extract.return_value = [
            {
                "name": "plot_scatter",
                "interface": "def plot_scatter(df, x, y)",
                "description": "Scatter plot visualization",
                "dict_args": {
                    "df": {"type": "Any", "description": "No description"},
                    "x": {"type": "Any", "description": "No description"},
                    "y": {"type": "Any", "description": "No description"},
                },
            }
        ]

        context = build_visualization_context(self.valid_execution_result)

        # Test compatible plots
        self.assertEqual(len(context["compatible_plots"]), 1)
        self.assertEqual(context["compatible_plots"][0]["name"], "plot_scatter")
        self.assertIn("interface", context["compatible_plots"][0])

        # Test data context
        self.assertEqual(context["data_context"]["row_count"], 3)
        self.assertEqual(
            context["data_context"]["columns"], {"age": "int64", "score": "int64"}
        )
        self.assertEqual(context["error"], None)

    @patch("app.backend.visualization.plot_context_selector.filter_plots_for_dataset")
    def test_no_compatible_plots(self, filter_plots_for_dataset):
        """Test when no plots are compatible"""

        filter_plots_for_dataset.return_value = []

        context = build_visualization_context(self.only_categorical_result)

        self.assertEqual(context["compatible_plots"], [])
        self.assertEqual(context["data_context"]["row_count"], 3)
        self.assertEqual(context["error"], None)

    def test_invalid_execution_result(self):
        """Test with missing required keys"""
        invalid_result = {"error": "Invalid query"}
        context = build_visualization_context(invalid_result)

        self.assertIsNotNone(context["error"])
        self.assertIn("Invalid execution result format", context["error"])
        self.assertEqual(context["data_context"], {})

    def test_empty_data(self):
        """Test with empty dataset"""
        empty_result = {"columns": [], "data": []}
        context = build_visualization_context(empty_result)

        self.assertEqual(context["compatible_plots"], [])
        self.assertEqual(context["data_context"]["row_count"], 0)
        self.assertEqual(context["data_context"]["columns"], {})
        self.assertEqual(context["error"], None)

    @patch(
        "app.backend.visualization.plot_context_selector.retrieve_plot_function_details"
    )
    def test_extract_plots_failure(self, mock_extract):
        """Test error handling when retrieve_plot_function_details fails"""
        mock_extract.side_effect = Exception("File not found")

        context = build_visualization_context(self.valid_execution_result)

        self.assertIsNotNone(context["error"])
        self.assertIn("File not found", context["error"])
        self.assertEqual(context["compatible_plots"], [])

    def test_data_context_structure(self):
        """Verify complete data context structure"""
        context = build_visualization_context(self.categorical_numeric_result)

        # Test column types
        self.assertEqual(
            context["data_context"]["columns"], {"category": "object", "count": "int64"}
        )

        # Test sample values
        samples = context["data_context"]["sample_3_values"]
        self.assertEqual(
            samples["category"],
            [sample[0] for sample in self.categorical_numeric_result["data"]],
        )
        self.assertEqual(
            samples["count"],
            [sample[1] for sample in self.categorical_numeric_result["data"]],
        )

        # Test row count
        self.assertEqual(context["data_context"]["row_count"], 2)

    @patch("app.backend.visualization.plot_context_selector.pd.DataFrame")
    def test_dataframe_creation_failure(self, mock_df):
        """Test error handling in DataFrame creation"""
        mock_df.side_effect = Exception("Invalid data shape")

        context = build_visualization_context(self.valid_execution_result)

        self.assertIsNotNone(context["error"])
        self.assertIn("Invalid data shape", context["error"])
        self.assertEqual(context["compatible_plots"], [])


class TestPlotFilterContext(unittest.TestCase):
    """
    Test suite for validating the generation of plot selection instructions from a visualization context.

    This class tests the transformation of plot metadata and dataset information into
    structured user instructions, including:
    - Formatting of available plot types with their descriptions and parameters
    - Presentation of dataset overview (row count, column types, sample values)
    - Error handling and messaging for incomplete or invalid context data
    - Proper rendering of optional parameters and default values
    - Edge cases such as empty datasets or missing metadata
    """

    def test_basic_context_generation(self):
        """Test context generation with valid input containing multiple plots and complete data."""

        plot_context = {
            "compatible_plots": [
                {
                    "name": "plot_bar",
                    "interface": "def plot_bar(data: pd.DataFrame, category_column: str, value_column: str):",
                    "description": "Create a vertical bar chart from a DataFrame.\n    Best for comparing values across categories\n\n    Args:\n        data: DataFrame containing the data.\n        category_column: Column name for the x-axis (categories).\n        value_column: Column name for the bar heights (values).",
                    "dict_args": {
                        "data": {
                            "type": "pd.DataFrame",
                            "description": "DataFrame containing the data.",
                        },
                        "category_column": {
                            "type": "str",
                            "description": "Column name for the x-axis (categories).",
                        },
                        "value_column": {
                            "type": "str",
                            "description": "Column name for the bar heights (values).",
                        },
                    },
                },
                {
                    "name": "plot_pie",
                    "interface": "def plot_pie(data: pd.DataFrame, category_column: str, value_column: str):",
                    "description": "Create a pie chart.\n    Best for proportional composition.\n\n    Args:\n        data: DataFrame containing the data.",
                    "dict_args": {
                        "data": {
                            "type": "pd.DataFrame",
                            "description": "DataFrame containing categories and values.",
                        },
                        "category_column": {
                            "type": "str",
                            "description": "Column with category labels.",
                        },
                        "value_column": {
                            "type": "str",
                            "description": "Column with numeric values.",
                        },
                    },
                },
            ],
            "data_context": {
                "row_count": 2,
                "columns": {"category": "object", "count": "int64"},
                "sample_3_values": {"category": ["A", "B"], "count": [10, 20]},
            },
            "error": None,
        }

        context = format_plot_selection_instructions(plot_context)

        # Verify sections exist
        self.assertIn("## Available Plot Types", context)
        self.assertIn("## Data Overview", context)
        self.assertIn("## Instructions", context)

        # Verify plot details
        self.assertIn("### plot_bar", context)
        self.assertIn(
            "def plot_bar(data: pd.DataFrame, category_column: str, value_column: str):",
            context,
        )
        self.assertIn(
            "- `data` (pd.DataFrame): DataFrame containing the data.", context
        )
        self.assertIn(
            "- `category_column` (str): Column name for the x-axis (categories).",
            context,
        )

        # Verify data details
        self.assertIn("- **Number of Rows**: 2", context)
        self.assertIn("`category` (object): Sample values: ['A', 'B']", context)
        self.assertIn("`count` (int64): Sample values: [10, 20]", context)

        # Verify instructions
        self.assertIn("Example Response", context)
        self.assertIn('"plot_type": "plot_bar"', context)

    def test_empty_compatible_plots(self):
        """Test handling when no compatible plots are available."""

        plot_context = {
            "compatible_plots": [],
            "data_context": {"row_count": 0, "columns": {}, "sample_3_values": {}},
            "error": None,
        }

        context = format_plot_selection_instructions(plot_context)

        self.assertIn("No compatible plots found for the given data.", context)
        self.assertNotIn("### plot_bar", context)  # Ensure no plots are listed
        self.assertNotIn("- **Number of Rows**:", context)

    def test_missing_data_context_keys(self):
        """Test robustness when data context has missing keys."""

        plot_context = {
            "compatible_plots": [
                {
                    "name": "plot_test",
                    "interface": "def plot_test(data: pd.DataFrame):",
                    "description": "Test plot.",
                    "dict_args": {
                        "data": {"type": "pd.DataFrame", "description": "DataFrame."}
                    },
                }
            ],
            "data_context": {  # Missing row_count and sample_3_values
                "columns": {"test_col": "float64"}
            },
            "error": None,
        }

        context = format_plot_selection_instructions(plot_context)

        # Verify default row count
        self.assertIn("- **Number of Rows**: 0", context)
        # Verify column without samples
        self.assertIn("`test_col` (float64): Sample values: []", context)

    def test_plot_with_no_arguments(self):
        """Test handling of a plot with no required arguments (hypothetical edge case)."""
        plot_context = {
            "compatible_plots": [
                {
                    "name": "plot_empty",
                    "interface": "def plot_empty():",
                    "description": "No arguments needed.",
                    "dict_args": {},  # No arguments
                }
            ],
            "data_context": {"row_count": 0, "columns": {}, "sample_3_values": {}},
            "error": None,
        }

        context = format_plot_selection_instructions(plot_context)

        self.assertIn("**Required Arguments**:\n", context)
        self.assertNotIn("- `data`", context)  # No arguments listed

    def test_missing_data_context_keys(self):
        """Test that missing required data context keys raise errors."""

        plot_context = {
            "compatible_plots": [
                {
                    "name": "plot_test",
                    "interface": "def plot_test(data: pd.DataFrame):",
                    "description": "Test plot.",
                    "dict_args": {
                        "data": {"type": "pd.DataFrame", "description": "DataFrame."}
                    },
                }
            ],
            "data_context": {  # Missing required keys: columns and sample_3_values
                "row_count": 5
            },
            "error": None,
        }

        with self.assertRaises(ValueError) as cm:
            format_plot_selection_instructions(plot_context)

        self.assertIn("data_context must contain 'columns'", str(cm.exception))

    def test_missing_sample_values(self):
        """Test handling of columns missing from sample_3_values shows None."""

        plot_context = {
            "compatible_plots": [
                {
                    "name": "plot_test",
                    "interface": "def plot_test(data: pd.DataFrame):",
                    "description": "Test plot.",
                    "dict_args": {
                        "data": {"type": "pd.DataFrame", "description": "DataFrame."}
                    },
                }
            ],
            "data_context": {
                "row_count": 3,
                "columns": {"missing_col": "int64", "present_col": "object"},
                "sample_3_values": {
                    "present_col": ["X", "Y", "Z"]
                },  # missing_col omitted
            },
            "error": None,
        }

        context = format_plot_selection_instructions(plot_context)

        # Verify missing column shows None
        self.assertIn("`missing_col` (int64): Sample values: None", context)
        # Verify present column shows actual values
        self.assertIn("`present_col` (object): Sample values: ['X', 'Y', 'Z']", context)

    def test_invalid_data_context_type(self):
        """Test that non-dict data_context raises error."""

        plot_context = {
            "compatible_plots": [],
            "data_context": "invalid",  # Should be dict
            "error": None,
        }

        with self.assertRaises(ValueError) as cm:
            format_plot_selection_instructions(plot_context)

        self.assertIn("data_context must be a dictionary", str(cm.exception))

    def test_default_parameters_set_to_none(self):
        """Test handling of parameters with default values set to None in the function definition."""

        plot_context = {
            "compatible_plots": [
                {
                    "name": "plot_scatter",
                    "interface": "def plot_scatter(data: pd.DataFrame, x_col: str, y_col: str, color: str = None):",
                    "description": "Create a scatter plot.\n    Useful for showing relationships between two variables.\n\n    Args:\n        data: DataFrame containing the data points.\n        x_col: Column name for the x-axis.\n        y_col: Column name for the y-axis.\n        color: Optional column name for point colors.",
                    "dict_args": {
                        "data": {
                            "type": "pd.DataFrame",
                            "description": "DataFrame containing the data points.",
                        },
                        "x_col": {
                            "type": "str",
                            "description": "Column name for the x-axis.",
                        },
                        "y_col": {
                            "type": "str",
                            "description": "Column name for the y-axis.",
                        },
                        "color": {
                            "type": "str",
                            "description": "Optional column name for point colors.",
                        },
                    },
                }
            ],
            "data_context": {
                "row_count": 100,
                "columns": {"x": "float64", "y": "float64", "group": "category"},
                "sample_3_values": {
                    "x": [1.5, 2.3, 3.7],
                    "y": [2.5, 3.1, 4.4],
                    "group": ["A", "B", "A"],
                },
            },
            "error": None,
        }

        context = format_plot_selection_instructions(plot_context)

        self.assertIn("color: str = None", context)

        # Verify all parameters are present in the description
        self.assertIn(
            "- `data` (pd.DataFrame): DataFrame containing the data points.", context
        )
        self.assertIn("- `x_col` (str): Column name for the x-axis.", context)
        self.assertIn("- `y_col` (str): Column name for the y-axis.", context)
        self.assertIn(
            "- `color` (str): Optional column name for point colors.", context
        )

        # Verify parameters with defaults are not marked as required
        self.assertIn("color: str = None", context)
