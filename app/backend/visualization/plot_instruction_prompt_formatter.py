"""
Provides functionality to generate detailed instructions for the LLM prompt based on
the dataset context and available plot types.


Key Features:
- Lists available plot types with their descriptions and required arguments.
- Provides a summary of the dataset, including column names, data types, and sample values.
- Includes clear instructions for constructing a plot configuration dictionary.
"""

# Visualization

from app.backend.visualization.consts import NO_COMPATIBLE_PLOTS_MESSAGE


def format_plot_selection_instructions(plot_context: dict) -> str:
    """
    Format a detailed instruction string to guide plot selection based on data context.

    This function constructs a multi-section text that includes available plot types,
    a summary of the dataset, and step-by-step instructions for mapping data columns
    to the selected plot's required arguments.

    Args:
        plot_context (dict): A dictionary containing 'compatible_plots' and 'data_context'
                             generated from the SQL query result.

    Returns:
        str: A formatted string with sections for available plots, dataset overview,
             and explicit instructions for selecting and configuring a plot.

    Raises:
        ValueError: If the dataset context does not contain required keys.
    """

    compatible_plots = plot_context.get("compatible_plots", [])
    data_context = plot_context.get("data_context")

    if not isinstance(data_context, dict):
        raise ValueError("data_context must be a dictionary")

    if not compatible_plots:
        return NO_COMPATIBLE_PLOTS_MESSAGE

    required_data_keys = ["columns", "sample_3_values"]
    for key in required_data_keys:
        if key not in data_context:
            raise ValueError(f"data_context must contain '{key}'")

    # Build the Available Plots section
    plots_section = "## Available Plot Types\n\n"

    for plot in compatible_plots:

        name = plot.get("name", "")
        interface = plot.get("interface", "")
        description = "\n".join(
            [line.strip() for line in plot.get("description", "").split("\n")]
        )
        dict_args = plot.get("dict_args", {})

        plots_section += f"### {name}\n"
        plots_section += f"**Function Signature**: `{interface}`\n\n"
        plots_section += f"**Description**: {description}\n\n"
        plots_section += "**Required Arguments**:\n"

        for arg, details in dict_args.items():
            arg_type = details.get("type", "")
            arg_desc = details.get("description", "")
            plots_section += f"- `{arg}` ({arg_type}): {arg_desc}\n"

        plots_section += "\n"

    # Build the Data Context section
    data_section = "## Data Overview\n\n"

    data_section += f"- **Number of Rows**: {data_context.get('row_count')}\n"
    columns = data_context.get("columns")
    sample_values = data_context.get("sample_3_values")
    data_section += "- **Columns**:\n"

    for col, dtype in columns.items():
        samples = sample_values.get(col)
        data_section += f"  - `{col}` ({dtype}): Sample values: {samples}\n"

    # Instructions for the LLM
    instructions = """## Instructions
1. **Select the Plot Type**: Choose the most appropriate plot based on the data structure and the plot's description.
2. **Map Arguments to Columns**: For each required argument in the selected plot, specify the corresponding column name from the data. Use the column names exactly as listed in the Data Overview.
3. **Construct the Configuration**: Return a dictionary with:
   - `"plot_type"`: The name of the chosen plot (e.g., "plot_bar").
   - `"arguments"`: A dictionary mapping each plot argument to the appropriate column name (as a string).

**Example Response**:
```json
{
  "plot_type": "plot_bar",
  "arguments": {
    "data": "df",
    "category_column": "category",
    "value_column": "count"
  }
}
```"""

    # Combine all sections
    full_context = f"{plots_section}\n{data_section}\n{instructions}"
    return full_context
