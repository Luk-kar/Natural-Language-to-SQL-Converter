"""
Contains the functions to generate SQL queries and database descriptions using the LLM model.
"""

# Python
import ast
import json
import os
import re

# LLM
from llama_cpp import Llama

# Model Configuration
# MODEL_NAME = "deepseek-coder-6.7b-instruct.Q4_K_M"
MODEL_NAME = "ggml-model-Q4_K_M"
MODEL_PATH = os.path.join(os.path.dirname(__file__), "models", f"{MODEL_NAME}.gguf")

LLM = None


def get_llm():
    """Lazily initialize and return the LLM instance"""
    global LLM
    if LLM is None:
        LLM = initialize_llm()
    return LLM


def initialize_llm():
    """Initialize and return the LLM model."""
    return Llama(
        model_path=MODEL_PATH,
        n_ctx=1024,  # Context window size (adjust as needed)
        # n_threads=4,  # Number of CPU threads
    )


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
        raise ValueError(
            "Generated SQL does not contain a SELECT statement:\n" + response_text
        )


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


def create_chart_dictionary(prompt: str) -> dict:
    """
    Generate a dictionary of arguments for creating a chart using the LLM model,
    based on the provided prompt.
    """

    response = LLM.create_completion(
        prompt=prompt,
        temperature=0.7,
        stop=["</s>"],
    )

    text = response["choices"][0]["text"].strip()

    # Extract the code block content if present
    code_block_pattern = re.compile(r"```.*?\n(.*?)```", re.DOTALL)
    match = code_block_pattern.search(text)
    if match:
        dict_str = match.group(1).strip()
    else:
        dict_str = text.strip()

    # Attempt to parse the extracted string as JSON
    try:
        plot_args = json.loads(dict_str)
    except json.JSONDecodeError:
        # If JSON parsing fails, try parsing as a Python literal
        try:
            plot_args = ast.literal_eval(dict_str)
        except (SyntaxError, ValueError) as e:
            raise ValueError(
                f"Failed to parse the response as a valid dictionary: {str(e)}"
            ) from e

    # Ensure the result is a dictionary
    if not isinstance(plot_args, dict):
        raise ValueError("The response did not produce a valid dictionary.")

    return plot_args
