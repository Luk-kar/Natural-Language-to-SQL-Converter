"""
This module transforms raw SQL query results into complete visualization artifacts.
The processing pipeline includes:
- Conversion of raw tabular data into a structured DataFrame
- Generation of visualization context layers for plot selection
- Creation of LLM-ready prompt instructions
- Final plot configuration JSON generation

In plain English, it acts as a bridge between database query results
and visualization systems by:
1. Converting raw numbers into analyzable data structures
2. Preparing context for plot type decisions
3. Formatting instructions for automated visualization choices
4. Handling errors and edge cases in data translation

The output is either a JSON-ready visualization specification
or an error message for client handling.
"""

# Third-party
import pandas as pd

# Visualization
from app.backend.visualization.plot_context_selector import (
    build_visualization_context,
)
from app.backend.visualization.plot_router import generate_plot_json
from app.backend.visualization.plot_instruction_prompt_formatter import (
    format_plot_selection_instructions,
)
from app.backend.visualization.consts import NO_COMPATIBLE_PLOTS_MESSAGE

# Flask
from flask import jsonify


def generate_visualization_artifacts(execution: dict) -> jsonify:
    """
    Transform raw execution data into visualization-ready artifacts.

    Args:
        execution: Raw data from query execution containing columns and data rows

    Returns:
        Flask response: Either JSON error response or final visualization JSON
    """

    # Recreate DataFrame from session data
    try:
        df = pd.DataFrame(execution["data"], columns=execution["columns"])
    except KeyError as e:
        return jsonify({"error": f"Missing data in session: {str(e)}"})

    # Build visualization context layers
    chart_generation_context = build_visualization_context(execution)

    prompt_generation_context = format_plot_selection_instructions(
        chart_generation_context
    )
    if prompt_generation_context == NO_COMPATIBLE_PLOTS_MESSAGE:
        return jsonify({"error": NO_COMPATIBLE_PLOTS_MESSAGE})

    # Generate final plot configuration JSON
    return generate_plot_json(
        execution, prompt_generation_context, chart_generation_context, df
    )
