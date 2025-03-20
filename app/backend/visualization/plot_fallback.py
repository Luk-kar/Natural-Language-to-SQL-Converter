# Third-party
import pandas as pd

# Visualization
from app.backend.visualization.consts import NO_COMPATIBLE_PLOTS_MESSAGE


def generate_fallback_plot_config(execution_result: dict, llm_context: dict) -> dict:
    """
    Generate a fallback plot configuration based on dataset characteristics and compatible plots.

    Args:
        execution_result: Dictionary containing 'data' and 'columns' from SQL execution
        llm_context: Visualization context from build_visualization_context()

    Returns:
        dict: Plot configuration dictionary

    Raises:
        ValueError: If no compatible plots or invalid data
    """

    def extract_required_params(parameter_strings: list[str]) -> list[str]:
        """
        Extract required parameters from a list of parameter strings.
        """

        required_params = []

        for param in parameter_strings:
            if "=" in param or param == "data":
                continue
            param_name = param.split(":")[0].strip()
            required_params.append(param_name)

        return required_params

    def get_required_params(interface: str) -> list:
        """
        Extract required parameters from a plot interface string.
        """

        start_index = interface.find("(")
        end_index = interface.find(")")

        parameters_section = interface[start_index + 1 : end_index]

        parameter_strings = [param.strip() for param in parameters_section.split(",")]

        required_params = extract_required_params(parameter_strings)

        return required_params

    def collect_plot_candidates(compatible_plots: list, plot_priority: list) -> list:
        """
        Collect plot candidates with metadata for fallback plot generation.
        """

        plot_candidates = []

        for plot in compatible_plots:
            plot_name = plot["name"]
            plot_type = plot_name.replace("plot_", "", 1)

            if plot_type not in plot_priority:
                continue

            required_params = get_required_params(plot.get("interface", ""))
            param_count = len(required_params)
            priority = plot_priority.index(plot_type)

            plot_candidates.append((param_count, priority, plot_type, required_params))
        return plot_candidates

    def sort_plot_candidates(plot_candidates: list):
        """
        Sort plot candidates by priority and parameter count.
        """

        plot_candidates.sort(key=lambda x: (x[0], x[1]))

    def create_dataframe_from_execution_result(execution_result: dict) -> pd.DataFrame:
        """
        Create a DataFrame from the execution result.
        """

        try:
            df = pd.DataFrame(
                execution_result["data"], columns=execution_result["columns"]
            )
        except KeyError as e:
            raise ValueError("Invalid execution result format") from e
        return df

    def extract_columns(llm_context: dict) -> dict:
        """
        Extract columns from the visualization context.
        """

        data_context = llm_context.get("data_context")
        columns = data_context.get("columns")
        return columns

    def filter_numerical_columns(columns: dict, categorical_cols: list) -> list:
        """
        Filter numerical columns from all columns.
        """
        return [col for col in columns if col not in categorical_cols]

    def extract_categorical_columns(columns: dict) -> list:
        """
        Extract categorical columns from all columns.
        """
        return [
            col
            for col, dtype in columns.items()
            if dtype == "object"
            or not pd.api.types.is_numeric_dtype(pd.Series(dtype=dtype))
        ]

    def get_compatible_plots(llm_context: dict) -> list:
        """
        Extract compatible plots from the visualization context.
        """

        compatible_plots = llm_context.get("compatible_plots", [])

        if not compatible_plots:
            raise ValueError(NO_COMPATIBLE_PLOTS_MESSAGE)

        return compatible_plots

    def generate_plot_arguments(
        df: pd.DataFrame,
        categorical_cols: list,
        numerical_cols: list,
        plot_candidates: list,
    ) -> dict:
        """
        Generate plot arguments for the first valid plot candidate.

        Returns a dictionary with keys 'plot_type' and 'arguments' if a valid candidate is found,
        otherwise returns an empty dictionary.
        """

        def get_available_columns(
            categorical_cols: list, numerical_cols: list, col_type: str
        ):
            """
            Get available columns based on column type.
            """
            return categorical_cols if col_type == "categorical" else numerical_cols

        for param_count, _, plot_type, req_params in plot_candidates:
            args = {"data": df}
            valid = True
            used_columns = []

            for param in req_params:

                if plot_type == "bar":
                    col_type = "categorical" if "category" in param else "numerical"

                elif plot_type == "scatter":
                    col_type = "numerical"

                elif plot_type == "pie":
                    col_type = "categorical" if "category" in param else "numerical"

                elif plot_type == "histogram":
                    col_type = "numerical"

                elif plot_type == "box":
                    col_type = "categorical" if param == "x_column" else "numerical"

                else:
                    col_type = "numerical" if "value" in param else "categorical"

                # Get available columns for type
                available = [
                    col
                    for col in get_available_columns(
                        categorical_cols, numerical_cols, col_type
                    )
                    if col not in used_columns  # Exclude already used columns
                ]

                if not available:
                    # Fallback to allow reuse if no alternatives
                    available = get_available_columns(
                        categorical_cols, numerical_cols, col_type
                    )

                if not available:
                    valid = False
                    break

                selected_col = available[0]
                args[param] = selected_col
                used_columns.append(selected_col)

            if valid:
                return {"plot_type": plot_type, "arguments": args}

        return {}

    df = create_dataframe_from_execution_result(execution_result)

    columns = extract_columns(llm_context)

    categorical_cols = extract_categorical_columns(columns)
    numerical_cols = filter_numerical_columns(columns, categorical_cols)

    compatible_plots = get_compatible_plots(llm_context)

    # Predefined priority (most popular first)
    plot_priority = [
        "bar",
        "scatter",
        "pie",
        "histogram",
        "box",
        "heatmap",
        "treemap",
        "ridge",
        "donut",
        "stacked_area",
    ]

    plot_candidates = collect_plot_candidates(compatible_plots, plot_priority)

    sort_plot_candidates(plot_candidates)

    plot_arguments = generate_plot_arguments(
        df, categorical_cols, numerical_cols, plot_candidates
    )

    if plot_arguments:
        return plot_arguments

    raise ValueError("No valid configuration could be generated for compatible plots")
