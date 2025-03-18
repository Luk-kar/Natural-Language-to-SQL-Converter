"""
Tests for extracting metadata from plot functions, including function signatures, parameter types, and docstrings.

This module combines tests for:
- Dynamic file-based extraction of plot function metadata.
- Parsing of function signatures with various parameter patterns.
- Extraction and formatting of argument descriptions from docstrings.
- Cleanup of temporary test artifacts.

Tests ensure that the system correctly identifies required and optional parameters, handles type hints, and processes
multi-function files with consistent formatting.
"""

# Python
import unittest
from unittest.mock import patch
import os
import tempfile

# Visualization
from app.backend.visualization.plot_details_extractor import (
    retrieve_plot_function_details,
)


class TestPlotMetadataExtractor(unittest.TestCase):
    """
    Test suite for validating plot function metadata extraction from Python files.

    This class tests the temporary file-based extraction process with:
    - Dynamic file content generation
    - Signature parsing with various parameter patterns
    - Docstring processing and argument description extraction
    - Cleanup of temporary test artifacts
    """

    def setUp(self):
        """
        Set up a temporary file for testing the plot functions extraction.
        """

        self.temp_file = tempfile.NamedTemporaryFile(
            mode="w+", delete=False, suffix=".py"
        )
        self.temp_file_name = self.temp_file.name

        self.patcher = patch(
            "app.backend.visualization.plot_details_extractor.PLOTS_PATH",
            self.temp_file_name,
        )
        self.patcher.start()

    def tearDown(self):
        # Stop patching and clean up
        self.patcher.stop()
        self.temp_file.close()
        os.unlink(self.temp_file_name)

    def write_to_temp_file(self, content):
        """Helper to write content to the temporary file."""

        with open(self.temp_file_name, "w", encoding="utf-8") as f:
            f.write(content.strip())

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
        self.write_to_temp_file(content)
        result = retrieve_plot_function_details()

        self.assertEqual(len(result), 1)
        func = result[0]
        self.assertEqual(func["name"], "func1")
        self.assertEqual(func["interface"], "def func1(a: int, b: str):")
        self.assertIn("a: Integer parameter.", func["description"])
        self.assertIn("b: String parameter.", func["description"])
        self.assertIn("a", func["dict_args"])
        self.assertEqual(
            func["dict_args"]["a"], {"type": "int", "description": "Integer parameter."}
        )
        self.assertIn("b", func["dict_args"])
        self.assertEqual(
            func["dict_args"]["b"],
            {"type": "str", "description": "String parameter."},
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
        self.write_to_temp_file(content)
        result = retrieve_plot_function_details()

        self.assertEqual(len(result), 1)
        func = result[0]
        self.assertEqual(func["interface"], "def func2(a: int):")
        self.assertIn("a: Integer parameter.", func["description"])
        self.assertNotIn("b: String parameter.", func["description"])

        self.assertIn("a", func["dict_args"])
        self.assertEqual(
            func["dict_args"]["a"], {"type": "int", "description": "Integer parameter."}
        )
        self
        self.assertNotIn("b", func["dict_args"])

    def test_function_with_no_params(self):
        """Test a function with no parameters."""
        content = """
def func3():
    \"\"\"No parameters here.\"\"\"
    pass
"""
        self.write_to_temp_file(content)
        result = retrieve_plot_function_details()

        self.assertEqual(len(result), 1)
        func = result[0]
        self.assertEqual(func["interface"], "def func3():")
        self.assertNotIn("Args:", func["description"])
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
        self.write_to_temp_file(content)
        result = retrieve_plot_function_details()

        func = result[0]
        self.assertIn("Args:", func["description"])
        self.assertIn("a: Integer parameter.", func["description"])
        self.assertFalse(
            any(
                keyword in func["description"].lower()
                for keyword in ["returns:", "return:"]
            )
        )
        self.assertNotIn("int: Result.", func["description"])

    def test_parameter_without_type_hint(self):
        """Test a parameter without a type hint."""
        content = """
def func5(a):
    \"\"\"Args:
        a: Some parameter.
    \"\"\"
    pass
"""
        self.write_to_temp_file(content)
        result = retrieve_plot_function_details()

        func = result[0]
        self.assertEqual(func["interface"], "def func5(a):")
        self.assertIn("a: Some parameter.", func["description"])
        self.assertIn("a", func["dict_args"])
        self.assertEqual(
            func["dict_args"]["a"], {"description": "Some parameter.", "type": "Any"}
        )

    def test_function_with_no_docstring(self):
        """Test a function with no docstring."""
        content = """
def func6(a: int):
    pass
"""
        self.write_to_temp_file(content)
        result = retrieve_plot_function_details()

        func = result[0]
        self.assertEqual(func["description"], "")
        self.assertIn("a", func["dict_args"])
        self.assertEqual(
            func["dict_args"]["a"], {"type": "int", "description": "No description"}
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
        self.write_to_temp_file(content)
        result = retrieve_plot_function_details()

        self.assertEqual(len(result), 2)
        func7 = next(f for f in result if f["name"] == "func7")
        self.assertEqual(func7["interface"], "def func7(a: int):")
        func8 = next(f for f in result if f["name"] == "func8")
        self.assertEqual(func8["interface"], "def func8(b: str):")
