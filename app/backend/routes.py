"""
Contains the routes for the Flask application.
"""

# Python
import re

# Flask
from flask import render_template, request, jsonify, session, redirect, url_for

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
    Renders the main page and displays any previous results from the session.
    """
    result = session.get("result")
    last_question = session.pop("last_question", None)

    trouble_chars_pattern = r"[\'\"\\\{\}%#]"

    pokemon_questions = [
        "How many Pokémon have Type1 = 'Fire'?",
        "Which Pokémon has the highest Total stat?",
        "What is the average HP of all Pokémon in Generation 1?",
        "How many Pokémon are dual-type (have both Type1 and Type2)?",
        "What is the average Speed of all Pokémon?",
        "What is the max Attack stat among Grass-type Pokémon?",
        "How many Pokémon have Type2 = 'Flying'?",
        "What is the average Sp. Def of Fire-type Pokémon?",
        "Which Pokémon has the lowest Defense stat?",
        "How many Pokémon are in each Generation?",
        "Which Pokémon have Sp. Atk > 100?",
        "How many Pokémon have a Total stat above 500?",
    ]

    if not pokemon_questions:
        raise ValueError("No sample questions set.")

    sanitized_questions = [
        re.sub(trouble_chars_pattern, "", question) for question in pokemon_questions
    ]

    return render_template(
        "index.html",
        result=result,
        last_question=last_question,
        model_name=MODEL_NAME,
        db_name=DB_CONFIG["database"],
        sample_questions=sanitized_questions,
    )


@flask_app.route("/process_question", methods=["POST"])
def process_question():
    """
    Processes the submitted question, generates SQL, executes it, and stores the result in the session.
    """
    result = None
    question = request.form.get("question")
    session["last_question"] = question

    if not question:
        result = {"error": "No question provided"}
        session["result"] = result
        return redirect(url_for("index"))

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
                execution_result["data"] = execution_result["data"][:MAX_ROWS_DISPLAY]

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
                and "error" not in execution_result
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
        session["result"] = result

    return redirect(url_for("index"))


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

        explanation = generate_clause_explanation_response(clause, full_sql)

        return jsonify({"clauseId": clause_id, "explanation": explanation})

    except Exception as e:
        return jsonify({"error": str(e)}), 500
