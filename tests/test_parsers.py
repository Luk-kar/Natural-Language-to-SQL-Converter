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
    Test suite for validating SQL query extraction from natural language text.

    This class tests both successful extraction of complete SELECT statements
    and proper error handling when no valid SQL is detected.
    """

    def test_extract_sql_positive(self):
        """
        Positive test: valid SQL query embedded in some text
        """

        input_text = "Here is the query:  SELECT * FROM my_table; and some extra text."
        expected_output = "SELECT * FROM my_table;"
        result = extract_sql(input_text)
        self.assertEqual(result, expected_output)

    def test_extract_sql_negative(self):
        """
        Negative test: no SELECT statement present in the input text
        """

        input_text = "This text does not contain a valid SQL query."

        with self.assertRaises(ValueError) as context:
            extract_sql(input_text)

        self.assertIn(
            "Generated SQL does not contain a valid sql SELECT statement:",
            str(context.exception),
        )


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
