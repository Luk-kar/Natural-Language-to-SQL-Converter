import unittest
import tempfile
import os
from unittest.mock import patch

import pandas as pd
import numpy as np
from bokeh.plotting import figure
from bokeh.models import (
    Plot,
    Scatter,
    VBar,
    Wedge,
    Whisker,
    AnnularWedge,
    ColorBar,
    Quad,
    Rect,
    AnnularWedge,
    Line,
    VArea,
)
from bokeh.models.glyphs import Patch

# Assume the code to test is in a module named 'plot_parser'
from app.backend.visualization.function_extractor import (
    extract_plot_functions,
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


class TestPlotFunctionsExtractor(unittest.TestCase):
    def setUp(self):
        # Create a temporary file
        self.temp_file = tempfile.NamedTemporaryFile(
            mode="w+", delete=False, suffix=".py"
        )
        self.temp_file_name = self.temp_file.name

        # Patch PLOTS_PATH to point to the temporary file
        self.patcher = patch(
            "app.backend.visualization.function_extractor.PLOTS_PATH",
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

        with open(self.temp_file_name, "w") as f:
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
        result = extract_plot_functions()

        self.assertEqual(len(result), 1)
        func = result[0]
        self.assertEqual(func["name"], "func1")
        self.assertEqual(func["interface"], "def func1(a: int, b: str):")
        self.assertIn("a: Integer parameter.", func["description"])
        self.assertIn("b: String parameter.", func["description"])
        self.assertIn('"a": None, # int: Integer parameter.', func["dict_args"])
        self.assertIn('"b": None, # str: String parameter.', func["dict_args"])

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
        result = extract_plot_functions()

        self.assertEqual(len(result), 1)
        func = result[0]
        self.assertEqual(func["interface"], "def func2(a: int):")
        self.assertIn("a: Integer parameter.", func["description"])
        self.assertNotIn("b: String parameter.", func["description"])
        self.assertIn('"a": None, # int: Integer parameter.', func["dict_args"])
        self.assertNotIn("b", func["dict_args"])

    def test_function_with_no_params(self):
        """Test a function with no parameters."""
        content = """
def func3():
    \"\"\"No parameters here.\"\"\"
    pass
"""
        self.write_to_temp_file(content)
        result = extract_plot_functions()

        self.assertEqual(len(result), 1)
        func = result[0]
        self.assertEqual(func["interface"], "def func3():")
        self.assertNotIn("Args:", func["description"])
        self.assertEqual(func["dict_args"].strip(), "{\n}")

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
        result = extract_plot_functions()

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
        result = extract_plot_functions()

        func = result[0]
        self.assertEqual(func["interface"], "def func5(a):")
        self.assertIn("a: Some parameter.", func["description"])
        self.assertIn('"a": None, # Any: Some parameter.', func["dict_args"])

    def test_function_with_no_docstring(self):
        """Test a function with no docstring."""
        content = """
def func6(a: int):
    pass
"""
        self.write_to_temp_file(content)
        result = extract_plot_functions()

        func = result[0]
        self.assertEqual(func["description"], "")
        self.assertIn('"a": None, # int: No description', func["dict_args"])

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
        result = extract_plot_functions()

        self.assertEqual(len(result), 2)
        func7 = next(f for f in result if f["name"] == "func7")
        self.assertEqual(func7["interface"], "def func7(a: int):")
        func8 = next(f for f in result if f["name"] == "func8")
        self.assertEqual(func8["interface"], "def func8(b: str):")


class TestPlotsSuccess(unittest.TestCase):

    def test_plot_bar(self):
        data = pd.DataFrame({"Category": ["A", "B", "C"], "Value": [10, 20, 30]})
        plot = plot_bar(data, "Category", "Value")
        self.assertIsInstance(plot, figure)
        vbars = [r for r in plot.renderers if isinstance(r.glyph, VBar)]
        self.assertTrue(len(vbars) > 0)
        self.assertEqual(plot.xaxis.axis_label, "Category")
        self.assertEqual(plot.yaxis.axis_label, "Value")
        self.assertEqual(plot.title.text, "Bar Chart")

    def test_plot_heatmap(self):
        data = pd.DataFrame(
            {
                "x": ["2020", "2021", "2022"],
                "y": ["Jan", "Feb", "Mar"],
                "value": [10, 20, 30],
            }
        )
        plot = plot_heatmap(data, "x", "y", "value")
        self.assertIsInstance(plot, figure)
        rects = [r for r in plot.renderers if isinstance(r.glyph, Rect)]
        self.assertTrue(len(rects) > 0)
        color_bars = [item for item in plot.right if isinstance(item, ColorBar)]
        self.assertTrue(len(color_bars) > 0)

    def test_plot_treemap(self):
        data = pd.DataFrame(
            {
                "Group1": ["A", "A", "B", "B"],
                "Group2": ["X", "Y", "X", "Y"],
                "Value": [10, 20, 30, 40],
            }
        )
        plot = plot_treemap(data, ["Group1", "Group2"], "Value")
        self.assertIsInstance(plot, figure)

    def test_plot_scatter(self):
        data = pd.DataFrame({"x": [1, 2, 3], "y": [4, 5, 6]})
        plot = plot_scatter(data, "x", "y")
        self.assertIsInstance(plot, Plot)
        scatters = [r for r in plot.renderers if isinstance(r.glyph, Scatter)]
        self.assertTrue(len(scatters) > 0)
        self.assertTrue(len(plot.axis) >= 2)  # Check axes are present

    def test_plot_stacked_area(self):
        data = pd.DataFrame({"index": [1, 2, 3], "A": [10, 20, 30], "B": [15, 25, 35]})
        plot = plot_stacked_area(data)
        self.assertIsInstance(plot, figure)
        vareas = [r for r in plot.renderers if isinstance(r.glyph, VArea)]
        self.assertTrue(len(vareas) > 0)

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
        data = pd.DataFrame({"Value": np.random.normal(0, 1, 100)})
        plot = plot_histogram(data)
        self.assertIsInstance(plot, figure)
        quads = [r for r in plot.renderers if isinstance(r.glyph, Quad)]
        lines = [r for r in plot.renderers if isinstance(r.glyph, Line)]
        self.assertTrue(len(quads) > 0 and len(lines) > 0)

    def test_plot_pie(self):
        data = pd.DataFrame({"Category": ["A", "B", "C"], "Value": [30, 50, 20]})
        plot = plot_pie(data, "Category", "Value")
        self.assertIsInstance(plot, figure)
        wedges = [r for r in plot.renderers if isinstance(r.glyph, Wedge)]
        self.assertTrue(len(wedges) > 0)
        self.assertIsNotNone(plot.legend[0])

    def test_plot_donut(self):
        data = pd.DataFrame({"Category": ["A", "B", "C"], "Value": [40, 30, 30]})
        plot = plot_donut(data, "Category", "Value")
        self.assertIsInstance(plot, figure)
        annulars = [r for r in plot.renderers if isinstance(r.glyph, AnnularWedge)]
        self.assertTrue(len(annulars) > 0)
        self.assertIsNotNone(plot.legend[0])

    def test_plot_box(self):
        data = pd.DataFrame(
            {"Category": ["A", "A", "B", "B"], "Value": [10, 15, 20, 25]}
        )
        plot = plot_box(data, "Category", "Value")
        self.assertIsInstance(plot, figure)
        vbars = [r for r in plot.renderers if isinstance(r.glyph, VBar)]
        self.assertTrue(len(vbars) > 0)
        self.assertTrue(plot.select(dict(type=Whisker)))


class TestPlotFunctions(unittest.TestCase):
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
        self.assertTrue(plot.select(dict(type=Quad)))

    def test_plot_pie(self):
        plot = plot_pie(
            self.sample_data, category_column="category", value_column="value"
        )
        self.assertIsInstance(plot, figure)
        self.assertTrue(plot.select(dict(type=Wedge)))

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


if __name__ == "__main__":
    unittest.main()

if __name__ == "__main__":
    unittest.main()
