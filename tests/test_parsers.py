# Python
import unittest
import tempfile
import os

# LLM
from app.backend.llm_engine import (
    extract_sql,
)


class TestExtractSQL(unittest.TestCase):
    def test_extract_sql_positive(self):
        # Positive test: valid SQL query embedded in some text
        input_text = "Here is the query:  SELECT * FROM my_table; and some extra text."
        expected_output = "SELECT * FROM my_table;"
        result = extract_sql(input_text)
        self.assertEqual(result, expected_output)

    def test_extract_sql_negative(self):
        # Negative test: no SELECT statement present in the input text
        input_text = "This text does not contain a valid SQL query."
        with self.assertRaises(ValueError) as context:
            extract_sql(input_text)
        self.assertIn(
            "Generated SQL does not contain a SELECT statement.", str(context.exception)
        )


from app.backend.visualization.function_extractor import (
    extract_plot_functions,
    PLOTS_PATH,
)


class TestPlotFunctionsExtractor(unittest.TestCase):
    def setUp(self):
        # Create a temporary file
        self.temp_file = tempfile.NamedTemporaryFile(
            mode="w+", delete=False, suffix=".py"
        )
        self.temp_file_name = self.temp_file.name
        # Backup original PLOTS_PATH and replace with temp file path
        self.original_plots_path = PLOTS_PATH
        globals()[
            "PLOTS_PATH"
        ] = self.temp_file_name  # Adjust based on actual module structure

    def tearDown(self):
        # Cleanup temporary file and restore original PLOTS_PATH
        self.temp_file.close()
        os.unlink(self.temp_file_name)
        globals()["PLOTS_PATH"] = self.original_plots_path

    def write_to_temp_file(self, content):
        """Helper to write content to the temporary file."""
        self.temp_file.seek(0)
        self.temp_file.truncate()
        self.temp_file.write(content.strip())
        self.temp_file.flush()

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
        result = extract_plot_functions()

        self.assertEqual(len(result), 1)
        func = result[0]
        self.assertEqual(func["name"], "func1")
        self.assertEqual(func["interface"], "def func1(a: int, b: str):")
        self.assertIn("a: Integer parameter.", func["description"])
        self.assertIn("b: String parameter.", func["description"])
        self.assertIn('"a": None, # int: Integer parameter.', func["dict_args"])
        self.assertIn('"b": None, # str: String parameter.', func["dict_args"])

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
        result = extract_plot_functions()

        self.assertEqual(len(result), 1)
        func = result[0]
        self.assertEqual(func["interface"], "def func2(a: int):")
        self.assertIn("a: Integer parameter.", func["description"])
        self.assertNotIn("b: String parameter.", func["description"])
        self.assertIn('"a": None, # int: Integer parameter.', func["dict_args"])
        self.assertNotIn("b", func["dict_args"])

    def test_function_with_no_params(self):
        """Test a function with no parameters."""
        content = """
def func3():
    \"\"\"No parameters here.\"\"\"
    pass
"""
        self.write_to_temp_file(content)
        result = extract_plot_functions()

        self.assertEqual(len(result), 1)
        func = result[0]
        self.assertEqual(func["interface"], "def func3():")
        self.assertNotIn("Args:", func["description"])
        self.assertEqual(func["dict_args"].strip(), "{\n}")

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
        result = extract_plot_functions()

        func = result[0]
        self.assertIn("Args:", func["description"])
        self.assertIn("a: Integer parameter.", func["description"])
        self.assertNotIn("Returns:", func["description"])
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
        result = extract_plot_functions()

        func = result[0]
        self.assertEqual(func["interface"], "def func5(a):")
        self.assertIn("a: Some parameter.", func["description"])
        self.assertIn('"a": None, # Any: Some parameter.', func["dict_args"])

    def test_function_with_no_docstring(self):
        """Test a function with no docstring."""
        content = """
def func6(a: int):
    pass
"""
        self.write_to_temp_file(content)
        result = extract_plot_functions()

        func = result[0]
        self.assertEqual(func["description"], "")
        self.assertIn('"a": None, # int: No description', func["dict_args"])

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
        result = extract_plot_functions()

        self.assertEqual(len(result), 2)
        func7 = next(f for f in result if f["name"] == "func7")
        self.assertEqual(func7["interface"], "def func7(a: int):")
        func8 = next(f for f in result if f["name"] == "func8")
        self.assertEqual(func8["interface"], "def func8(b: str):")


if __name__ == "__main__":
    unittest.main()
