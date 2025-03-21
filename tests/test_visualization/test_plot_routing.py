"""
Tests for routing plot configurations to the appropriate plot functions.

This module validates the system's ability to:
- Correctly route valid configurations to their corresponding plot functions.
- Handle errors for invalid plot types or configurations.
- Enforce argument validation and provide clear error messages.

Tests ensure that the routing logic is robust, user-friendly, and handles edge cases effectively.
"""

# Python
import json
import unittest
from unittest.mock import patch, MagicMock

# Visualization
from app.backend.visualization.plot_context_selector import (
    filter_plots_for_dataset,
)
from app.backend.visualization.generator import (
    generate_plot_from_config,
    create_chart_dictionary,
    generate_fallback_plot_config,
    NO_COMPATIBLE_PLOTS_MESSAGE,
    get_plot_function,
)

# Third-party
import pandas as pd

# Bokeh
from bokeh.embed import json_item
from bokeh.models import Plot

# Flask
from flask import Flask

# LLM
from app.backend.llm_engine import get_llm, LLM


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


class TestVisualizationGeneration(unittest.TestCase):
    """
    Test suite for generating visualizations based on LLM-generated configurations.

    This class tests:
    - Successful generation of Bokeh plots from valid configurations.
    - Fallback to simpler plots when LLM fails to generate a valid configuration.
    - Proper handling of missing or invalid data for plot generation.
    - Error handling for missing or incompatible plot configurations.
    """

    def setUp(self):

        # Create a Flask app instance
        self.app = Flask(__name__)
        self.app.config["TESTING"] = True

        # Mock LLM instance
        self.mock_llm = MagicMock()
        self.patcher = patch("app.backend.llm_engine.LLM", new=self.mock_llm)
        self.patcher.start()

        self.sample_execution = {
            "columns": ["category", "value"],
            "data": [["A", 10], ["B", 20], ["C", 30]],
        }

        self.valid_llm_context = {
            "compatible_plots": [
                {
                    "name": "plot_bar",
                    "interface": "def plot_bar(data, category_column, value_column)",
                    "description": "Bar chart",
                    "dict_args": {
                        "category_column": {
                            "type": "str",
                            "description": "Category column",
                        },
                        "value_column": {"type": "str", "description": "Value column"},
                    },
                }
            ],
            "data_context": {
                "columns": {"category": "object", "value": "int64"},
                "sample_3_values": {"category": ["A", "B", "C"], "value": [10, 20, 30]},
            },
        }

        self.chart_generation_context = "dummy_context"

        self.df = pd.DataFrame(
            self.sample_execution["data"], columns=self.sample_execution["columns"]
        )

    def tearDown(self):
        self.patcher.stop()
        # Reset the LLM instance
        global LLM
        LLM = None

    # Tests for generate_plot_from_config
    @patch("app.backend.visualization.generator.create_chart_dictionary")
    def test_generate_plot_success(self, mock_create):
        mock_create.return_value = {
            "plot_type": "bar",
            "arguments": {"category_column": "category", "value_column": "value"},
        }

        result = generate_plot_from_config(
            self.sample_execution,
            self.valid_llm_context,
            self.chart_generation_context,
            self.df,
        )

        # Verify Bokeh-compatible JSON output
        self.assertIsInstance(json.loads(result), dict)
        self.assertIn("target_id", json.loads(result))

    @patch("app.backend.visualization.generator.create_chart_dictionary")
    @patch("app.backend.visualization.generator.generate_fallback_plot_config")
    def test_generate_plot_fallback(self, mock_fallback, mock_create):
        mock_fallback.return_value = {
            "plot_type": "bar",
            "arguments": {"category_column": "category", "value_column": "value"},
        }
        mock_create.side_effect = Exception("LLM error")

        result = generate_plot_from_config(
            self.sample_execution,
            self.valid_llm_context,
            self.chart_generation_context,
            self.df,
        )

        self.assertIsInstance(json.loads(result), dict)

    @patch("app.backend.visualization.generator.create_chart_dictionary")
    @patch("app.backend.visualization.generator.generate_fallback_plot_config")
    def test_no_compatible_plots(self, mock_fallback, mock_create):
        mock_create.side_effect = Exception("LLM error")
        mock_fallback.side_effect = ValueError(NO_COMPATIBLE_PLOTS_MESSAGE)

        # Create application context
        with self.app.app_context():
            result = generate_plot_from_config(
                self.sample_execution,
                self.valid_llm_context,
                self.chart_generation_context,
                self.df,
            )

        response = json.loads(result.get_data(as_text=True))
        self.assertIn("compatible_plots_error", response)
        self.assertEqual(
            response["compatible_plots_error"], NO_COMPATIBLE_PLOTS_MESSAGE
        )

    # Tests for create_chart_dictionary
    @patch("app.backend.llm_engine.LLM.create_completion")
    def test_create_chart_valid_response(self, mock_llm):
        mock_llm.return_value = {
            "choices": [
                {
                    "text": """```json
                {
                    "plot_type": "bar",
                    "arguments": {
                        "category_column": "category",
                        "value_column": "value"
                    }
                }
                ```"""
                }
            ]
        }

        config = create_chart_dictionary("dummy_prompt")
        self.assertEqual(config["plot_type"], "bar")
        self.assertEqual(config["arguments"]["category_column"], "category")

    @patch("app.backend.llm_engine.LLM.create_completion")
    def test_create_chart_invalid_response(self, mock_llm):
        mock_llm.return_value = {"choices": [{"text": "invalid JSON"}]}

        with self.assertRaises(ValueError):
            create_chart_dictionary("dummy_prompt")

    # Tests for generate_fallback_plot_config
    def test_fallback_success(self):
        config = generate_fallback_plot_config(
            self.sample_execution, self.valid_llm_context
        )

        self.assertEqual(config["plot_type"], "bar")
        self.assertEqual(config["arguments"]["category_column"], "category")
        self.assertEqual(config["arguments"]["value_column"], "value")

    def test_fallback_no_compatible_plots(self):
        invalid_context = {
            "compatible_plots": [],
            "data_context": self.valid_llm_context["data_context"],
        }

        with self.assertRaises(ValueError) as cm:
            generate_fallback_plot_config(self.sample_execution, invalid_context)

        self.assertEqual(str(cm.exception), NO_COMPATIBLE_PLOTS_MESSAGE)

    def test_fallback_column_selection(self):
        modified_context = self.valid_llm_context.copy()
        modified_context["compatible_plots"].append(
            {
                "name": "plot_scatter",
                "interface": "def plot_scatter(data, x_column, y_column)",
                "description": "Scatter plot",
            }
        )

        config = generate_fallback_plot_config(self.sample_execution, modified_context)

        # Should prefer bar (fewer params) over scatter
        self.assertEqual(config["plot_type"], "bar")

    # Browser rendering check
    def test_bokeh_rendering(self):
        config = {
            "plot_type": "bar",
            "arguments": {
                "data": self.df,
                "category_column": "category",
                "value_column": "value",
            },
        }

        try:
            plot = get_plot_function(config)
            plot_json = json.dumps(json_item(plot, "chart"))

            # Verify JSON structure
            json_data = json.loads(plot_json)
            self.assertIn("target_id", json_data)
            self.assertIn("doc", json_data)
            self.assertIn("version", json_data)

            # Verify the plot can be rendered
            self.assertIsInstance(plot, Plot)

        except Exception as e:
            self.fail(f"Bokeh rendering failed: {str(e)}")
