"""
This script defines a Flask web application that generates:
- SQL queries based on user input questions in natural language.
- Executes the generated SQL queries on a PostgreSQL database.
- Descriptions of the database schema in plain language.
- Generates plots based on the executed SQL queries.
- Generate tooltips for the SQL queries.
"""

# Python
import os
import re
import logging

# Backend
from flask import Flask, render_template, request, jsonify, session
import psycopg2
from llama_cpp import Llama

# Flask Configuration
app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", os.urandom(24))  # <-- Add secret key

# Database Configuration
DB_CONFIG = {
    "host": os.getenv("DB_HOST"),
    "port": os.getenv("DB_PORT"),
    "database": os.getenv("DB_NAME"),
    "user": os.getenv("DB_USER_READONLY"),
    "password": os.getenv("DB_PASSWORD_READONLY"),
}

MAX_ROWS_DISPLAY = 100

# Model Configuration
MODEL_NAME = "deepseek-coder-6.7b-instruct.Q4_K_M"
MODEL_PATH = f"backend/models/{MODEL_NAME}.gguf"
LLM = None

# Flask Run Config
FLASK_ENV = os.getenv("FLASK_ENV", "production")
FLASK_DEBUG = os.getenv("FLASK_DEBUG", "False").lower() == "true"
FLASK_RUN_HOST = os.getenv("FLASK_RUN_HOST", "0.0.0.0")
FLASK_RUN_PORT = int(os.getenv("FLASK_RUN_PORT", 5000))


def initialize_llm(model_path):
    """Initialize and return the LLM model."""
    return Llama(
        model_path=model_path,
        n_ctx=4096,  # Context window size (adjust as needed)
        n_threads=4,  # Number of CPU threads
    )


def get_llm():
    """Lazily initialize and return the LLM instance."""
    global LLM
    if LLM is None:
        LLM = initialize_llm(MODEL_PATH)
    return LLM


def get_schema():
    """Retrieve database schema from PostgreSQL"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()

        # Get tables and columns
        cur.execute(
            """
            SELECT 
                table_schema,
                table_name, 
                column_name, 
                data_type, 
                col_description((table_schema || '.' || table_name)::regclass, ordinal_position) AS column_comment
            FROM information_schema.columns 
            WHERE table_schema = 'public'
            ORDER BY table_name, ordinal_position;
            """
        )

        results = cur.fetchall()

        if not results:
            raise ValueError("No tables or columns found in the public schema.")

        schema = []
        current_table = None
        for table_schema, table, column, dtype, comment in results:  # Fixed unpacking
            if table != current_table:
                schema.append(f"\nTable {table_schema}.{table}:")
                schema.append("|Column|Data Type|Comment|")
                schema.append("|------|---------|-------|")
                current_table = table
            schema.append(f"|{column}|({dtype})|{comment}|")

        return "\n".join(schema)

    except Exception as e:
        logging.error("Schema retrieval error:\n%s", str(e))
        raise  # Re-raise the exception for better error handling
    finally:
        if "conn" in locals():
            conn.close()


def generate_sql(schema: str, question: str) -> str:
    """Generate SQL using the LLM model"""

    if not schema:
        schema_part = ""
    else:
        schema_part = f"""Database schema:
                {schema}

            """
    prompt = (
        schema_part
        + f"""
            Convert this question into a Postgres SQL Query Command:
            {question}

            SQL Query:\n
            
            DO NOT ADD ANY OTHER CODE THAN THE DATA QUERY LANGUAGE (DQL)!
            DO NOT ADD ANY COMMENTS OR DESCRIPTIONS!
            DO NOT USE TEMPORARY TABLES OR VIEWS!
            DO NOT USE ANY FUNCTIONS OR PROCEDURES!
            """
    )

    response = LLM.create_completion(
        prompt=prompt,
        max_tokens=256,
        temperature=0.7,
        stop=["</s>"],  # Stop token (adjust based on model requirements)
    )

    generated_text = response["choices"][0]["text"]
    sql_query = extract_sql(generated_text)

    return sql_query


def extract_sql(response_text: str) -> str:
    """Extract SQL query from the generated text"""

    match = re.search(r"(SELECT).+?;", response_text, re.IGNORECASE | re.DOTALL)

    if match:
        return match.group(0).strip()
    else:
        raise ValueError("Generated SQL does not contain a SELECT statement.")


def generate_describe(schema: str, question: str) -> str:
    """Generate a description about the database structure using the LLM model"""
    if not schema:
        raise ValueError("Database schema is empty.")
    else:
        schema_part = f"""Database schema:
    {schema}
    """
        prompt = (
            schema_part
            + f"""

    {question}

    Describe the structure of the database in a way that anyone can understand. 
    Focus on what kind of information is stored and how it is organized, without using technical terms. 
    For example, explain what kinds of records exist and how they relate to each other. 
    DO NOT USE ANY PROGRAMMING CODE OR SQL QUERIES!
    BE CONCISE!
    DO NOT START WITH: 'Answer:', 'Solution', '.etc'
    """
        )
    response = LLM.create_completion(
        prompt=prompt,
        max_tokens=256,
        temperature=0.7,
        stop=["</s>"],
    )
    return response["choices"][0]["text"].strip()


def execute_query(sql: str):
    """Execute SELECT SQL query on PostgreSQL"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        cur.execute(sql)

        if cur.description:  # For SELECT queries
            columns = [desc[0] for desc in cur.description]
            results = cur.fetchall()
            return {"columns": columns, "data": results}
        else:  # For non-SELECT queries
            raise ValueError("Only SELECT queries are supported.")

    except Exception as e:
        return {"error": str(e)}
    finally:
        if "conn" in locals():
            conn.close()


@app.route("/", methods=["GET", "POST"])
def index():
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
                result = {
                    "question": question,
                    "sql": sql,
                    "execution": execution_result,
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


@app.route("/get_last_sql")
def get_last_sql():
    """Return the last generated SQL from session"""
    result = session.get("result")
    # Extract SQL if result exists and contains 'sql', else default message
    sql = (
        result.get("sql", "No SQL queries generated yet")
        if result
        else "No SQL queries generated yet"
    )
    return jsonify({"sql": sql})


if __name__ == "__main__":

    get_llm()  # Initialize LLM
    app.run(host=FLASK_RUN_HOST, port=FLASK_RUN_PORT, debug=FLASK_DEBUG)
