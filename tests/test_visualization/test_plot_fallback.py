# Python
import unittest
import random
import string

from app.backend.visualization.plot_fallback import generate_fallback_plot_config


class TestFallbackPlotGeneration(unittest.TestCase):
    def setUp(self):
        self.valid_execution = {
            "columns": ["category", "value"],
            "data": [["A", 10], ["B", 20], ["C", 30]],
        }

        self.basic_context = {
            "compatible_plots": [
                {
                    "name": "plot_bar",
                    "interface": "def plot_bar(data, category_column, value_column)",
                    "description": "Bar chart",
                },
                {
                    "name": "plot_pie",
                    "interface": "def plot_pie(data, category_column, value_column)",
                    "description": "Pie chart",
                },
            ],
            "data_context": {
                "columns": {"category": "object", "value": "int64"},
                "sample_3_values": {"category": ["A", "B", "C"], "value": [10, 20, 30]},
            },
        }

    def test_basic_fallback(self):
        """Test fallback to simplest available plot"""

        config = generate_fallback_plot_config(self.valid_execution, self.basic_context)

        self.assertEqual(config["plot_type"], "bar")
        self.assertEqual(config["arguments"]["category_column"], "category")
        self.assertEqual(config["arguments"]["value_column"], "value")

    def test_priority_order(self):
        """Test plot priority when multiple options exist"""

        modified_context = self.basic_context.copy()
        modified_context["compatible_plots"].append(
            {
                "name": "plot_scatter",
                "interface": "def plot_scatter(data, x_column, y_column)",
                "description": "Scatter plot",
            }
        )

        config = generate_fallback_plot_config(self.valid_execution, modified_context)

        # Should prefer bar (1 param) over scatter (2 params)
        self.assertEqual(config["plot_type"], "bar")

    def test_missing_columns(self):
        """Test fallback with missing required column types"""

        context = {
            "compatible_plots": [
                {
                    "name": "plot_histogram",
                    "interface": "def plot_histogram(data, value_column)",
                    "description": "Histogram",
                }
            ],
            "data_context": {
                "columns": {"category": "object"},
                "sample_3_values": {"category": ["A", "B", "C"]},
            },
        }

        with self.assertRaises(ValueError) as cm:
            generate_fallback_plot_config(self.valid_execution, context)

        self.assertIn("No valid configuration", str(cm.exception))

    def test_column_type_detection(self):
        """Test proper detection of categorical/numerical columns"""

        execution = {
            "columns": ["id", "temperature"],
            "data": [[1, 22.5], [2, 23.1], [3, 24.8]],
        }

        context = {
            "compatible_plots": [
                {
                    "name": "plot_scatter",
                    "interface": "def plot_scatter(data, x_column, y_column)",
                    "description": "Scatter plot",
                }
            ],
            "data_context": {
                "columns": {"id": "int64", "temperature": "float64"},
                "sample_3_values": {"id": [1, 2, 3], "temperature": [22.5, 23.1, 24.8]},
            },
        }

        config = generate_fallback_plot_config(execution, context)
        self.assertEqual(config["plot_type"], "scatter")

        self.assertEqual(config["arguments"]["x_column"], "id")
        self.assertEqual(config["arguments"]["y_column"], "temperature")

    def test_invalid_execution_result(self):
        """Test handling of malformed execution result"""

        with self.assertRaises(ValueError):
            generate_fallback_plot_config({"invalid": "structure"}, self.basic_context)

    def test_required_param_matching(self):
        """Test parameter name to column type matching"""

        context = {
            "compatible_plots": [
                {
                    "name": "plot_box",
                    "interface": "def plot_box(data, x_column, y_column)",
                    "description": "Box plot",
                }
            ],
            "data_context": {
                "columns": {"group": "object", "measurement": "float64"},
                "sample_3_values": {
                    "group": ["A", "B", "C"],
                    "measurement": [1.1, 2.2, 3.3],
                },
            },
        }

        config = generate_fallback_plot_config(self.valid_execution, context)
        self.assertEqual(config["plot_type"], "box")
        self.assertEqual(config["arguments"]["x_column"], "group")
        self.assertEqual(config["arguments"]["y_column"], "measurement")

    def test_random_column_names(self):
        """Test fallback works with arbitrary column names based on data types"""

        # Generate 2 random column names
        random_cols = [
            "".join(random.choices(string.ascii_letters, k=8))
            for _ in range(len(self.valid_execution["columns"]))
        ]

        # Create modified execution result with random column names
        modified_execution = {
            "columns": random_cols,
            "data": self.valid_execution["data"],  # Original data structure
        }

        context = {
            "compatible_plots": [
                {
                    "name": "plot_bar",
                    "interface": "def plot_bar(data, category_column, value_column)",
                    "description": "Bar chart",
                }
            ],
            "data_context": {
                "columns": {random_cols[0]: "object", random_cols[1]: "int64"},
                "sample_3_values": {
                    random_cols[0]: ["A", "B", "C"],
                    random_cols[1]: [10, 20, 30],
                },
            },
        }

        config = generate_fallback_plot_config(modified_execution, context)

        self.assertEqual(config["plot_type"], "bar")
        self.assertEqual(config["arguments"]["category_column"], random_cols[0])
        self.assertEqual(config["arguments"]["value_column"], random_cols[1])


if __name__ == "__main__":
    unittest.main()
