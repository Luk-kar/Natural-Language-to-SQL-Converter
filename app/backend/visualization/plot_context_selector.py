import pandas as pd
from app.backend.visualization.generator import plots_list
from app.backend.visualization.plot_filter import filter_compatible_plots
from app.backend.visualization.plot_details_extractor import (
    retrieve_plot_function_details,
)

NO_COMPATIBLE_PLOTS_MESSAGE = "No compatible plots found for the given data."


def build_visualization_context(execution_result: dict) -> dict:
    """
    Build a comprehensive context for visualization generation from an SQL query result.

    The function extracts compatible plot configurations, filters the available
    plot functions based on compatibility, and summarizes dataset information.

    Args:
        execution_result (dict): A dictionary containing 'columns' and 'data' from an SQL query.

    Returns:
        dict: A context dictionary that includes:
            - 'compatible_plots': A list of available and compatible plot configurations.
            - 'data_context': Information about the dataset including row count,
                              column types, and sample values.
            - 'error': An error message if context generation fails.
    """
    context = {"compatible_plots": [], "data_context": {}, "error": None}

    try:
        # Get compatible plot names from previous filtering
        compatible_plots = filter_plots_for_dataset(execution_result)
        compatible_names = set(compatible_plots)

        # Get all available plot functions from the codebase
        all_plots = retrieve_plot_function_details()

        # Filter to only include compatible plots
        filtered_plots = [
            plot for plot in all_plots if plot["name"] in compatible_names
        ]

        # Trim the plot metadata for LLM consumption
        context["compatible_plots"] = [
            {
                "name": plot["name"],
                "interface": plot.get("interface", ""),
                "description": plot.get("description", ""),
                "dict_args": plot.get("dict_args", {}),
            }
            for plot in filtered_plots
        ]

        # Add dataset context
        df = pd.DataFrame(execution_result["data"], columns=execution_result["columns"])
        context["data_context"] = {
            "row_count": len(df),
            "columns": {col: str(df[col].dtype) for col in df.columns},
            "sample_3_values": {
                col: df[col].dropna().head(3).tolist() for col in df.columns
            },
        }

    except Exception as e:
        context["error"] = f"Context generation failed:\n{str(e)}"

    return context


def filter_plots_for_dataset(execution_result: dict) -> list[dict]:
    """
    Identify plot configurations that are compatible with the given SQL query result.

    This function converts the query execution result into a DataFrame and uses
    a filtering utility to determine which plot types can be used with the data.

    Args:
        execution_result (dict): A dictionary containing 'columns' and 'data' from an SQL query.

    Returns:
        list[dict]: A list of plot configurations that are compatible with the dataset.

    Raises:
        ValueError: If the execution result format is invalid.
    """
    if (
        not execution_result
        or "data" not in execution_result
        or "columns" not in execution_result
    ):
        raise ValueError(f"Invalid execution result format.\n{execution_result}")

    try:
        df = pd.DataFrame(execution_result["data"], columns=execution_result["columns"])
        return filter_compatible_plots(plots_list, df)
    except Exception as e:
        return []


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
