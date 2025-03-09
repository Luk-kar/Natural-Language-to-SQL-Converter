import unittest
import pandas as pd
import numpy as np

from backend.bokeh_charts_examples import (
    bar_chart,
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


class TestPlots(unittest.TestCase):

    def test_bar_chart(self):
        df = pd.DataFrame({"category": ["A", "B", "C", "D"], "value": [5, 6, 7, 8]})
        bar_chart(
            df,
            category_column="category",
            value_column="value",
            title="Example Bar Chart",
        )

    def test_plot_heatmap(self):
        df = pd.DataFrame(
            {
                "Year": ["2020", "2020", "2021", "2021"],
                "Month": ["Jan", "Feb", "Jan", "Feb"],
                "rate": [5, 6, 7, 8],
            }
        )
        plot_heatmap(df, x_column="Year", y_column="Month", value_column="rate")

    def test_plot_treemap(self):
        df = pd.DataFrame(
            {
                "Region": ["North", "North", "South", "South"],
                "City": ["CityA", "CityB", "CityC", "CityD"],
                "Sales": [100, 150, 200, 50],
            }
        )
        plot_treemap(
            df,
            group_columns=["Region", "City"],
            value_column="Sales",
            title="Treemap Test",
        )

    def test_plot_scatter(self):
        N = 10
        x = np.linspace(-2, 2, N)
        y = x**2
        df = pd.DataFrame({"x_values": x, "y_values": y})
        plot_scatter(df, x_column="x_values", y_column="y_values")

    def test_plot_stacked_area(self):
        np.random.seed(0)
        df = pd.DataFrame(np.random.randint(10, 100, size=(15, 5))).add_prefix("y")
        plot_stacked_area(df)

    def test_plot_ridge(self):
        df = pd.DataFrame(
            {
                "A": np.random.normal(0, 1, 100),
                "B": np.random.normal(1, 1.5, 100),
                "C": np.random.normal(-1, 0.5, 100),
            }
        )
        plot_ridge(df, title="Ridge Test")

    def test_plot_histogram(self):
        df = pd.DataFrame(np.random.normal(0, 1, 1000), columns=["Random Values"])
        plot_histogram(df)

    def test_plot_pie(self):
        df = pd.DataFrame(
            {"country": ["USA", "UK", "France"], "value": [100, 150, 250]}
        )
        plot_pie(df, category_column="country", value_column="value")

    def test_plot_donut(self):
        df = pd.DataFrame(
            {"Browser": ["Chrome", "Firefox", "Safari"], "Share": [60, 25, 15]}
        )
        plot_donut(df, category_column="Browser", value_column="Share")

    def test_plot_box(self):
        df = pd.DataFrame(
            {
                "class": ["SUV", "Sedan", "SUV", "Sedan", "Coupe", "Coupe"],
                "hwy": [20, 30, 25, 35, 40, 45],
            }
        )
        plot_box(df, x_column="class", y_column="hwy", title="Box Test")


if __name__ == "__main__":
    unittest.main()
