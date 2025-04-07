"""
Contains the routes for the Flask application.
"""

# Flask
from flask import render_template, request, jsonify, session

# Flask configuration
from app.backend.flask_configuration import MAX_ROWS_DISPLAY, flask_app

# Database
from app.backend.database import get_schema, execute_query, DB_CONFIG

# LLM
from app.backend.llm_engine import (
    generate_sql,
    generate_describe,
    generate_clause_explanation_response,
    MODEL_NAME,
)

# Visualization
from app.backend.visualization.plot_artifact_generator import (
    generate_visualization_artifacts,
)
from app.backend.visualization.plot_fallback import generate_fallback_plot_config
from app.backend.visualization.plot_instruction_prompt_formatter import (
    format_plot_selection_instructions,
    NO_COMPATIBLE_PLOTS_MESSAGE,
)
from app.backend.visualization.plot_context_selector import (
    build_visualization_context,
)


@flask_app.route("/", methods=["GET", "POST"])
def index():
    """
    Starting point for the web application.
    Handles the form submission and generates SQL queries.
    """

    result = None

    if request.method == "POST":
        question = request.form["question"]
        try:
            schema = get_schema()

            if question.strip().upper().startswith("DESCRIBE:"):

                stripped_question = question.strip()[len("DESCRIBE:") :].strip()
                description = generate_describe(schema, stripped_question)
                result = {"question": question, "describe": description}

            else:

                sql = generate_sql(schema, question)
                execution_result = execute_query(sql)

                if "data" in execution_result:
                    execution_result["data"] = execution_result["data"][
                        :MAX_ROWS_DISPLAY
                    ]

                is_chart_possible = False
                try:

                    chart_context = build_visualization_context(execution_result)

                    prompt_context = format_plot_selection_instructions(chart_context)
                    is_chart_possible = prompt_context != NO_COMPATIBLE_PLOTS_MESSAGE

                    if is_chart_possible:
                        generate_fallback_plot_config(execution_result, chart_context)

                except (ValueError, KeyError, TypeError):
                    is_chart_possible = False

                except Exception as e:
                    is_chart_possible = False

                data_valid = (
                    "data" in execution_result
                    and len(execution_result.get("data", [])) > 0
                    and "error" not in execution_result,
                )

                result = {
                    "question": question,
                    "sql": sql,
                    "execution": execution_result,
                    "chart_available": data_valid and is_chart_possible,
                }

                session["result"] = result

        except Exception as e:
            result = {"error": str(e)}

    return render_template(
        "index.html",
        result=result,
        model_name=MODEL_NAME,
        db_name=DB_CONFIG["database"],
    )


@flask_app.route("/generate_plots")
def generate_plots():
    """
    Generate a plot based on the previously executed SQL query result.
    """

    result = session.get("result")

    if not result:
        return jsonify({"error": "No data available for plotting"}), 400

    if "execution" not in result:
        return jsonify({"error": "No execution data available"}), 400

    execution = result["execution"]

    if "data" not in execution:
        return jsonify({"error": "No dataset available for plotting"}), 400

    return generate_visualization_artifacts(execution)


@flask_app.route("/generate_clause_explanation", methods=["POST"])
def generate_clause_explanation():

    if not request.is_json:
        return jsonify({"error": "Request must be JSON"}), 400

    data = request.get_json()
    # Validate presence of required fields
    required_fields = ["clause", "fullSql", "clauseId"]
    missing = [field for field in required_fields if field not in data]

    if missing:
        return jsonify({"error": f"Missing required fields: {missing}"}), 400

    # Validate field types
    if not isinstance(data["clauseId"], (str, int)):
        return jsonify({"error": "clauseId must be string or integer"}), 400

    try:
        clause = data["clause"]
        full_sql = data["fullSql"]
        clause_id = data["clauseId"]

        response = generate_clause_explanation_response(clause, full_sql)

        explanation = response["choices"][0]["text"].strip()

        return jsonify({"clauseId": clause_id, "explanation": explanation})

    except Exception as e:
        return jsonify({"error": str(e)}), 500
