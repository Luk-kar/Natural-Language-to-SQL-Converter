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
            DO NOT ADD ANY COMMENTS OR DESCRIPTIONS!
            DO NOT USE TEMPORARY TABLES OR VIEWS!
            DO NOT USE ANY FUNCTIONS OR PROCEDURES!
            YOU CAN USE CTEs (Common Table Expressions)!
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


def extract_sql(input_text: str) -> str:
    """Extract SQL query from generated text with security checks and PostgreSQL formatting"""

    ILLEGAL_SQL_PATTERN = re.compile(
        r"\b(INSERT\s+INTO|UPDATE\s+|DELETE\s+FROM|"
        r"CREATE|DROP|ALTER|TRUNCATE|GRANT|REVOKE|"
        r"COMMIT|ROLLBACK|SAVEPOINT|WITH\s+RETURNING|INTO\s+)\b",
        re.IGNORECASE,
    )

    try:
        # Initial cleaning
        cleaned_text = re.sub(r"/\*.*?\*/", " ", input_text, flags=re.DOTALL)
        cleaned_text = re.sub(r"--.*$", " ", cleaned_text, flags=re.MULTILINE)

        # Remove one or more backtciks from trailint and start of the string
        cleaned_text = re.sub(r"(^`+)|(`+$)", "", cleaned_text)

        # Final whitespace cleanup
        cleaned_whitespace = re.sub(r"\s+", " ", cleaned_text).strip()

        # CTE pattern matching
        cte_match = re.compile(
            r"(?i)(?:(WITH\s+.*?\bSELECT\b)|\bSELECT\b).*", re.DOTALL
        ).search(cleaned_whitespace)

        if not cte_match:
            raise ValueError("No valid SQL statement found")

        extracted_sql = cte_match.group(0).strip()

        # Pattern processing
        patterns = [
            ("semicolon", re.compile(r"^(.*?)(;|\Z)", re.DOTALL)),
            (
                "termination",
                re.compile(
                    r"^(.*?)(?=\b(?:UNION\s+ALL|UNION|EXCEPT|INTERSECT|LIMIT|OFFSET|FETCH|FOR|"
                    r"ORDER\s+BY|GROUP\s+BY|HAVING|WINDOW)\b)",
                    re.DOTALL | re.IGNORECASE,
                ),
            ),
        ]

        for pattern_name, pattern in patterns:
            if match := pattern.match(extracted_sql):
                sql_candidate = match.group(1).strip()

                if pattern_name == "semicolon":
                    final_sql = f"{sql_candidate}{match.group(2)}".rstrip()
                    final_sql = (
                        final_sql if final_sql.endswith(";") else f"{final_sql};"
                    )
                elif pattern_name == "termination":
                    final_sql = f"{sql_candidate};"

                # Final validation
                if ILLEGAL_SQL_PATTERN.search(final_sql):
                    raise ValueError(f"Blocked dangerous SQL: {final_sql}")

                if final_sql.endswith("`") or final_sql.startswith("`"):
                    raise ValueError(
                        f"Invalid backticks at front or end of SQL:\n{final_sql}"
                    )

                    # To avoid issues with backticks outside of quotes
                if has_unquoted_backtick(final_sql):
                    raise ValueError(
                        f"Invalid backticks in the final_sql:\n{final_sql}"
                    )

                return final_sql

        raise ValueError("No valid SELECT statement found")

    except Exception as e:
        error_context = f"""
        SQL Extraction Failed:{str(e)}
        Original Input: {input_text}
        Cleaned Text:   {cleaned_whitespace if 'cleaned_whitespace' in locals() else 'N/A'}
        Extracted SQL:  {extracted_sql if 'extracted_sql' in locals() else 'N/A'}
        """
        raise ValueError(error_context) from e


def has_unquoted_backtick(text: str) -> bool:
    """Returns True if a backtick (`) exists outside of quotes, otherwise False."""

    pattern = re.compile(r'"[^"]*"|\'[^\']*\'|`')

    return any(m.group() == "`" for m in pattern.finditer(text))


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
        temperature=0.7,
        stop=["</s>"],
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
