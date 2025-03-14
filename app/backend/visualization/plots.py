"""
Top 10 Bokeh Charts for Data Visualization
"""

# Python
from math import pi
from typing import List

# Third-party
import numpy as np
from numpy import linspace
import pandas as pd
from scipy.stats import gaussian_kde
from squarify import normalize_sizes, squarify
import colorcet as cc

# Bokeh - Core and Models
from bokeh.models import (
    ColumnDataSource,
    Grid,
    LinearAxis,
    Plot,
    Scatter,
    Whisker,
    BasicTicker,
    BasicTickFormatter,
    PrintfTickFormatter,
    Range1d,
    AnnularWedge,
    Legend,
    LegendItem,
)

# Bokeh - Palettes and Plotting
from bokeh.palettes import tol, Category10, Category20, Category20c
from bokeh.plotting import figure
from bokeh.transform import linear_cmap, factor_cmap, cumsum


def plot_bar(
    data: pd.DataFrame,
    category_column: str,
    value_column: str,
    title: str = "Bar Chart",
    width: int = 500,
    height: int = 300,
) -> None:
    """
    Create a vertical bar chart from a DataFrame.
    Best for comparing values across categories

    Args:
        data: DataFrame containing the data.
        category_column: Column name for the x-axis (categories).
        value_column: Column name for the bar heights (values).
        title: Title of the plot. Defaults to "Bar Chart".
        width: Plot width in pixels. Defaults to 500.
        height: Plot height in pixels. Defaults to 300.
    """
    # Ensure the specified columns exist in the DataFrame
    if category_column not in data.columns or value_column not in data.columns:
        raise ValueError(
            f"The DataFrame must contain columns '{category_column}' and '{value_column}'."
        )

    # Extract x-values and bar heights
    x_values = data[category_column].tolist()
    top_values = data[value_column].tolist()

    # Auto-calculate width if not provided
    width = max(width, len(x_values) * 50)

    # Auto-calculate height if not provided
    height = max(height, int(max(top_values) * 1.2))

    # Calculate bar width
    if len(x_values) > 1:
        # For numeric categories, calculate the average gap between values
        if pd.api.types.is_numeric_dtype(data[category_column]):
            sorted_x = sorted(x_values)
            avg_gap = np.mean(np.diff(sorted_x))
            bar_width = avg_gap * 0.8
        else:
            # For non-numeric categories (e.g., strings), use a fixed bar width
            bar_width = 0.8
    else:
        # Fallback for a single bar
        bar_width = 0.5

    # Generate a dynamic color palette based on the number of bars
    bright = tol["Sunset"]
    num_categories = len(x_values)
    if num_categories in bright:
        colors = bright[num_categories]
    else:
        # If the exact number is not available, use the largest available and repeat/cut as needed.
        max_colors = max(bright.keys())
        palette = bright[max_colors]
        # Repeat the palette if necessary, then cut to the desired length.
        colors = (palette * ((num_categories // len(palette)) + 1))[:num_categories]

    # Create the figure
    x_range = (
        pd.Series(x_values).unique().tolist()
    )  # Convert to Series and get unique values
    plot = figure(
        width=width,
        height=height,
        x_range=x_range,
        toolbar_location=None,
        title=title,  # Add title to the plot
    )
    plot.vbar(x=x_values, width=bar_width, bottom=0, top=top_values, color=colors)

    # Styling
    plot.xaxis.axis_label = category_column
    plot.yaxis.axis_label = value_column
    plot.xgrid.grid_line_color = None
    plot.ygrid.grid_line_color = "#dddddd"

    return plot


def plot_heatmap(
    data: pd.DataFrame,
    x_column: str,
    y_column: str,
    value_column: str,
    title: str = "Heatmap Chart",
    width: int = 900,
    height: int = 400,
) -> None:
    """
    Create a rectangular heatmap plot.
    Best for matrix-like data with two dimensions.

    Args:
        data: DataFrame for the heatmap.
        x_column: Column name for the x-axis (e.g., "Year").
        y_column: Column name for the y-axis (e.g., "Month").
        value_column: Column name with values to visualize.
        title: Plot title. Defaults to "Heatmap Chart".
        width: Plot width in pixels. Defaults to 900.
        height: Plot height in pixels. Defaults to 400.
    """

    colors: List[str] = [
        "#75968f",
        "#a5bab7",
        "#c9d9d3",
        "#e2e2e2",
        "#dfccce",
        "#ddb7b1",
        "#cc7878",
        "#933b41",
        "#550b1d",
    ]
    x_range = sorted(data[x_column].unique().astype(str))
    y_range = sorted(data[y_column].unique(), reverse=True)

    tooltips = [
        (f"{y_column} {x_column}", f"@{y_column} @{x_column}"),
        (f"{value_column}", f"@{value_column}%"),
    ]

    plot = figure(
        title=title,
        x_range=x_range,
        y_range=y_range,
        x_axis_location="above",
        width=width,
        height=height,
        tools="hover,save,pan,box_zoom,reset,wheel_zoom",
        toolbar_location="below",
        tooltips=tooltips,
    )

    plot.grid.grid_line_color = plot.axis.axis_line_color = None
    plot.axis.major_tick_line_color = None
    plot.axis.major_label_text_font_size = "7px"
    plot.xaxis.major_label_orientation = pi / 3

    mapper = linear_cmap(
        value_column,
        colors,
        low=data[value_column].min(),
        high=data[value_column].max(),
    )

    heatmap_rectangles = plot.rect(
        x=x_column,
        y=y_column,
        width=1,
        height=1,
        source=data,
        fill_color=mapper,
        line_color=None,
    )

    color_bar = heatmap_rectangles.construct_color_bar(
        major_label_text_font_size="7px",
        ticker=BasicTicker(desired_num_ticks=len(colors)),
        formatter=PrintfTickFormatter(format="%d%%"),
        label_standoff=6,
        border_line_color=None,
        padding=5,
    )
    plot.add_layout(color_bar, "right")

    return plot


def plot_treemap(
    data: pd.DataFrame,
    group_columns: List[str],
    value_column: str,
    title: str = "Treemap Chart",
    width: int = 800,
    height: int = 450,
) -> None:
    """
    Create a hierarchical treemap.
    Best for hierarchical part-to-whole relationships.

    Args:
        data: DataFrame containing the data.
        group_columns: Columns to group by (hierarchy from first to last).
        value_column: Column to aggregate for sizing.
        title: Plot title. Defaults to "Treemap Chart".
        width: Plot width in pixels. Defaults to 800.
        height: Plot height in pixels. Defaults to 450.
    """
    color_palette = Category10[4]

    if len(group_columns) < 2:
        raise ValueError("At least two group columns are required.")

    aggregated_data = data.groupby(group_columns)[value_column].sum().reset_index()
    start_x, start_y = 0, 0
    canvas_width, canvas_height = width, height

    def compute_treemap(
        data_frame: pd.DataFrame,
        value_column: str,
        start_x: float,
        start_y: float,
        width: float,
        height: float,
        max_entries: int = 100,
    ) -> pd.DataFrame:
        """
        Compute the treemap layout for a subset of data.
        """
        subset = data_frame.nlargest(max_entries, value_column)
        sizes = normalize_sizes(subset[value_column], width, height)
        rects = squarify(sizes, start_x, start_y, width, height)
        rects_df = pd.DataFrame(rects, index=subset.index)

        # Join the original subset to preserve additional columns like 'Region'
        return subset.join(rects_df)

    def recursive_treemap(
        data_frame: pd.DataFrame,
        group_levels: List[str],
        start_x: float,
        start_y: float,
        width: float,
        height: float,
    ) -> pd.DataFrame:
        """
        Recursively compute a hierarchical treemap layout.
        """
        if len(group_levels) == 1:  # Base case: last level (smallest categories)
            return compute_treemap(
                data_frame,
                value_column,
                start_x,
                start_y,
                width,
                height,
                max_entries=10,
            )

        current_level = group_levels[0]
        next_level = group_levels[1:]

        # Get the top-level blocks
        top_blocks = compute_treemap(
            data_frame.groupby(current_level).sum().reset_index(),
            value_column,
            start_x,
            start_y,
            width,
            height,
        )

        all_blocks = []
        for _, row in top_blocks.iterrows():
            sub_df = data_frame[data_frame[current_level] == row[current_level]]
            sub_blocks = recursive_treemap(
                sub_df, next_level, row.x, row.y, row.dx, row.dy
            )
            all_blocks.append(sub_blocks)

        return pd.concat(all_blocks)

    treemap_blocks = recursive_treemap(
        aggregated_data, group_columns, start_x, start_y, canvas_width, canvas_height
    )

    treemap_plot = figure(
        width=canvas_width,
        height=canvas_height,
        toolbar_location=None,
        title=title,
        x_axis_location=None,
        y_axis_location=None,
        tooltips=f"@{group_columns[-1]}",
    )
    treemap_plot.grid.grid_line_color = None

    # Color based on top-level category
    top_level_categories = data[group_columns[0]].unique()
    treemap_plot.block(
        "x",
        "y",
        "dx",
        "dy",
        source=treemap_blocks,
        line_color="white",
        line_width=1,
        fill_color=factor_cmap(group_columns[0], color_palette, top_level_categories),
    )

    # Add labels
    treemap_blocks["ytop"] = treemap_blocks.y + treemap_blocks.dy
    treemap_plot.text(
        x="x",
        y="ytop",
        text=group_columns[-1],
        source=treemap_blocks,
        text_font_size="6pt",
        text_color="white",
        x_offset=2,
        y_offset=2,
        text_baseline="top",
    )

    return treemap_plot


def plot_scatter(
    data: pd.DataFrame,
    x_column: str,
    y_column: str,
    title: str = "Scatter Chart",
    width: int = 600,
    height: int = 300,
) -> None:
    """
    Create a scatter plot.
    Best for correlation between two numerical variables.

    Args:
        data: DataFrame containing the data.
        x_column: Column for x-axis values.
        y_column: Column for y-axis values.
        title: Plot title. Defaults to "Scatter Chart".
        width: Plot width in pixels. Defaults to 600.
        height: Plot height in pixels. Defaults to 300.
    """
    # Extract x and y values using specified columns
    x = data[x_column].tolist()
    y = data[y_column].tolist()

    markers = ["circle" if i % 2 == 0 else "square" for i in range(len(x))]
    marker_size = 8

    # Get color palette based on number of points
    num_points = len(data)
    if num_points in tol["Sunset"]:
        palette = tol["Sunset"][num_points]
    else:
        palette = tol["Sunset"][max(tol["Sunset"].keys())]

    # Create color mapper
    color_mapper = linear_cmap(field_name="y", palette=palette, low=min(y), high=max(y))

    # Create data source
    source = ColumnDataSource({"x": x, "y": y, "markers": markers})

    # Configure plot
    plot = Plot(
        title=title, width=width, height=height, min_border=0, toolbar_location=None
    )

    # Create scatter glyph
    scatter = Scatter(
        x="x",
        y="y",
        size=marker_size,
        fill_color=color_mapper,
        line_color=None,
        marker="markers",
    )
    plot.add_glyph(source, scatter)

    # Add axes and grids
    xaxis = LinearAxis()
    yaxis = LinearAxis()
    plot.add_layout(xaxis, "below")
    plot.add_layout(yaxis, "left")
    plot.add_layout(Grid(dimension=0, ticker=xaxis.ticker))
    plot.add_layout(Grid(dimension=1, ticker=yaxis.ticker))

    return plot


def plot_stacked_area(
    data: pd.DataFrame,
    to_include_only: list[str] = None,
    title: str = "Stacked Area Chart",
    width: int = 600,
    height: int = 400,
):
    """
    Create a stacked area chart.
    Best for cumulative trends over time.

    Args:
        data: DataFrame containing the data.
        to_include_only: List of columns to include in the plot.
        title: Plot title. Defaults to "Stacked Area Chart".
        width: Plot width in pixels. Defaults to 600.
        height: Plot height in pixels. Defaults to 400.
    """
    # Calculate stackers automatically if not provided
    stackers = [
        col
        for col in data.columns
        if col != "index" and pd.api.types.is_numeric_dtype(data[col])
    ]

    if to_include_only:
        # Filter the stackers to include only those specified
        stackers = [col for col in stackers if col in to_include_only]

    # Calculate the palette automatically if not provided.
    # Use the 'Sunset' palette from tol with a number of colors equal to the number of stackers.
    num_stackers = len(stackers)
    # tol["Sunset"] is a dict with keys for different numbers of colors.
    if num_stackers in tol["Sunset"]:
        palette = tol["Sunset"][num_stackers]
    else:
        # Use the maximum available colors and cycle if needed
        max_colors = max(tol["Sunset"].keys())
        base_palette = tol["Sunset"][max_colors]
        palette = (base_palette * ((num_stackers // len(base_palette)) + 1))[
            :num_stackers
        ]

    plot = figure(
        x_range=(0, len(data) - 1),
        y_range=(0, data[stackers].sum(axis=1).max() * 1.1),
        width=width,
        height=height,
        title=title,
    )
    plot.grid.minor_grid_line_color = "#eeeeee"

    plot.varea_stack(
        stackers=stackers,
        x="index",
        color=palette,
        legend_label=stackers,
        source=ColumnDataSource(data),
    )

    plot.legend.update(
        orientation="horizontal", background_fill_color="#fafafa", location="top_center"
    )
    return plot


def plot_ridge(
    data: pd.DataFrame,
    to_include_only: list[str] = None,
    width: int = 900,
    title: str = "Ridge Chart",
) -> None:
    """
    Create a ridge plot (joyplot) for numeric samples across categories.
    Best for comparing distributions across categories.

    Args:
        data: DataFrame where columns are categories and rows are samples.
        to_include_only: List of categories to include in the plot.
        title: Plot title. Defaults to "Ridge Chart".
        width: Plot width in pixels. Defaults to 900.
    """
    # Use the DataFrame's columns as the categories.
    categories = list(data.columns)

    if to_include_only:
        # Filter the categories to include only those specified
        categories = [col for col in categories if col in to_include_only]

    # Create a color palette with the correct number of colors.
    palette = [cc.rainbow[i * 15] for i in range(len(categories))]

    def ridge(category, arr, scale):
        # Returns (x, y) pairs, with the x values set to the category label and the y values scaled.
        return list(zip([category] * len(arr), scale * arr))

    # Create a fixed grid over which densities are computed
    all_values = data.values.flatten()
    all_values = all_values[~np.isnan(all_values)]
    x_min = all_values.min() if len(all_values) > 0 else 0
    x_max = all_values.max() if len(all_values) > 0 else 1
    padding = 0.1 * (x_max - x_min) if x_max != x_min else 1
    x_values = linspace(x_min - padding, x_max + padding, 500)

    x_range = (x_min - padding, x_max + padding)

    source = ColumnDataSource(data={"x": x_values})

    plot = figure(
        y_range=categories[::-1],
        width=width,
        x_range=x_range,
        toolbar_location=None,
        title=title,
    )  # Reversed order in y_range

    scale = (250 / len(categories)) * (
        width / 900
    )  # Scale factor for the ridge heights

    # Loop over categories in original order (no reversal)
    for current_category, data_category in enumerate(categories):
        values = (
            data[data_category].dropna().values
        )  # Ensure no NaN values are passed to gaussian_kde
        probability_density_function = gaussian_kde(values)
        probability_y_values = ridge(
            data_category, probability_density_function(x_values), scale
        )
        source.add(probability_y_values, data_category)
        renderers = plot.patch(
            "x",
            data_category,
            color=palette[current_category],
            alpha=0.6,
            line_color="black",
            source=source,
        )
        renderers.name = "patches"  # Assign a name for testing

    plot.background_fill_color = "#efefef"
    plot.xaxis.ticker = BasicTicker()
    plot.xaxis.formatter = BasicTickFormatter()
    plot.ygrid.grid_line_color = None
    plot.xgrid.grid_line_color = "#dddddd"
    plot.xgrid.ticker = plot.xaxis.ticker
    plot.y_range.range_padding = 0.12

    return plot


def plot_histogram(
    data: pd.DataFrame,
    value_column: str = None,
    title="Histogram Chart",
    width=670,
    height=400,
):
    """
    Create a histogram for a numeric column.
    Best for distribution of single numerical variable.

    Args:
        data: DataFrame containing the data.
        value_column: Column to plot as a histogram.
        title: Plot title. Defaults to "Histogram Chart".
        width: Plot width in pixels. Defaults to 670.
        height: Plot height in pixels. Defaults to 400.
    """
    # Ensure the DataFrame has at least one numeric column
    if not data.select_dtypes(include=[np.number]).columns.any():
        raise ValueError("The DataFrame must contain at least one numeric column.")

    # Use the first numeric column if none is specified
    if value_column:
        numeric_column = value_column
    else:
        numeric_column = data.select_dtypes(include=[np.number]).columns[0]

    data_values = data[numeric_column].dropna().values  # Extract values and drop NaNs

    # Calculate data range with padding
    data_min = np.min(data_values)
    data_max = np.max(data_values)
    data_range = data_max - data_min

    # Handle edge case (constant data)
    if data_range == 0:
        data_min -= 1
        data_max += 1
    else:
        padding = 0.05 * data_range  # 5% padding on both sides
        data_min -= padding
        data_max += padding

    # Dynamic bin count based on data size and plot width
    base_data_size = 1000  # Reference size (original example)
    base_width = 670  # Original width
    base_bins = 40  # Original bin count

    # Calculate adjusted bin count
    adjusted_bins = (
        base_bins * np.sqrt(len(data_values) / base_data_size) * (width / base_width)
    )
    bins_count = int(np.clip(adjusted_bins, 15, 100))  # Keep between 15-100 bins

    bins = np.linspace(data_min, data_max, bins_count)

    # Create plot
    plot = figure(width=width, height=height, toolbar_location=None, title=title)

    # Histogram
    hist, edges = np.histogram(data_values, density=True, bins=bins)
    plot.quad(
        top=hist,
        bottom=0,
        left=edges[:-1],
        right=edges[1:],
        fill_color="skyblue",
        line_color="white",
        legend_label="Samples",
    )

    # Probability density function (using actual data stats)
    x = np.linspace(data_min, data_max, 100)
    mean, std = np.mean(data_values), np.std(data_values)
    pdf = np.exp(-0.5 * ((x - mean) / std) ** 2) / (std * np.sqrt(2 * np.pi))
    plot.line(x, pdf, line_width=2, line_color="navy", legend_label="Distribution Line")

    # Styling
    plot.y_range.start = 0
    plot.xaxis.axis_label = numeric_column  # Use column name as x-axis label
    plot.yaxis.axis_label = "Density"  # Default y-axis label
    plot.legend.location = "top_right"

    return plot


def plot_pie(
    data: pd.DataFrame,
    category_column: str,
    value_column: str,
    title: str = "Pie Chart",
    height: int = 350,
) -> None:
    """
    Create a pie chart from DataFrame columns.
    Best for proportional composition of categories.

    Args:
        data: DataFrame containing categories and values.
        category_column: Column with category labels.
        value_column: Column with numeric values.
        title: Plot title. Defaults to "Pie Chart".
        height: Plot height in pixels. Defaults to 350.
    """
    # Ensure the specified columns exist in the DataFrame
    if category_column not in data.columns or value_column not in data.columns:
        raise ValueError(
            f"The DataFrame must contain columns '{category_column}' and '{value_column}'."
        )

    # Prepare the DataFrame for plotting
    df = data[[category_column, value_column]].copy()
    df.columns = ["category", "value"]  # Rename columns for consistency
    df["angle"] = df["value"] / df["value"].sum() * 2 * pi
    df["color"] = Category20c[len(df)]

    # Create the pie chart
    plot = figure(
        height=height,
        title=title,
        toolbar_location=None,
        tools="hover",
        tooltips="@category: @value",
        x_range=(-0.5, 1.0),
    )
    plot.wedge(
        x=0,
        y=1,
        radius=0.4,
        start_angle=cumsum("angle", include_zero=True),
        end_angle=cumsum("angle"),
        line_color="white",
        fill_color="color",
        legend_field="category",
        source=df,
    )
    plot.axis.axis_label = None
    plot.axis.visible = False
    plot.grid.grid_line_color = None
    return plot


def plot_donut(
    data: pd.DataFrame,
    category_column: str,
    value_column: str,
    title: str = "Donut Chart",
    height: int = 500,
) -> None:
    """
    Create a donut chart from DataFrame columns.
    Best for proportional data with emphasis.

    Args:
        data: DataFrame containing categories and values.
        category_column: Column with category labels.
        value_column: Column with numeric values.
        title: Plot title. Defaults to "Donut Chart".
        width: Plot width in pixels. Defaults to 500.
        height: Plot height in pixels. Defaults to 500.
    """
    # Ensure the specified columns exist in the DataFrame
    if category_column not in data.columns or value_column not in data.columns:
        raise ValueError(
            f"The DataFrame must contain columns '{category_column}' and '{value_column}'."
        )

    # Aggregate data
    aggregated = data.groupby(category_column).sum(numeric_only=True)
    selected = aggregated[aggregated[value_column] >= 1].copy()
    selected.loc["Other"] = aggregated[aggregated[value_column] < 1].sum()
    categories = selected.index.tolist()

    # Automatically assign colors using a Bokeh palette
    num_categories = len(categories)
    palette = Category20[
        max(3, num_categories)
    ]  # Use Category20 palette (minimum 3 colors)
    colors = {
        category: palette[i % len(palette)] for i, category in enumerate(categories)
    }

    # Calculate angles for the annular wedges
    angles = selected[value_column].map(lambda x: 2 * pi * (x / 100)).cumsum().tolist()
    source = ColumnDataSource(
        {
            "start": [0] + angles[:-1],
            "end": angles,
            "colors": [colors[category] for category in categories],
        }
    )

    # Create plot with fixed ranges
    x_range_data = Range1d(start=-2, end=2)
    y_range_data = Range1d(start=-2, end=2)

    plot_size = height

    plot = figure(
        x_range=x_range_data,
        y_range=y_range_data,
        title=title,
        toolbar_location=None,
        width=plot_size,
        height=plot_size,
    )

    # Add annular wedges to the plot
    donut_slice = AnnularWedge(
        x=0,
        y=0,
        inner_radius=0.9,
        outer_radius=1.8,
        start_angle="start",
        end_angle="end",
        line_color="white",
        line_width=3,
        fill_color="colors",
    )
    renderer = plot.add_glyph(source, donut_slice)

    # Create a legend
    legend = Legend(location="center")
    for i, category in enumerate(categories):
        legend.items.append(LegendItem(label=category, renderers=[renderer], index=i))
    plot.add_layout(legend, "center")

    return plot


def plot_box(
    data: pd.DataFrame,
    x_column: str,
    y_column: str,
    title: str = "Box Chart",
    width: int = 600,
    height: int = 400,
) -> None:
    """
    Create a box plot with whiskers from DataFrame columns.
    Best for distribution comparison with outliers.

    Args:
        data: DataFrame containing the data.
        x_column: Categorical column for x-axis grouping.
        y_column: Numeric column for y-axis values.
        title: Plot title. Defaults to "Box Chart".
        width: Plot width in pixels. Defaults to 600.
        height: Plot height in pixels. Defaults to 400.
    """
    background_fill_color = "#eaefef"
    df = data.copy()

    # Calculate quantiles for each category
    quantile_summary = (
        df.groupby(x_column)[y_column]
        .quantile([0.25, 0.5, 0.75])
        .unstack()
        .reset_index()
    )
    quantile_summary.columns = [x_column, "q1", "q2", "q3"]

    # Compute IQR and outlier bounds
    quantile_summary["iqr"] = quantile_summary.q3 - quantile_summary.q1
    quantile_summary["upper"] = quantile_summary.q3 + 1.5 * quantile_summary.iqr
    quantile_summary["lower"] = quantile_summary.q1 - 1.5 * quantile_summary.iqr

    # Merge bounds with original data
    df = pd.merge(df, quantile_summary[[x_column, "upper", "lower"]], on=x_column)

    # Prepare data sources
    source = ColumnDataSource(quantile_summary)
    categories = df[x_column].unique()

    # Create figure with configurable size
    plot = figure(
        x_range=categories,
        toolbar_location=None,
        title=title,
        background_fill_color=background_fill_color,
        y_axis_label=y_column,
        width=width,
        height=height,
    )

    # Add whiskers for outlier bounds
    whisker = Whisker(base=x_column, upper="upper", lower="lower", source=source)
    whisker.upper_head.size = whisker.lower_head.size = 20
    plot.add_layout(whisker)

    # Configure color mapping
    palette = (
        Category10[max(3, len(categories))] if len(categories) <= 10 else Category10[10]
    )
    color_map = factor_cmap(x_column, palette=palette, factors=categories)

    # Draw box elements
    plot.vbar(
        x_column, 0.7, "q2", "q3", source=source, color=color_map, line_color="black"
    )
    plot.vbar(
        x_column, 0.7, "q1", "q2", source=source, color=color_map, line_color="black"
    )

    # Plot outliers
    outliers = df[~df[y_column].between(df.lower, df.upper)]
    plot.scatter(
        x_column,
        y_column,
        source=ColumnDataSource(outliers),
        size=6,
        color="black",
        alpha=0.3,
    )

    # Final styling
    plot.xgrid.grid_line_color = None
    plot.axis.major_label_text_font_size = "14px"
    plot.axis.axis_label_text_font_size = "12px"

    return plot
