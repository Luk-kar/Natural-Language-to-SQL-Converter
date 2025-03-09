import numpy as np
import pandas as pd
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
from bokeh.palettes import tol, Category10, Category20, Category20c
from bokeh.plotting import figure
from bokeh.transform import linear_cmap, factor_cmap, cumsum
from math import pi
from typing import List
from scipy.stats import gaussian_kde
from squarify import normalize_sizes, squarify
import colorcet as cc
from numpy import linspace


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
    n = len(x_values)
    if n in bright:
        colors = bright[n]
    else:
        # If the exact number is not available, use the largest available and repeat/cut as needed.
        max_colors = max(bright.keys())
        palette = bright[max_colors]
        # Repeat the palette if necessary, then cut to the desired length.
        colors = (palette * ((n // len(palette)) + 1))[:n]

    # Create the figure
    x_range = (
        pd.Series(x_values).unique().tolist()
    )  # Convert to Series and get unique values
    p = figure(
        width=width,
        height=height,
        x_range=x_range,
        toolbar_location=None,
        title=title,  # Add title to the plot
    )
    p.vbar(x=x_values, width=bar_width, bottom=0, top=top_values, color=colors)

    # Styling
    p.xaxis.axis_label = category_column
    p.yaxis.axis_label = value_column
    p.xgrid.grid_line_color = None
    p.ygrid.grid_line_color = "#dddddd"

    return p


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

    p = figure(
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

    p.grid.grid_line_color = p.axis.axis_line_color = None
    p.axis.major_tick_line_color = None
    p.axis.major_label_text_font_size = "7px"
    p.xaxis.major_label_orientation = pi / 3

    mapper = linear_cmap(
        value_column,
        colors,
        low=data[value_column].min(),
        high=data[value_column].max(),
    )

    r = p.rect(
        x=x_column,
        y=y_column,
        width=1,
        height=1,
        source=data,
        fill_color=mapper,
        line_color=None,
    )

    color_bar = r.construct_color_bar(
        major_label_text_font_size="7px",
        ticker=BasicTicker(desired_num_ticks=len(colors)),
        formatter=PrintfTickFormatter(format="%d%%"),
        label_standoff=6,
        border_line_color=None,
        padding=5,
    )
    p.add_layout(color_bar, "right")

    return p


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

    grouped = data.groupby(group_columns)[value_column].sum().reset_index()
    x, y, w, h = 0, 0, width, height

    def treemap(
        df: pd.DataFrame,
        col: str,
        x: float,
        y: float,
        dx: float,
        dy: float,
        N: int = 100,
    ) -> pd.DataFrame:
        subset = df.nlargest(N, col)
        sizes = normalize_sizes(subset[col], dx, dy)
        rects = squarify(sizes, x, y, dx, dy)
        rects_df = pd.DataFrame(rects, index=subset.index)
        # Join the original subset to preserve additional columns like 'Region'
        return subset.join(rects_df)

    def recursive_treemap(
        df: pd.DataFrame,
        group_levels: List[str],
        x: float,
        y: float,
        dx: float,
        dy: float,
    ) -> pd.DataFrame:
        if len(group_levels) == 1:  # Base case: last level (smallest categories)
            return treemap(df, value_column, x, y, dx, dy, N=10)

        current_level = group_levels[0]
        next_level = group_levels[1:]

        # Get the top-level blocks
        top_blocks = treemap(
            df.groupby(current_level).sum().reset_index(), value_column, x, y, dx, dy
        )

        all_blocks = []
        for _, row in top_blocks.iterrows():
            sub_df = df[df[current_level] == row[current_level]]
            sub_blocks = recursive_treemap(
                sub_df, next_level, row.x, row.y, row.dx, row.dy
            )
            all_blocks.append(sub_blocks)

        return pd.concat(all_blocks)

    blocks = recursive_treemap(grouped, group_columns, x, y, w, h)

    p = figure(
        width=w,
        height=h,
        toolbar_location=None,
        title=title,
        x_axis_location=None,
        y_axis_location=None,
        tooltips=f"@{group_columns[-1]}",
    )
    p.grid.grid_line_color = None

    # Color based on top-level category
    regions = data[group_columns[0]].unique()
    p.block(
        "x",
        "y",
        "dx",
        "dy",
        source=blocks,
        line_color="white",
        line_width=1,
        fill_color=factor_cmap(group_columns[0], color_palette, regions),
    )

    # Add labels
    blocks["ytop"] = blocks.y + blocks.dy
    p.text(
        x="x",
        y="ytop",
        text=group_columns[-1],
        source=blocks,
        text_font_size="6pt",
        text_color="white",
        x_offset=2,
        y_offset=2,
        text_baseline="top",
    )

    return p


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
    source = ColumnDataSource(dict(x=x, y=y, markers=markers))

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
    title: str = "Stacked Area Chart",
    width: int = 600,
    height: int = 400,
):
    """
    Create a stacked area chart.
    Best for cumulative trends over time.

    Args:
        data: DataFrame containing the data.
        title: Plot title. Defaults to "Stacked Area Chart".
        width: Plot width in pixels. Defaults to 600.
        height: Plot height in pixels. Defaults to 400.
    """
    # Calculate stackers automatically if not provided
    stackers = [col for col in data.columns if col != "index"]

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

    p = figure(
        x_range=(0, len(data) - 1),
        y_range=(0, data[stackers].sum(axis=1).max() * 1.1),
        width=width,
        height=height,
        title=title,
    )
    p.grid.minor_grid_line_color = "#eeeeee"

    p.varea_stack(
        stackers=stackers,
        x="index",
        color=palette,
        legend_label=stackers,
        source=ColumnDataSource(data),
    )

    p.legend.update(
        orientation="horizontal", background_fill_color="#fafafa", location="top_center"
    )
    return p


def plot_ridge(
    data: pd.DataFrame,
    width: int = 900,
    title: str = "Ridge Chart",
) -> None:
    """
    Create a ridge plot (joyplot) for numeric samples across categories.
    Best for comparing distributions across categories.

    Args:
        data: DataFrame where columns are categories and rows are samples.
        title: Plot title. Defaults to "Ridge Chart".
        width: Plot width in pixels. Defaults to 900.
    """
    # Use the DataFrame's columns as the categories.
    categories = list(data.columns)

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
    x = linspace(x_min - padding, x_max + padding, 500)

    x_range = (x_min - padding, x_max + padding)

    source = ColumnDataSource(data=dict(x=x))

    # The categories are the DataFrame's column names (now displayed in the same order)
    categories = list(data.columns)
    p = figure(
        y_range=categories[::-1],
        width=width,
        x_range=x_range,
        toolbar_location=None,
        title=title,  # Add title to the plot
    )  # Reversed order in y_range

    scale = (250 / len(categories)) * (
        width / 900
    )  # Scale factor for the ridge heights

    # Loop over categories in original order (no reversal)
    for i, cat in enumerate(categories):
        values = (
            data[cat].dropna().values
        )  # Ensure no NaN values are passed to gaussian_kde
        pdf = gaussian_kde(values)
        y = ridge(cat, pdf(x), scale)
        source.add(y, cat)
        p.patch(
            "x", cat, color=palette[i], alpha=0.6, line_color="black", source=source
        )

    p.background_fill_color = "#efefef"
    p.xaxis.ticker = BasicTicker()
    p.xaxis.formatter = BasicTickFormatter()
    p.ygrid.grid_line_color = None
    p.xgrid.grid_line_color = "#dddddd"
    p.xgrid.ticker = p.xaxis.ticker
    p.y_range.range_padding = 0.12

    return p


def plot_histogram(data: pd.DataFrame, title="Histogram Chart", width=670, height=400):
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

    # Use the first numeric column for the histogram
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
    p = figure(width=width, height=height, toolbar_location=None, title=title)

    # Histogram
    hist, edges = np.histogram(data_values, density=True, bins=bins)
    p.quad(
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
    p.line(x, pdf, line_width=2, line_color="navy", legend_label="Distribution Line")

    # Styling
    p.y_range.start = 0
    p.xaxis.axis_label = numeric_column  # Use column name as x-axis label
    p.yaxis.axis_label = "Density"  # Default y-axis label
    p.legend.location = "top_right"

    return p


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
    p = figure(
        height=height,
        title=title,
        toolbar_location=None,
        tools="hover",
        tooltips="@category: @value",
        x_range=(-0.5, 1.0),
    )
    p.wedge(
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
    p.axis.axis_label = None
    p.axis.visible = False
    p.grid.grid_line_color = None
    return p


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
        dict(
            start=[0] + angles[:-1],
            end=angles,
            colors=[colors[category] for category in categories],
        )
    )

    # Create plot with fixed ranges
    xdr = Range1d(start=-2, end=2)
    ydr = Range1d(start=-2, end=2)

    plot_size = height

    p = figure(
        x_range=xdr,
        y_range=ydr,
        title=title,
        toolbar_location=None,
        width=plot_size,
        height=plot_size,
    )

    # Add annular wedges to the plot
    glyph = AnnularWedge(
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
    renderer = p.add_glyph(source, glyph)

    # Create a legend
    legend = Legend(location="center")
    for i, category in enumerate(categories):
        legend.items.append(LegendItem(label=category, renderers=[renderer], index=i))
    p.add_layout(legend, "center")

    return p


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
    qs = (
        df.groupby(x_column)[y_column]
        .quantile([0.25, 0.5, 0.75])
        .unstack()
        .reset_index()
    )
    qs.columns = [x_column, "q1", "q2", "q3"]

    # Compute IQR and outlier bounds
    qs["iqr"] = qs.q3 - qs.q1
    qs["upper"] = qs.q3 + 1.5 * qs.iqr
    qs["lower"] = qs.q1 - 1.5 * qs.iqr

    # Merge bounds with original data
    df = pd.merge(df, qs[[x_column, "upper", "lower"]], on=x_column)

    # Prepare data sources
    source = ColumnDataSource(qs)
    categories = df[x_column].unique()

    # Create figure with configurable size
    p = figure(
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
    p.add_layout(whisker)

    # Configure color mapping
    palette = Category10[len(categories)] if len(categories) <= 10 else Category10[10]
    cmap = factor_cmap(x_column, palette=palette, factors=categories)

    # Draw box elements
    p.vbar(x_column, 0.7, "q2", "q3", source=source, color=cmap, line_color="black")
    p.vbar(x_column, 0.7, "q1", "q2", source=source, color=cmap, line_color="black")

    # Plot outliers
    outliers = df[~df[y_column].between(df.lower, df.upper)]
    p.scatter(
        x_column,
        y_column,
        source=ColumnDataSource(outliers),
        size=6,
        color="black",
        alpha=0.3,
    )

    # Final styling
    p.xgrid.grid_line_color = None
    p.axis.major_label_text_font_size = "14px"
    p.axis.axis_label_text_font_size = "12px"

    return p
