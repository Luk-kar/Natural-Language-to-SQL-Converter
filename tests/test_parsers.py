# Python
import unittest
from unittest.mock import patch

# LLM
from app.backend.llm_engine import (
    extract_sql,
)

from app.backend.visualization.plot_details_extractor import (
    retrieve_plot_function_details,
)


class TestExtractSQL(unittest.TestCase):
    """
    Test suite for validating SQL query extraction with enhanced error handling,
    CTE support, and comment stripping.
    """

    # Positive Test Cases
    def test_basic_select(self):
        """Test extraction of simple SELECT statement"""

        input_text = "Result: SELECT id, name FROM users WHERE active = true;"
        expected = "SELECT id, name FROM users WHERE active = true;"

        self.assertEqual(extract_sql(input_text), expected)

    def test_cte_select(self):
        """Test extraction of SELECT with Common Table Expression"""

        input_text = """Analysis:
            WITH recent_orders AS (
                SELECT * FROM orders WHERE order_date > '2023-01-01'
            )
            SELECT customer_id, COUNT(*) FROM recent_orders GROUP BY 1
        """
        expected = (
            "WITH recent_orders AS ( SELECT * FROM orders WHERE order_date > '2023-01-01' ) "
            "SELECT customer_id, COUNT(*) FROM recent_orders GROUP BY 1;"
        )
        self.assertEqual(extract_sql(input_text), expected)

    def test_comments_in_sql(self):
        """Test stripping of PostgreSQL comments"""

        input_text = """/* Get active users */
            SELECT 
                id, -- user ID
                name /* full name */
            FROM users
            WHERE active = true
        """

        expected = "SELECT id, name FROM users WHERE active = true;"
        self.assertEqual(extract_sql(input_text), expected)

    def test_missing_semicolon(self):
        """Test automatic semicolon addition"""

        input_text = "Data: SELECT product, price FROM inventory"
        expected = "SELECT product, price FROM inventory;"

        self.assertEqual(extract_sql(input_text), expected)

    def test_case_insensitive_select(self):
        """Test case-insensitive matching"""

        input_text = "/* JSON format */ select * from api_logs"
        expected = "select * from api_logs;"

        self.assertEqual(extract_sql(input_text).lower(), expected.lower())

    def test_multiline_sql(self):
        """Test handling of multi-line queries"""

        input_text = """
            SELECT id,
                   name,
                   email
            FROM users
            WHERE department = 'engineering'
            ORDER BY name
        """

        expected = (
            "SELECT id, name, email FROM users WHERE department = 'engineering' "
            "ORDER BY name;"
        )

        self.assertEqual(extract_sql(input_text), expected)

    # Negative Test Cases
    def test_no_select_statement(self):
        """Test detection of missing SELECT statement"""

        input_text = "INSERT INTO users (name) VALUES ('test')"
        with self.assertRaises(ValueError) as ctx:
            extract_sql(input_text)

        self.assertIn("No valid SQL statement found", str(ctx.exception))
        self.assertIn("Cleaned Text:", str(ctx.exception))
        self.assertIn("Extracted SQL:", str(ctx.exception))
        self.assertIn("N/A", str(ctx.exception))

    def test_select_into_dml(self):
        """Test blocking of SELECT INTO statements"""

        input_text = "SELECT * INTO new_table FROM current_data"

        with self.assertRaises(ValueError) as ctx:
            extract_sql(input_text)

        self.assertIn("Blocked potentially dangerous SQL operation", str(ctx.exception))
        self.assertIn("INTO", str(ctx.exception))
        self.assertIn("Original Input:", str(ctx.exception))
        self.assertIn("Cleaned Text:", str(ctx.exception))
        self.assertIn("Extracted SQL:", str(ctx.exception))

    def test_missing_semicolon_at_end(self):
        """Test detection of malformed SELECT statements"""

        input_text = "SELECT id name FROM users"  # Missing semicolon

        expected = "SELECT id name FROM users;"

        self.assertEqual(extract_sql(input_text), expected)

    def test_error_context_inclusion(self):
        """Verify error context contains debugging information"""

        input_text = "Find dad jokes."

        try:
            extract_sql(input_text)

        except ValueError as e:
            self.assertIn("SQL Extraction Failed:", str(e))
            self.assertIn("Original Input:", str(e))
            self.assertIn("Cleaned Text:", str(e))
        else:
            self.fail("Expected ValueError not raised")


class TestPlotInterfaceParser(unittest.TestCase):
    """
    Test suite for validating the parsing of plot function metadata from source code.

    This class tests the extraction of function signatures, parameter types,
    and docstring documentation for various function patterns including:
    - Required and optional parameters
    - Type hints and missing type information
    - Docstring formatting variations
    - Multi-function file processing
    """

    def test_function_with_required_params_only(self):
        """Test a function with only required parameters."""
        content = """
def func1(a: int, b: str):
    \"\"\"Args:
        a: Integer parameter.
        b: String parameter.
    \"\"\"
    pass
"""
        # Mock read_code_from_file to return the test content directly
        with patch(
            "app.backend.visualization.plot_details_extractor.read_code_from_file"
        ) as mock_read:
            mock_read.return_value = content.strip()
            result = retrieve_plot_function_details()

        self.assertEqual(len(result), 1)
        func = result[0]
        self.assertEqual(func["name"], "func1")
        self.assertEqual(func["interface"], "def func1(a: int, b: str):")

        self.assertEqual(
            func["dict_args"],
            {
                "a": {"type": "int", "description": "Integer parameter."},
                "b": {"type": "str", "description": "String parameter."},
            },
        )

    def test_function_with_default_params(self):
        """Test a function with parameters having default values."""
        content = """
def func2(a: int, b: str = "default"):
    \"\"\"Args:
        a: Integer parameter.
        b: String parameter. Defaults to "default".
    \"\"\"
    pass
"""
        with patch(
            "app.backend.visualization.plot_details_extractor.read_code_from_file"
        ) as mock_read:
            mock_read.return_value = content.strip()
            result = retrieve_plot_function_details()

        self.assertEqual(len(result), 1)
        func = result[0]
        self.assertEqual(func["interface"], "def func2(a: int):")
        self.assertEqual(
            func["dict_args"],
            {
                "a": {"type": "int", "description": "Integer parameter."},
            },
        )

    def test_function_with_no_params(self):
        """Test a function with no parameters."""
        content = """
def func3():
    \"\"\"No parameters here.\"\"\"
    pass
"""
        with patch(
            "app.backend.visualization.plot_details_extractor.read_code_from_file"
        ) as mock_read:
            mock_read.return_value = content.strip()
            result = retrieve_plot_function_details()

        self.assertEqual(len(result), 1)
        func = result[0]
        self.assertEqual(func["interface"], "def func3():")
        self.assertEqual(func["dict_args"], {})

    def test_docstring_with_args_and_returns(self):
        """Test docstring containing Args and Returns sections."""
        content = """
def func4(a: int):
    \"\"\"Args:
        a: Integer parameter.
    Returns:
        int: Result.
    \"\"\"
    return a
"""
        with patch(
            "app.backend.visualization.plot_details_extractor.read_code_from_file"
        ) as mock_read:
            mock_read.return_value = content.strip()
            result = retrieve_plot_function_details()

        func = result[0]
        self.assertIn("Args:", func["description"])
        self.assertEqual(
            func["dict_args"],
            {
                "a": {"type": "int", "description": "Integer parameter."},
            },
        )

    def test_parameter_without_type_hint(self):
        """Test a parameter without a type hint."""
        content = """
def func5(a):
    \"\"\"Args:
        a: Some parameter.
    \"\"\"
    pass
"""
        with patch(
            "app.backend.visualization.plot_details_extractor.read_code_from_file"
        ) as mock_read:
            mock_read.return_value = content.strip()
            result = retrieve_plot_function_details()

        func = result[0]
        self.assertEqual(func["interface"], "def func5(a):")
        self.assertEqual(
            func["dict_args"],
            {
                "a": {"type": "Any", "description": "Some parameter."},
            },
        )

    def test_function_with_no_docstring(self):
        """Test a function with no docstring."""
        content = """
def func6(a: int):
    pass
"""
        with patch(
            "app.backend.visualization.plot_details_extractor.read_code_from_file"
        ) as mock_read:
            mock_read.return_value = content.strip()
            result = retrieve_plot_function_details()

        func = result[0]
        self.assertEqual(func["description"], "")
        self.assertEqual(
            func["dict_args"],
            {
                "a": {"type": "int", "description": "No description"},
            },
        )

    def test_multiple_functions(self):
        """Test parsing multiple functions."""
        content = """
def func7(a: int):
    \"\"\"Args: a: Integer.\"\"\"
    pass

def func8(b: str):
    \"\"\"Args: b: String.\"\"\"
    pass
"""
        with patch(
            "app.backend.visualization.plot_details_extractor.read_code_from_file"
        ) as mock_read:
            mock_read.return_value = content.strip()
            result = retrieve_plot_function_details()

        self.assertEqual(len(result), 2)
        func7 = next(f for f in result if f["name"] == "func7")
        self.assertEqual(func7["interface"], "def func7(a: int):")
        self.assertEqual(
            func7["dict_args"],
            {"a": {"type": "int", "description": "No description"}},
        )

        func8 = next(f for f in result if f["name"] == "func8")
        self.assertEqual(func8["interface"], "def func8(b: str):")
        self.assertEqual(
            func8["dict_args"],
            {"b": {"type": "str", "description": "No description"}},
        )


if __name__ == "__main__":
    unittest.main()
