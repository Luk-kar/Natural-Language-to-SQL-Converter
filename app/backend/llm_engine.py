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

# Project
from app.backend.sql_parser import extract_sql

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
        n_ctx=2048,  # Context window size (adjust as needed)
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
            DO NOT USE TEMPORARY TABLES OR VIEWS!
            DO NOT USE ANY FUNCTIONS OR PROCEDURES!
            YOU CAN USE CTEs (Common Table Expressions)!
            """
    )

    response = LLM.create_completion(
        prompt=prompt,
        temperature=0.7,
        # stop=["</s>"],  # Stop token (adjust based on model requirements)
    )

    generated_text = response["choices"][0]["text"]
    sql_query = extract_sql(generated_text)

    return sql_query


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
    """
        )
    response = LLM.create_completion(
        prompt=prompt,
        temperature=0.7,
        # stop=["</s>"],
    )
    return response["choices"][0]["text"].strip()


def create_chart_dictionary(prompt: str) -> dict:
    """
    Generate a dictionary of arguments for creating a chart using the LLM model,
    based on the provided prompt. Iterates through all response choices, extracts
    code blocks, and attempts to parse them or the entire text as JSON/dict.
    Falls back to a dummy plot if all parsing attempts fail.
    """

    if not isinstance(prompt, str) or not prompt:
        raise ValueError("Prompt must be a non-empty string:\n" + str(prompt))

    response = LLM.create_completion(
        prompt=prompt,
        temperature=0.7,
        stop=["</s>"],
    )

    code_block_pattern = re.compile(r"```.*?\n(.*?)```", re.DOTALL)

    for choice in response.get("choices", []):

        choice_text = choice.get("text", "").strip()

        if not choice_text:
            continue

        # Extract all code blocks from the choice text
        code_blocks = code_block_pattern.findall(choice_text)
        parsed_dict = None

        # Check each code block for valid JSON or dict
        for block in code_blocks:

            dict_str = block.strip()

            try:
                parsed_dict = json.loads(dict_str)

                if isinstance(parsed_dict, dict):
                    return parsed_dict

            except json.JSONDecodeError:
                try:
                    parsed_dict = ast.literal_eval(dict_str)

                    if isinstance(parsed_dict, dict):
                        return parsed_dict

                except (SyntaxError, ValueError):
                    continue  # Move to next block if parsing fails

        # If no valid code blocks, check the entire text
        try:

            parsed_dict = json.loads(choice_text)

            if isinstance(parsed_dict, dict):
                return parsed_dict

        except json.JSONDecodeError:

            try:
                parsed_dict = ast.literal_eval(choice_text)
                if isinstance(parsed_dict, dict):
                    return parsed_dict

            except (SyntaxError, ValueError):
                continue  # Move to next choice if parsing fails

    error_message = "Failed to generate a valid chart configuration.\nResponse:\n"
    if response:
        error_message += str(response)

    raise ValueError(error_message)


def generate_clause_explanation_response(clause, full_sql):
    """
    Generate an explanation for a specific clause in the SQL query using LLM.
    """

    if not isinstance(clause, str) or not clause:
        raise ValueError(
            "Clause cannot be empty non-empty string.\nProvide meaningful SQL segment. The segment:\n"
            + str(clause)
        )

    if not isinstance(full_sql, str) or not full_sql:
        raise ValueError(
            "Full SQL cannot be empty non-empty string.\nnProvide full context.\nThe full SQL:\n"
            + str(full_sql)
        )

    prompt = f"""Given this SQL query:
{full_sql}
Explain this specific part of the query: 
'{clause}'
Keep the explanation concise (1-2 sentences) and focus on its role in the overall query. Use simple language."""

    response = LLM.create_completion(prompt=prompt, temperature=0.4)

    explanation = response["choices"][0]["text"].strip()

    # Remove code blocks from the explanation
    pattern = r"```.*```"

    no_code_base = re.sub(
        pattern,
        "",
        explanation,
        flags=re.DOTALL,
    )

    # Remove unwanted prefixes
    unwanted_prefixes = [
        "Explanation",
        "Answer",
        "Response",
        "Result",
        "Summary",
        "Description",
        "Insight",
        "Analysis",
        "Commentary",
        "Note",
        "Observation",
        "Remark",
        "Feedback",
        "Interpretation",
        "Clarification",
        "Definition",
        "Elaboration",
        "Conclusion",
    ]

    pattern = rf"^\s*\**({'|'.join(unwanted_prefixes)})[^A-Za-z0-9]*"

    no_prefixes = re.sub(
        pattern,
        "",
        no_code_base,
        flags=re.IGNORECASE,
    )

    # Add ... to the end if the answer is more than 1500 characters
    if len(no_prefixes) > 1500:
        response_truncation = "..."
        no_prefixes = (
            no_prefixes[: 1500 - len(response_truncation)] + response_truncation
        )

    return no_prefixes.strip()
