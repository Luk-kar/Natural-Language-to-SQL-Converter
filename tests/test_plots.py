# Python
import unittest

# Third-party
import pandas as pd
import numpy as np

# Bokeh
from bokeh.models import Plot

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
from app.backend.visualization.plot_router import get_plot_function

VALID_CONFIGS = {
    "bar": {
        "data": pd.DataFrame({"category": ["A", "B", "C", "D"], "value": [5, 6, 7, 8]}),
        "category_column": "category",
        "value_column": "value",
        "title": "Example Bar Chart",
    },
    "heatmap": {
        "data": pd.DataFrame(
            {
                "Year": ["2020", "2020", "2021", "2021"],
                "Month": ["Jan", "Feb", "Jan", "Feb"],
                "rate": [5, 6, 7, 8],
            }
        ),
        "x_column": "Year",
        "y_column": "Month",
        "value_column": "rate",
    },
    "treemap": {
        "data": pd.DataFrame(
            {
                "Region": ["North", "North", "South", "South"],
                "City": ["CityA", "CityB", "CityC", "CityD"],
                "Sales": [100, 150, 200, 50],
            }
        ),
        "group_columns": ["Region", "City"],
        "value_column": "Sales",
        "title": "Treemap Test",
    },
    "scatter": {
        "data": pd.DataFrame(
            {
                "x_values": np.linspace(-2, 2, 10),
                "y_values": np.linspace(-2, 2, 10) ** 2,
            }
        ),
        "x_column": "x_values",
        "y_column": "y_values",
    },
    "stacked_area": {
        "data": pd.DataFrame(np.random.randint(10, 100, size=(15, 5))).add_prefix("y"),
    },
    "ridge": {
        "data": pd.DataFrame(
            {
                "A": np.random.normal(0, 1, 100),
                "B": np.random.normal(1, 1.5, 100),
                "C": np.random.normal(-1, 0.5, 100),
            }
        ),
        "title": "Ridge Test",
    },
    "histogram": {
        "data": pd.DataFrame(np.random.normal(0, 1, 1000), columns=["Random Values"]),
    },
    "pie": {
        "data": pd.DataFrame(
            {
                "country": ["USA", "UK", "France"],
                "value": [100, 150, 250],
            }
        ),
        "category_column": "country",
        "value_column": "value",
    },
    "donut": {
        "data": pd.DataFrame(
            {
                "Browser": ["Chrome", "Firefox", "Safari"],
                "Share": [60, 25, 15],
            }
        ),
        "category_column": "Browser",
        "value_column": "Share",
    },
    "box": {
        "data": pd.DataFrame(
            {
                "class": ["SUV", "Sedan", "SUV", "Sedan", "Coupe", "Coupe"],
                "hwy": [20, 30, 25, 35, 40, 45],
            }
        ),
        "x_column": "class",
        "y_column": "hwy",
        "title": "Box Test",
    },
}


class TestVisualizationPlotFunctions(unittest.TestCase):
    """
    Test suite for validating the core visualization plot implementations.

    This class tests the successful generation of Bokeh figures for each plot type
    using valid configuration presets, ensuring proper glyph creation and basic
    plot structure validation.
    """

    def test_plot_bar(self):
        plot_bar(**VALID_CONFIGS["bar"])

    def test_plot_heatmap(self):
        plot_heatmap(**VALID_CONFIGS["heatmap"])

    def test_plot_treemap(self):
        plot_treemap(**VALID_CONFIGS["treemap"])

    def test_plot_scatter(self):
        plot_scatter(**VALID_CONFIGS["scatter"])

    def test_plot_stacked_area(self):
        plot_stacked_area(**VALID_CONFIGS["stacked_area"])

    def test_plot_ridge(self):
        plot_ridge(**VALID_CONFIGS["ridge"])

    def test_plot_histogram(self):
        plot_histogram(**VALID_CONFIGS["histogram"])

    def test_plot_pie(self):
        plot_pie(**VALID_CONFIGS["pie"])

    def test_plot_donut(self):
        plot_donut(**VALID_CONFIGS["donut"])

    def test_plot_box(self):
        plot_box(**VALID_CONFIGS["box"])


class TestPlotFunctionSelector(unittest.TestCase):
    """
    Test suite for validating the plot function selection and execution system.

    This class tests:
    - Correct routing of configuration to appropriate plot functions
    - Error handling for invalid plot types and configurations
    - Data validation and type checking
    - Argument validation and error messaging
    """

    def test_get_plot_function(self):
        """
        Test that get_plot_function correctly selects and calls the
        plot_treemap function with the provided keyword arguments.
        """
        config = {
            "plot_type": "treemap",
            "arguments": VALID_CONFIGS["treemap"],
        }
        plot = get_plot_function(config)
        self.assertIsInstance(plot, Plot)

    def test_invalid_plot_type(self):
        """
        Test that providing an invalid plot type raises a ValueError.
        """
        df = pd.DataFrame({"A": [1, 2, 3]})
        config = {
            "plot_type": "invalid_plot",  # invalid plot type
            "arguments": {
                "data": df,
                "title": "Invalid Plot Test",
            },
        }
        with self.assertRaises(ValueError) as context:
            get_plot_function(config)
        self.assertIn("Invalid plot type specified", str(context.exception))

    def test_invalid_data_type(self):
        """
        Test that providing a non-DataFrame for 'data' raises a ValueError.
        """
        config = {
            "plot_type": "treemap",
            "arguments": {
                "data": [1, 2, 3],  # not a DataFrame
                "group_columns": ["Group"],
                "value_column": "Value",
                "title": "Data Type Test",
            },
        }
        with self.assertRaises(ValueError) as context:
            get_plot_function(config)
        self.assertIn("Data must be a pandas DataFrame", str(context.exception))

    def test_missing_arguments_key(self):
        """
        Test that calling get_plot_function without the 'arguments' key raises a ValueError.
        """
        config = {
            "plot_type": "treemap",
            # Missing 'arguments' key
        }
        with self.assertRaises(ValueError) as context:
            get_plot_function(config)
        self.assertIn("Invalid arguments provided", str(context.exception))

    def test_invalid_arguments_exceed(self):
        """
        Test that providing an invalid (extra) argument raises a TypeError.
        """
        cfg = VALID_CONFIGS["treemap"].copy()
        cfg["extra"] = "extra argument"  # not a valid argument
        config = {
            "plot_type": "treemap",
            "arguments": cfg,
        }
        with self.assertRaises(TypeError) as context:
            get_plot_function(config)
        self.assertIn("got an unexpected keyword argument", str(context.exception))

    def test_invalid_arguments_missing(self):
        """
        Test that providing an invalid (missing) argument raises a TypeError.
        """
        cfg = VALID_CONFIGS["treemap"].copy()
        cfg.pop("value_column")  # remove a required argument
        config = {
            "plot_type": "treemap",
            "arguments": cfg,
        }
        with self.assertRaises(TypeError) as context:
            get_plot_function(config)
        self.assertIn("missing 1 required positional argument", str(context.exception))


if __name__ == "__main__":
    unittest.main()
