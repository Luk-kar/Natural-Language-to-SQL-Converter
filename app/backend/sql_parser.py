"""
Security-Critical SQL Query Sanitization and Validation Gateway

Acts as the second line of defense against malicious SQL generation, enforcing strict
PostgreSQL DQL compliance while blocking all other command types.
"""

# Python
import re
from typing import Tuple

# Security Patterns
ILLEGAL_OPERATION_PATTERNS = [
    r"INSERT\s+INTO",
    r"UPDATE\s+",
    r"DELETE\s+FROM",
    r"CREATE\s+",
    r"DROP\s+",
    r"ALTER\s+",
    r"TRUNCATE\s+",
    r"GRANT\s+",
    r"REVOKE\s+",
    r"COMMIT\s+",
    r"ROLLBACK\s+",
    r"SAVEPOINT\s+",
    r"WITH\s+RETURNING",
    r"INTO\s+",
]

TERMINATION_PATTERNS = [
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


def extract_sql(input_text: str) -> str:
    """Orchestrate SQL extraction pipeline with security validation"""

    try:
        sanitized_text = _clean_input_text(input_text)
        sql_candidate = _extract_sql_candidate(sanitized_text)
        final_sql = _process_termination_pattern(sql_candidate)

        _validate_security(final_sql)
        return final_sql

    except Exception as e:

        context = _create_error_context(
            e,
            input_text,
            sanitized_text if "sanitized_text" in locals() else "N/A",
            sql_candidate if "sql_candidate" in locals() else "N/A",
        )

        raise ValueError(context) from e


def _clean_input_text(input_text: str) -> str:
    """Sanitize raw input by removing comments and dialect-specific characters"""

    # Remove all SQL comments
    cleaned = re.sub(r"/\*.*?\*/", " ", input_text, flags=re.DOTALL)
    cleaned = re.sub(r"--.*$", " ", cleaned, flags=re.MULTILINE)

    # Strip surrounding backticks
    cleaned = re.sub(r"(^`+)|(`+$)", "", cleaned)

    # Normalize whitespace
    return re.sub(r"\s+", " ", cleaned).strip()


def _extract_sql_candidate(cleaned_text: str) -> str:
    """Identify CTE or SELECT patterns in sanitized text"""

    cte_pattern = re.compile(r"(?i)(?:(WITH\s+.*?\bSELECT\b)|\bSELECT\b).*", re.DOTALL)

    if match := cte_pattern.search(cleaned_text):
        return match.group(0).strip()

    raise ValueError("No valid SQL statement found")


def _process_termination_pattern(extracted_sql: str) -> str:
    """Determine proper statement termination and format"""

    for pattern_name, pattern in TERMINATION_PATTERNS:

        if match := pattern.match(extracted_sql):

            sql_candidate = match.group(1).strip()

            if pattern_name == "semicolon":

                terminated = f"{sql_candidate}{match.group(2)}".rstrip()
                return terminated if terminated.endswith(";") else f"{terminated};"

            if pattern_name == "termination":

                return f"{sql_candidate};"

    raise ValueError("No valid SELECT statement found")


def _validate_security(final_sql: str) -> None:
    """Perform security validation on unquoted SQL content"""

    unquoted = _remove_quoted_content(final_sql)

    # Check for prohibited operations
    for pattern in ILLEGAL_OPERATION_PATTERNS:

        if re.search(pattern, unquoted, re.IGNORECASE):
            raise ValueError(f"Blocked SQL operation detected: {pattern.strip()}")

    # Validate backtick usage
    if final_sql.startswith("`") or final_sql.endswith("`"):

        raise ValueError(f"Invalid backticks in SQL:\n{final_sql}")

    if _has_unquoted_backtick(final_sql):
        raise ValueError(f"Unquoted backticks detected:\n{final_sql}")


def _remove_quoted_content(sql: str) -> str:
    """Replace quoted strings with empty values"""

    return re.sub(r"""('[^']*'|"[^"]*")""", "", sql)


def _has_unquoted_backtick(text: str) -> bool:
    """Detect unquoted backticks in SQL string"""

    return any(m.group() == "`" for m in re.finditer(r'"[^"]*"|\'[^\']*\'|`', text))


def _create_error_context(
    error: Exception, original_input: str, cleaned_text: str, extracted_sql: str
) -> str:
    """Generate detailed error context for security forensics"""

    return (
        f"SQL Extraction Failed: {str(error)}\n"
        f"Original Input: {original_input}\n"
        f"Cleaned Text: {cleaned_text}\n"
        f"Extracted SQL: {extracted_sql}"
    )
