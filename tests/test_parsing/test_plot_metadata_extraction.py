"""
Unit tests for parsing plot function metadata.

Visualization Metadata Extraction:
   - Function signature parsing for plot generation
   - Parameter type detection and documentation
   - Docstring processing for API documentation
   - Multi-function module analysis
"""

import unittest
from unittest.mock import patch

from app.backend.visualization.plot_details_extractor import (
    retrieve_plot_function_details,
)


class TestPlotInterfaceParser(unittest.TestCase):
    """
    Test suite for automated API documentation generation from source code.

    Validates:
    - Function signature parsing for required/optional parameters
    - Type hint extraction and fallback handling
    - Docstring section processing (Args/Returns)
    - Multi-function module analysis
    - Default parameter detection and stripping

    Tests cover edge cases including:
    - Missing type hints → 'Any' type fallback
    - Empty docstrings → default descriptions
    - Mixed documentation formats
    - Parameter inheritance patterns
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
