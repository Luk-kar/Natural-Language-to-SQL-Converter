"""
Unit tests for the visualization module:

- It tests the functions in the plot_details_extractor.py module
  that extract plot functions from a Python file.

- It also tests the plot functions in the plots.py
  module that generate Bokeh plots from a DataFrame.
"""

# Python
import unittest
from unittest.mock import patch
import os
import tempfile

# Third-party
import pandas as pd
import numpy as np

# Bokeh
from bokeh.plotting import figure
from bokeh.models import (
    Plot,
    Scatter,
    Wedge,
    Whisker,
    AnnularWedge,
    ColorBar,
    Quad,
)
from bokeh.models.glyphs import Patch

# Visualization
from app.backend.visualization.plot_details_extractor import (
    retrieve_plot_function_details,
)
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
from app.backend.visualization.plot_filter import filter_compatible_plots
from app.backend.visualization.generator import validate_plot_function_names
from app.backend.visualization.plot_context_selector import (
    filter_plots_for_dataset,
    build_visualization_context,
    format_plot_selection_instructions,
)


class TestPlotFunctionsExtractor(unittest.TestCase):
    """
    Test the plot functions extraction from a Python file.
    """

    def setUp(self):
        """
        Set up a temporary file for testing the plot functions extraction.
        """

        self.temp_file = tempfile.NamedTemporaryFile(
            mode="w+", delete=False, suffix=".py"
        )
        self.temp_file_name = self.temp_file.name

        self.patcher = patch(
            "app.backend.visualization.plot_details_extractor.PLOTS_PATH",
            self.temp_file_name,
        )
        self.patcher.start()

    def tearDown(self):
        # Stop patching and clean up
        self.patcher.stop()
        self.temp_file.close()
        os.unlink(self.temp_file_name)

    def write_to_temp_file(self, content):
        """Helper to write content to the temporary file."""

        with open(self.temp_file_name, "w", encoding="utf-8") as f:
            f.write(content.strip())

    def test_function_with_required_params_only(self):
        """Test a function with only required parameters."""
        content = """
def func1(a: int, b: str):
    \"\"\"Args:
        a: Integer parameter.
        b: String parameter.
    \"\"\"
    pass
"""
        self.write_to_temp_file(content)
        result = retrieve_plot_function_details()

        self.assertEqual(len(result), 1)
        func = result[0]
        self.assertEqual(func["name"], "func1")
        self.assertEqual(func["interface"], "def func1(a: int, b: str):")
        self.assertIn("a: Integer parameter.", func["description"])
        self.assertIn("b: String parameter.", func["description"])
        self.assertIn("a", func["dict_args"])
        self.assertEqual(
            func["dict_args"]["a"], {"type": "int", "description": "Integer parameter."}
        )
        self.assertIn("b", func["dict_args"])
        self.assertEqual(
            func["dict_args"]["b"],
            {"type": "str", "description": "String parameter."},
        )

    def test_function_with_default_params(self):
        """Test a function with parameters having default values."""
        content = """
def func2(a: int, b: str = "default"):
    \"\"\"Args:
        a: Integer parameter.
        b: String parameter. Defaults to "default".
    \"\"\"
    pass
"""
        self.write_to_temp_file(content)
        result = retrieve_plot_function_details()

        self.assertEqual(len(result), 1)
        func = result[0]
        self.assertEqual(func["interface"], "def func2(a: int):")
        self.assertIn("a: Integer parameter.", func["description"])
        self.assertNotIn("b: String parameter.", func["description"])

        self.assertIn("a", func["dict_args"])
        self.assertEqual(
            func["dict_args"]["a"], {"type": "int", "description": "Integer parameter."}
        )
        self
        self.assertNotIn("b", func["dict_args"])

    def test_function_with_no_params(self):
        """Test a function with no parameters."""
        content = """
def func3():
    \"\"\"No parameters here.\"\"\"
    pass
"""
        self.write_to_temp_file(content)
        result = retrieve_plot_function_details()

        self.assertEqual(len(result), 1)
        func = result[0]
        self.assertEqual(func["interface"], "def func3():")
        self.assertNotIn("Args:", func["description"])
        self.assertEqual(func["dict_args"], {})

    def test_docstring_with_args_and_returns(self):
        """Test docstring containing Args and Returns sections."""
        content = """
def func4(a: int):
    \"\"\"Args:
        a: Integer parameter.
    Returns:
        int: Result.
    \"\"\"
    return a
"""
        self.write_to_temp_file(content)
        result = retrieve_plot_function_details()

        func = result[0]
        self.assertIn("Args:", func["description"])
        self.assertIn("a: Integer parameter.", func["description"])
        self.assertFalse(
            any(
                keyword in func["description"].lower()
                for keyword in ["returns:", "return:"]
            )
        )
        self.assertNotIn("int: Result.", func["description"])

    def test_parameter_without_type_hint(self):
        """Test a parameter without a type hint."""
        content = """
def func5(a):
    \"\"\"Args:
        a: Some parameter.
    \"\"\"
    pass
"""
        self.write_to_temp_file(content)
        result = retrieve_plot_function_details()

        func = result[0]
        self.assertEqual(func["interface"], "def func5(a):")
        self.assertIn("a: Some parameter.", func["description"])
        self.assertIn("a", func["dict_args"])
        self.assertEqual(
            func["dict_args"]["a"], {"description": "Some parameter.", "type": "Any"}
        )

    def test_function_with_no_docstring(self):
        """Test a function with no docstring."""
        content = """
def func6(a: int):
    pass
"""
        self.write_to_temp_file(content)
        result = retrieve_plot_function_details()

        func = result[0]
        self.assertEqual(func["description"], "")
        self.assertIn("a", func["dict_args"])
        self.assertEqual(
            func["dict_args"]["a"], {"type": "int", "description": "No description"}
        )

    def test_multiple_functions(self):
        """Test parsing multiple functions."""
        content = """
def func7(a: int):
    \"\"\"Args: a: Integer.\"\"\"
    pass

def func8(b: str):
    \"\"\"Args: b: String.\"\"\"
    pass
"""
        self.write_to_temp_file(content)
        result = retrieve_plot_function_details()

        self.assertEqual(len(result), 2)
        func7 = next(f for f in result if f["name"] == "func7")
        self.assertEqual(func7["interface"], "def func7(a: int):")
        func8 = next(f for f in result if f["name"] == "func8")
        self.assertEqual(func8["interface"], "def func8(b: str):")


class TestPlotFunctionsExtractorOriginalFile(unittest.TestCase):
    """
    Test the plot functions extraction from the original plots.py file.
    """

    @classmethod
    def setUpClass(cls):
        cls.result = retrieve_plot_function_details()

    def test_number_of_functions(self):

        result = self.result
        self.assertEqual(len(result), 10)

    def test_plot_bar(self):

        result = self.result

        plot_bar_func = next(f for f in result if f["name"] == "plot_bar")
        self.assertEqual(
            plot_bar_func["interface"],
            "def plot_bar(data: pd.DataFrame, category_column: str, value_column: str):",
        )
        self.assertTrue(
            "Create a vertical bar chart from a DataFrame."
            in plot_bar_func["description"]
        )

        self.assertTrue("data" in plot_bar_func["dict_args"])
        self.assertTrue("category_column" in plot_bar_func["dict_args"])
        self.assertTrue("value_column" in plot_bar_func["dict_args"])

    def test_plot_heatmap(self):

        result = self.result
        plot_heatmap_func = next(f for f in result if f["name"] == "plot_heatmap")

        self.assertEqual(
            plot_heatmap_func["interface"],
            "def plot_heatmap(data: pd.DataFrame, x_column: str, y_column: str, value_column: str):",
        )

        self.assertTrue(
            "Create a rectangular heatmap plot." in plot_heatmap_func["description"]
        )
        self.assertTrue("data" in plot_heatmap_func["dict_args"])
        self.assertTrue("x_column" in plot_heatmap_func["dict_args"])
        self.assertTrue("y_column" in plot_heatmap_func["dict_args"])

    def test_plot_treemap(self):

        result = self.result
        plot_treemap_func = next(f for f in result if f["name"] == "plot_treemap")

        self.assertEqual(
            plot_treemap_func["interface"],
            "def plot_treemap(data: pd.DataFrame, group_columns: List[str], value_column: str):",
        )

        self.assertTrue(
            "Create a hierarchical treemap." in plot_treemap_func["description"]
        )
        self.assertTrue("group_columns" in plot_treemap_func["dict_args"])
        self.assertTrue("value_column" in plot_treemap_func["dict_args"])

    def test_plot_scatter(self):

        result = self.result
        plot_scatter_func = next(f for f in result if f["name"] == "plot_scatter")

        self.assertEqual(
            plot_scatter_func["interface"],
            "def plot_scatter(data: pd.DataFrame, x_column: str, y_column: str):",
        )

        self.assertTrue("Create a scatter plot." in plot_scatter_func["description"])
        self.assertTrue("data" in plot_scatter_func["dict_args"])
        self.assertTrue("x_column" in plot_scatter_func["dict_args"])
        self.assertTrue("y_column" in plot_scatter_func["dict_args"])

    def test_plot_stacked_area(self):

        result = self.result
        plot_stacked_area_func = next(
            f for f in result if f["name"] == "plot_stacked_area"
        )

        self.assertEqual(
            plot_stacked_area_func["interface"],
            "def plot_stacked_area(data: pd.DataFrame):",
        )

        self.assertTrue(
            "Create a stacked area chart." in plot_stacked_area_func["description"]
        )
        self.assertTrue("data" in plot_stacked_area_func["dict_args"])

    def test_plot_ridge(self):

        result = self.result
        plot_ridge_func = next(f for f in result if f["name"] == "plot_ridge")

        self.assertEqual(
            plot_ridge_func["interface"],
            "def plot_ridge(data: pd.DataFrame):",
        )

        self.assertTrue(
            "Create a ridge plot (joyplot) for numeric samples across categories."
            in plot_ridge_func["description"]
        )
        self.assertTrue("data" in plot_ridge_func["dict_args"])

    def test_plot_histogram(self):

        result = self.result
        plot_histogram_func = next(f for f in result if f["name"] == "plot_histogram")

        self.assertEqual(
            plot_histogram_func["interface"],
            "def plot_histogram(data: pd.DataFrame):",
        )

        self.assertTrue(
            "Create a histogram for a numeric column."
            in plot_histogram_func["description"]
        )

        self.assertTrue("data" in plot_histogram_func["dict_args"])

    def test_plot_pie(self):

        result = self.result
        plot_pie_func = next(f for f in result if f["name"] == "plot_pie")

        self.assertEqual(
            plot_pie_func["interface"],
            "def plot_pie(data: pd.DataFrame, category_column: str, value_column: str):",
        )

        self.assertTrue(
            "Create a pie chart from DataFrame columns." in plot_pie_func["description"]
        )

        self.assertTrue("category_column" in plot_pie_func["dict_args"])
        self.assertTrue("value_column" in plot_pie_func["dict_args"])

    def test_plot_donut(self):

        result = self.result
        plot_donut_func = next(f for f in result if f["name"] == "plot_donut")

        self.assertEqual(
            plot_donut_func["interface"],
            "def plot_donut(data: pd.DataFrame, category_column: str, value_column: str):",
        )

        self.assertTrue(
            "Create a donut chart from DataFrame columns."
            in plot_donut_func["description"]
        )

        self.assertTrue("category_column" in plot_donut_func["dict_args"])
        self.assertTrue("value_column" in plot_donut_func["dict_args"])

    def test_plot_box(self):

        result = self.result
        plot_box_func = next(f for f in result if f["name"] == "plot_box")

        self.assertEqual(
            plot_box_func["interface"],
            "def plot_box(data: pd.DataFrame, x_column: str, y_column: str):",
        )

        self.assertTrue(
            "Create a box plot with whiskers from DataFrame columns."
            in plot_box_func["description"]
        )

        self.assertTrue("x_column" in plot_box_func["dict_args"])
        self.assertTrue("y_column" in plot_box_func["dict_args"])


class TestPlotFunctions(unittest.TestCase):
    """
    Test the plot functions that generate Bokeh plots from a DataFrame.
    """

    def setUp(self):
        # Common test data setup
        self.sample_data = pd.DataFrame(
            {
                "category": ["A", "B", "C", "D"],
                "value": [10, 20, 30, 40],
                "group": ["X", "X", "Y", "Y"],
                "x_val": np.random.rand(4),
                "y_val": np.random.rand(4),
            }
        )
        self.time_data = pd.DataFrame(
            {
                "index": range(5),
                "series1": [1, 2, 3, 4, 5],
                "series2": [2, 3, 4, 5, 6],
                "series3": [5, 4, 3, 2, 1],
            }
        ).reset_index(drop=True)
        self.ridge_data = pd.DataFrame(
            {
                "A": np.random.normal(0, 1, 100),
                "B": np.random.normal(1, 1, 100),
                "C": np.random.normal(2, 1, 100),
            }
        )

    def test_plot_bar(self):
        plot = plot_bar(
            self.sample_data, category_column="category", value_column="value"
        )
        self.assertIsInstance(plot, figure)
        self.assertEqual(len(plot.renderers), 1)  # Check for vbar renderer

    def test_plot_heatmap(self):
        heatmap_data = pd.DataFrame(
            {
                "x": ["2020", "2021", "2022"],
                "y": ["Jan", "Feb", "Mar"],
                "val": np.random.randint(0, 100, 3),
            }
        ).reset_index()

        plot = plot_heatmap(
            heatmap_data, x_column="x", y_column="y", value_column="val"
        )
        self.assertIsInstance(plot, figure)
        self.assertTrue(any(isinstance(item, ColorBar) for item in plot.right))

    def test_plot_treemap(self):
        with self.assertRaises(ValueError):
            plot_treemap(self.sample_data, ["group"], "value")

        plot = plot_treemap(
            self.sample_data, group_columns=["group", "category"], value_column="value"
        )
        self.assertIsInstance(plot, figure)

    def test_plot_scatter(self):
        plot = plot_scatter(self.sample_data, x_column="x_val", y_column="y_val")
        self.assertIsInstance(plot, Plot)
        self.assertTrue(plot.select(Scatter))

    def test_plot_stacked_area(self):
        time_data = pd.DataFrame(
            {
                "date": pd.date_range("2020-01-01", periods=5),
                "series1": [1, 2, 3, 4, 5],
                "series2": [2, 3, 4, 5, 6],
            }
        )
        plot = plot_stacked_area(time_data)
        self.assertIsInstance(plot, figure)
        self.assertTrue(plot.legend)

    def test_plot_ridge(self):
        data = pd.DataFrame(
            {"A": np.random.normal(0, 1, 100), "B": np.random.normal(1, 1, 100)}
        )
        plot = plot_ridge(data)
        self.assertIsInstance(plot, figure)
        # Check for patch renderers (ridge lines)
        patches = [r for r in plot.renderers if isinstance(r.glyph, Patch)]
        self.assertTrue(len(patches) > 0)

    def test_plot_histogram(self):
        plot = plot_histogram(self.sample_data)
        self.assertIsInstance(plot, figure)
        self.assertTrue(plot.select({"type": Quad}))

    def test_plot_pie(self):
        plot = plot_pie(
            self.sample_data, category_column="category", value_column="value"
        )
        self.assertIsInstance(plot, figure)
        self.assertTrue(plot.select({"type": Wedge}))

    def test_plot_donut(self):
        plot = plot_donut(
            self.sample_data, category_column="category", value_column="value"
        )
        self.assertIsInstance(plot, figure)
        self.assertTrue(plot.select(AnnularWedge))

    def test_plot_box(self):
        plot = plot_box(self.sample_data, x_column="group", y_column="value")
        self.assertIsInstance(plot, figure)
        self.assertTrue(plot.select(Whisker))

    def test_error_handling(self):
        with self.assertRaises(ValueError):
            plot_bar(pd.DataFrame(), "missing", "columns")

        with self.assertRaises(ValueError):
            plot_pie(self.sample_data, "invalid", "columns")

    # === New tests for added parameters ===

    def test_plot_histogram_with_value_column(self):

        plot = plot_histogram(
            self.sample_data, value_column="value", title="Other Value Histogram"
        )
        self.assertIsInstance(plot, figure)

        self.assertEqual(plot.xaxis[0].axis_label, "value")

    def test_plot_stacked_area_with_to_include_only(self):

        to_include = ["series1", "series3"]
        plot = plot_stacked_area(
            self.time_data, to_include_only=to_include, title="Subset Stacked Area"
        )
        self.assertIsInstance(plot, figure)

        if plot.legend:

            legend_labels = [item.label["value"] for item in plot.legend[0].items]

            for label in to_include:
                self.assertIn(label, legend_labels)
        else:
            self.fail("No legend found in stacked area plot.")

    def test_plot_ridge_with_to_include_only(self):

        to_include = ["A", "C"]
        plot = plot_ridge(
            self.ridge_data, to_include_only=to_include, title="Subset Ridge Chart"
        )
        self.assertIsInstance(plot, figure)

        patches = [r for r in plot.renderers if getattr(r, "name", None) == "patches"]
        self.assertEqual(len(patches), len(to_include))

        expected_y_range = to_include[::-1]
        self.assertEqual(plot.y_range.factors, expected_y_range)


class TestFilterCompatiblePlots(unittest.TestCase):
    """
    Test the plot compatibility filter based on DataFrame column structure.
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


class TestPlotContextSelector(unittest.TestCase):

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


class TestGeneratePlotContext(unittest.TestCase):
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


class TestCreatePlotSelectionContext(unittest.TestCase):
    """Unit tests for the `create_plot_selection_context` function."""

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


if __name__ == "__main__":
    unittest.main()
