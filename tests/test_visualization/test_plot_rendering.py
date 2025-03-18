"""
Tests for validating the rendering of Bokeh plots, including low-level glyph generation and high-level plot structure.

This module is divided into two test classes:
1. `TestPlotGlyphs`: Focuses on the correct creation of Bokeh glyphs (e.g., bars, wedges, patches) and their mapping to data properties.
2. `TestPlotRendering`: Validates the overall structure of generated plots, including axes, titles, toolbars, and interaction features.

Tests ensure that plots are visually accurate, interactive, and adhere to Bokeh's rendering standards.
"""

# Python
import unittest

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
from app.backend.visualization.plot_details_extractor import (
    retrieve_plot_function_details,
)


class TestPlotGlyphs(unittest.TestCase):
    """
    Test suite for validating Bokeh glyph generation in plot functions.

    This class tests:
    - Correct creation of specific glyph types (bars, wedges, patches, etc.)
    - Data-to-visual property mapping
    - Error handling for invalid column references
    - Advanced parameter handling and plot customization
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


class TestPlotRendering(unittest.TestCase):
    """
    Test suite for validating the production plot functions' interface contracts.

    This class tests the real plot implementations against expected:
    - Function signatures and parameter requirements
    - Documentation completeness
    - Argument type annotations
    - Consistency across all visualization functions
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
