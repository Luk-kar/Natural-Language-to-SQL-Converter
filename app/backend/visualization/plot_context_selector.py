import pandas as pd
from app.backend.visualization.generator import plots_list
from app.backend.visualization.plot_filter import filter_compatible_plots
from app.backend.visualization.plot_extractor import extract_plot_functions


def get_compatible_plots(execution_result: dict) -> list[dict]:
    """
    Determine compatible plots based on the result from an SQL query execution.

    Args:
        execution_result (dict): The result from execute_query, containing 'columns' and 'data'.

    Returns:
        list[dict]: List of compatible plot configurations.
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


def generate_plot_context(execution_result: dict) -> dict:
    """
    Generate context for the Lineage Link Mapper based on the result from an SQL query execution.

    Args:
        execution_result (dict): The result from execute_query, containing 'columns' and 'data'.

    Returns:
        dict: Context for the Lineage Link Mapper.
    """
    context = {"compatible_plots": [], "data_context": {}, "error": None}

    try:
        # Get compatible plot names from previous filtering
        compatible_plots = get_compatible_plots(execution_result)
        compatible_names = set(compatible_plots)

        # Get all available plot functions from the codebase
        all_plots = extract_plot_functions()

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
            }
            for plot in filtered_plots
        ]

        # Add dataset context
        df = pd.DataFrame(execution_result["data"], columns=execution_result["columns"])
        context["data_context"] = {
            "row_count": len(df),
            "columns": {col: str(df[col].dtype) for col in df.columns},
            "sample_values": {
                col: df[col].dropna().head(3).tolist() for col in df.columns
            },
        }

    except Exception as e:
        context["error"] = f"Context generation failed:\n{str(e)}"

    return context
