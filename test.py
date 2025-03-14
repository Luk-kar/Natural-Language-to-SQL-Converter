import re
import inspect

from app.backend.visualization import plots

plots_list = [
    name
    for name, obj in inspect.getmembers(plots, inspect.isfunction)
    if re.match(r"plot_.+", name)
]

print(plots_list)
