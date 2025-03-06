"""
Below are examples of ten different types of charts that can be generated using Bokeh.
These examples are adapted from the official Bokeh documentation and customized as reference implementations.
They are meant to serve as a guide for generating charts in the application.

version:
bokeh===3.4.3
"""

# ----------------------------
# 1. Bar Chart
# Ideal for comparing categorical data, such as total medals won by different countries.

from bokeh.plotting import figure, show

plot = figure(width=300, height=300)
plot.vbar(x=[1, 2, 3], width=0.5, bottom=0, top=[1, 2, 3], color="#CAB2D6")

show(plot)

# ----------------------------
# 2. ColorBar / Heatmap
# Best for visualizing patterns and relationships in large datasets, such as fruit sales over different seasons.

from math import pi

import pandas as pd

from bokeh.models import BasicTicker, PrintfTickFormatter
from bokeh.plotting import figure, show
from bokeh.sampledata.unemployment1948 import data
from bokeh.transform import linear_cmap

data["Year"] = data["Year"].astype(str)
data = data.set_index("Year")
data.drop("Annual", axis=1, inplace=True)
data.columns.name = "Month"

years = list(data.index)
months = list(reversed(data.columns))

# reshape to 1D array or rates with a month and year for each row.
df = pd.DataFrame(data.stack(), columns=["rate"]).reset_index()

# this is the colormap from the original NYTimes plot
colors = [
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

TOOLS = "hover,save,pan,box_zoom,reset,wheel_zoom"

p = figure(
    title=f"US Unemployment ({years[0]} - {years[-1]})",
    x_range=years,
    y_range=months,
    x_axis_location="above",
    width=900,
    height=400,
    tools=TOOLS,
    toolbar_location="below",
    tooltips=[("date", "@Month @Year"), ("rate", "@rate%")],
)

p.grid.grid_line_color = None
p.axis.axis_line_color = None
p.axis.major_tick_line_color = None
p.axis.major_label_text_font_size = "7px"
p.axis.major_label_standoff = 0
p.xaxis.major_label_orientation = pi / 3

r = p.rect(
    x="Year",
    y="Month",
    width=1,
    height=1,
    source=df,
    fill_color=linear_cmap("rate", colors, low=df.rate.min(), high=df.rate.max()),
    line_color=None,
)

p.add_layout(
    r.construct_color_bar(
        major_label_text_font_size="7px",
        ticker=BasicTicker(desired_num_ticks=len(colors)),
        formatter=PrintfTickFormatter(format="%d%%"),
        label_standoff=6,
        border_line_color=None,
        padding=5,
    ),
    "right",
)

show(p)

# ----------------------------
# 3. Treemap Plot
# Represents the density of points by grouping them into hexagonal bins; useful for large scatter datasets.

import pandas as pd
from squarify import normalize_sizes, squarify

from bokeh.plotting import figure, show
from bokeh.sampledata.sample_superstore import data
from bokeh.transform import factor_cmap

data = data[["City", "Region", "Sales"]]

regions = ("West", "Central", "South", "East")

sales_by_city = data.groupby(["Region", "City"]).sum("Sales")
sales_by_city = sales_by_city.sort_values(by="Sales").reset_index()

sales_by_region = sales_by_city.groupby("Region").sum("Sales").sort_values(by="Sales")


def treemap(df, col, x, y, dx, dy, *, N=100):
    sub_df = df.nlargest(N, col)
    normed = normalize_sizes(sub_df[col], dx, dy)
    blocks = squarify(normed, x, y, dx, dy)
    blocks_df = pd.DataFrame.from_dict(blocks).set_index(sub_df.index)
    return sub_df.join(blocks_df, how="left").reset_index()


x, y, w, h = 0, 0, 800, 450

blocks_by_region = treemap(sales_by_region, "Sales", x, y, w, h)

dfs = []
for index, (Region, Sales, x, y, dx, dy) in blocks_by_region.iterrows():
    df = sales_by_city[sales_by_city.Region == Region]
    dfs.append(treemap(df, "Sales", x, y, dx, dy, N=10))
blocks = pd.concat(dfs)

p = figure(
    width=w,
    height=h,
    tooltips="@City",
    toolbar_location=None,
    x_axis_location=None,
    y_axis_location=None,
)
p.x_range.range_padding = p.y_range.range_padding = 0
p.grid.grid_line_color = None

p.block(
    "x",
    "y",
    "dx",
    "dy",
    source=blocks,
    line_width=1,
    line_color="white",
    fill_alpha=0.8,
    fill_color=factor_cmap("Region", "MediumContrast4", regions),
)

p.text(
    "x",
    "y",
    x_offset=2,
    text="Region",
    source=blocks_by_region,
    text_font_size="18pt",
    text_color="white",
)

blocks["ytop"] = blocks.y + blocks.dy
p.text(
    "x",
    "ytop",
    x_offset=2,
    y_offset=2,
    text="City",
    source=blocks,
    text_font_size="6pt",
    text_baseline="top",
    text_color=factor_cmap("Region", ("black", "white", "black", "white"), regions),
)

show(p)

# ----------------------------
# 4. Scatter Plot
# Best for identifying relationships between two continuous variables with a third variable represented by color.

import numpy as np

from bokeh.core.enums import MarkerType
from bokeh.io import curdoc, show
from bokeh.models import ColumnDataSource, Grid, LinearAxis, Plot, Scatter

N = len(MarkerType)
x = np.linspace(-2, 2, N)
y = x**2
markers = list(MarkerType)

source = ColumnDataSource(dict(x=x, y=y, markers=markers))

plot = Plot(title=None, width=300, height=300, min_border=0, toolbar_location=None)

glyph = Scatter(x="x", y="y", size=20, fill_color="#74add1", marker="markers")
plot.add_glyph(source, glyph)

xaxis = LinearAxis()
plot.add_layout(xaxis, "below")

yaxis = LinearAxis()
plot.add_layout(yaxis, "left")

plot.add_layout(Grid(dimension=0, ticker=xaxis.ticker))
plot.add_layout(Grid(dimension=1, ticker=yaxis.ticker))

curdoc().add_root(plot)

show(plot)

# ----------------------------
# 5. Stacked Area Plot
# Best for visualizing trends over time and the cumulative contribution of different series.

import numpy as np
import pandas as pd

from bokeh.palettes import tol
from bokeh.plotting import figure, show

N = 10
df = pd.DataFrame(np.random.randint(10, 100, size=(15, N))).add_prefix("y")

p = figure(x_range=(0, len(df) - 1), y_range=(0, 800))
p.grid.minor_grid_line_color = "#eeeeee"

names = [f"y{i}" for i in range(N)]
p.varea_stack(
    stackers=names, x="index", color=tol["Sunset"][N], legend_label=names, source=df
)

p.legend.orientation = "horizontal"
p.legend.background_fill_color = "#fafafa"

show(p)

# ----------------------------
# 6. ridgeplot
# Useful for visualizing the distribution of a dataset across multiple categories.

import colorcet as cc
from numpy import linspace
from scipy.stats import gaussian_kde

from bokeh.models import ColumnDataSource, FixedTicker, PrintfTickFormatter
from bokeh.plotting import figure, show
from bokeh.sampledata.perceptions import probly


def ridge(category, data, scale=20):
    return list(zip([category] * len(data), scale * data))


cats = list(reversed(probly.keys()))

palette = [cc.rainbow[i * 15] for i in range(17)]

x = linspace(-20, 110, 500)

source = ColumnDataSource(data=dict(x=x))

p = figure(y_range=cats, width=900, x_range=(-5, 105), toolbar_location=None)

for i, cat in enumerate(reversed(cats)):
    pdf = gaussian_kde(probly[cat])
    y = ridge(cat, pdf(x))
    source.add(y, cat)
    p.patch("x", cat, color=palette[i], alpha=0.6, line_color="black", source=source)

p.outline_line_color = None
p.background_fill_color = "#efefef"

p.xaxis.ticker = FixedTicker(ticks=list(range(0, 101, 10)))
p.xaxis.formatter = PrintfTickFormatter(format="%d%%")

p.ygrid.grid_line_color = None
p.xgrid.grid_line_color = "#dddddd"
p.xgrid.ticker = p.xaxis.ticker

p.axis.minor_tick_line_color = None
p.axis.major_tick_line_color = None
p.axis.axis_line_color = None

p.y_range.range_padding = 0.12

show(p)

# ----------------------------
# 7. Histogram
# Used for understanding the distribution of a dataset by showing the frequency of data points in intervals.
"""
- `values` (iterable): a 1d array of numeric data.
- `bins` (int): number of bins to use for grouping data.
- `density` (bool, optional): if True, normalizes the histogram. Defaults to `True`.
"""

import numpy as np

from bokeh.plotting import figure, show

rng = np.random.default_rng()
x = rng.normal(loc=0, scale=1, size=1000)

p = figure(
    width=670, height=400, toolbar_location=None, title="Normal (Gaussian) Distribution"
)

# Histogram
bins = np.linspace(-3, 3, 40)
hist, edges = np.histogram(x, density=True, bins=bins)
p.quad(
    top=hist,
    bottom=0,
    left=edges[:-1],
    right=edges[1:],
    fill_color="skyblue",
    line_color="white",
    legend_label="1000 random samples",
)

# Probability density function
x = np.linspace(-3.0, 3.0, 100)
pdf = np.exp(-0.5 * x**2) / np.sqrt(2.0 * np.pi)
p.line(
    x, pdf, line_width=2, line_color="navy", legend_label="Probability Density Function"
)

p.y_range.start = 0
p.xaxis.axis_label = "x"
p.yaxis.axis_label = "PDF(x)"

show(p)

# ----------------------------
# 8. Pie Chart
# Suitable for displaying proportions of a whole, where each slice represents a category's contribution.

from math import pi

import pandas as pd

from bokeh.palettes import Category20c
from bokeh.plotting import figure, show
from bokeh.transform import cumsum

x = {
    "United States": 157,
    "United Kingdom": 93,
    "Japan": 89,
    "China": 63,
    "Germany": 44,
    "India": 42,
    "Italy": 40,
    "Australia": 35,
    "Brazil": 32,
    "France": 31,
    "Taiwan": 31,
    "Spain": 29,
}

data = pd.Series(x).reset_index(name="value").rename(columns={"index": "country"})
data["angle"] = data["value"] / data["value"].sum() * 2 * pi
data["color"] = Category20c[len(x)]

p = figure(
    height=350,
    title="Pie Chart",
    toolbar_location=None,
    tools="hover",
    tooltips="@country: @value",
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
    legend_field="country",
    source=data,
)

p.axis.axis_label = None
p.axis.visible = False
p.grid.grid_line_color = None

show(p)

# ----------------------------
# 9. Donut Chart
# A variation of the pie chart with a central hole, ideal for aesthetic representation of proportional data.

from math import pi

from bokeh.io import show
from bokeh.models import (
    AnnularWedge,
    ColumnDataSource,
    Legend,
    LegendItem,
    Plot,
    Range1d,
)
from bokeh.sampledata.browsers import browsers_nov_2013 as df

xdr = Range1d(start=-2, end=2)
ydr = Range1d(start=-2, end=2)

plot = Plot(x_range=xdr, y_range=ydr)
plot.title.text = "Web browser market share (November 2013)"
plot.toolbar_location = None

colors = {
    "Chrome": "seagreen",
    "Firefox": "tomato",
    "Safari": "orchid",
    "Opera": "firebrick",
    "IE": "skyblue",
    "Other": "lightgray",
}

aggregated = df.groupby("Browser").sum(numeric_only=True)
selected = aggregated[aggregated.Share >= 1].copy()
selected.loc["Other"] = aggregated[aggregated.Share < 1].sum()
browsers = selected.index.tolist()

angles = selected.Share.map(lambda x: 2 * pi * (x / 100)).cumsum().tolist()

browsers_source = ColumnDataSource(
    dict(
        start=[0] + angles[:-1],
        end=angles,
        colors=[colors[browser] for browser in browsers],
    )
)

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
r = plot.add_glyph(browsers_source, glyph)

legend = Legend(location="center")
for i, name in enumerate(colors):
    legend.items.append(LegendItem(label=name, renderers=[r], index=i))
plot.add_layout(legend, "center")

show(plot)

# ----------------------------
# 10. Boxplot Chart
# Commonly used to display the distribution of a dataset, showing the median, quartiles, and outliers.

import pandas as pd

from bokeh.models import ColumnDataSource, Whisker
from bokeh.plotting import figure, show
from bokeh.sampledata.autompg2 import autompg2
from bokeh.transform import factor_cmap

df = autompg2[["class", "hwy"]].rename(columns={"class": "kind"})

kinds = df.kind.unique()

# compute quantiles
qs = df.groupby("kind").hwy.quantile([0.25, 0.5, 0.75])
qs = qs.unstack().reset_index()
qs.columns = ["kind", "q1", "q2", "q3"]

# compute IQR outlier bounds
iqr = qs.q3 - qs.q1
qs["upper"] = qs.q3 + 1.5 * iqr
qs["lower"] = qs.q1 - 1.5 * iqr
df = pd.merge(df, qs, on="kind", how="left")

source = ColumnDataSource(qs)

p = figure(
    x_range=kinds,
    tools="",
    toolbar_location=None,
    title="Highway MPG distribution by vehicle class",
    background_fill_color="#eaefef",
    y_axis_label="MPG",
)

# outlier range
whisker = Whisker(base="kind", upper="upper", lower="lower", source=source)
whisker.upper_head.size = whisker.lower_head.size = 20
p.add_layout(whisker)

# quantile boxes
cmap = factor_cmap("kind", "TolRainbow7", kinds)
p.vbar("kind", 0.7, "q2", "q3", source=source, color=cmap, line_color="black")
p.vbar("kind", 0.7, "q1", "q2", source=source, color=cmap, line_color="black")

# outliers
outliers = df[~df.hwy.between(df.lower, df.upper)]
p.scatter("kind", "hwy", source=outliers, size=6, color="black", alpha=0.3)

p.xgrid.grid_line_color = None
p.axis.major_label_text_font_size = "14px"
p.axis.axis_label_text_font_size = "12px"

show(p)
