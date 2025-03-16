import pandas as pd
from app.backend.visualization.generator import plots_list
from app.backend.visualization.plot_filter import filter_compatible_plots


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
        return []

    try:
        df = pd.DataFrame(execution_result["data"], columns=execution_result["columns"])
        return filter_compatible_plots(plots_list, df)
    except Exception as e:
        return []
