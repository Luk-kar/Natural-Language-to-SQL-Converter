# Python
import unittest
from unittest.mock import patch, MagicMock
import json
import ast

# Visualization
from app.backend.visualization.plot_context_selector import (
    format_plot_selection_instructions,
    NO_COMPATIBLE_PLOTS_MESSAGE,
    build_visualization_context,
)

# LLM
from app.backend.llm_engine import (
    get_llm,
    generate_sql,
    generate_describe,
    create_chart_dictionary,
)


class TestGenerateSQLLive(unittest.TestCase):
    """
    Test the generate_sql function with a live LLM instance.
    """

    @classmethod
    def setUpClass(cls):
        """Ensure the LLM instance is initialized before running tests."""
        get_llm()

    def test_generate_sql_live(self):
        # Provide a simple schema and question that the LLM should be able to handle.
        dummy_schema = (
            "Table public.users:\n"
            "|Column|Data Type|Comment|\n"
            "|------|---------|-------|\n"
            "|id|(integer)|User ID|"
        )
        dummy_question = "Retrieve all user records."

        sql = generate_sql(dummy_schema, dummy_question)

        # Check that the returned SQL string starts with SELECT and ends with a semicolon.
        self.assertIsInstance(sql, str)
        self.assertTrue(
            sql.strip().startswith("SELECT"), "SQL should start with SELECT"
        )
        self.assertTrue(sql.strip().endswith(";"), "SQL should end with a semicolon")

        # Optionally, print the generated SQL for manual inspection.
        print("Generated SQL:", sql)


class TestGenerateDescribe(unittest.TestCase):
    """
    Test the generate_describe function with a live LLM instance.
    """

    @classmethod
    def setUpClass(cls):
        """Ensure the LLM instance is initialized before running tests."""
        get_llm()

    def test_generate_describe_positive(self):
        # Provide a valid schema and a question.
        dummy_schema = (
            "Table public.users:\n"
            "|Column|Data Type|Comment|\n"
            "|------|---------|-------|\n"
            "|id|(integer)|User ID|\n"
            "|name|(text)|User name|"
        )
        dummy_question = "Describe the users table."

        description = generate_describe(dummy_schema, dummy_question)

        # Assert that a non-empty string is returned.
        self.assertIsInstance(description, str)
        self.assertGreater(
            len(description.strip()), 0, "The description should not be empty"
        )

        # Optionally, check that it does not include unwanted formatting or SQL code.
        self.assertNotIn(
            "SELECT", description.upper(), "Description should not include SQL code"
        )
        print("Generated Description:", description)

    def test_generate_describe_negative_empty_schema(self):
        # When schema is empty, the function should raise a ValueError.
        dummy_schema = ""
        dummy_question = "Describe the users table."

        with self.assertRaises(ValueError) as context:
            generate_describe(dummy_schema, dummy_question)

        self.assertIn("Database schema is empty", str(context.exception))


class TestChartDictionaryResponses(unittest.TestCase):
    """
    Test the create_chart_dictionary function with various LLM responses.
    """

    @classmethod
    def setUpClass(cls):

        get_llm()

        # Create a valid plot_context for testing valid context generation
        cls.data_context = {
            "columns": {"category": "str", "count": "int"},
            "sample_3_values": {"category": ["A", "B", "C"], "count": [10, 20, 30]},
            "row_count": 3,
        }
        cls.compatible_plots = [
            {
                "name": "plot_bar",
                "interface": "plot_bar(data, category_column, value_column)",
                "description": "A bar plot",
                "dict_args": {
                    "category_column": {
                        "type": "str",
                        "description": "Category column",
                    },
                    "value_column": {"type": "int", "description": "Value column"},
                },
            }
        ]
        cls.plot_context = {
            "compatible_plots": cls.compatible_plots,
            "data_context": cls.data_context,
        }
        cls.valid_prompt = format_plot_selection_instructions(cls.plot_context)

    @patch("app.backend.llm_engine.LLM.create_completion")
    def test_valid_code_block_response(self, mock_create):
        """Test parsing a valid JSON code block response."""

        mock_response = {
            "choices": [
                {
                    "text": '```json\n{"plot_type": "heatmap", "arguments": {"data": "df"}}\n```'
                }
            ]
        }

        mock_create.return_value = mock_response

        result = create_chart_dictionary("dummy_prompt")
        expected = {"plot_type": "heatmap", "arguments": {"data": "df"}}

        self.assertEqual(result, expected)

    @patch("app.backend.llm_engine.LLM.create_completion")
    def test_valid_response_without_code_block(self, mock_create):
        """Test parsing a valid JSON response without a code block."""

        mock_response = {
            "choices": [
                {
                    "text": '{"plot_type": "scatter", "arguments": {"x": "col1", "y": "col2"}}'
                }
            ]
        }

        mock_create.return_value = mock_response

        result = create_chart_dictionary("dummy_prompt")
        expected = {"plot_type": "scatter", "arguments": {"x": "col1", "y": "col2"}}

        self.assertEqual(result, expected)

    @patch("app.backend.llm_engine.LLM.create_completion")
    def test_valid_python_dict_response(self, mock_create):
        """Test parsing a Python-style dictionary with single quotes."""

        mock_response = {
            "choices": [
                {
                    "text": "{'plot_type': 'treemap', 'arguments': {'group_columns': ['Region']}}"
                }
            ]
        }
        mock_create.return_value = mock_response

        result = create_chart_dictionary("dummy_prompt")
        expected = {"plot_type": "treemap", "arguments": {"group_columns": ["Region"]}}

        self.assertEqual(result, expected)

    @patch("app.backend.llm_engine.LLM.create_completion")
    def test_invalid_json_response(self, mock_create):
        mock_response = {
            "choices": [
                {
                    "text": '{"plot_type": "pie", "arguments: {"values": "count"}}'
                }  # Invalid JSON
            ]
        }
        mock_create.return_value = mock_response
        result = create_chart_dictionary("dummy_prompt")
        self.assertEqual(result, {"plot": "dummy_plot"})  # Expect fallback

    @patch("app.backend.llm_engine.LLM.create_completion")
    def test_response_not_a_dict(self, mock_create):
        mock_response = {"choices": [{"text": '["plot_type", "arguments"]'}]}
        mock_create.return_value = mock_response
        result = create_chart_dictionary("dummy_prompt")
        self.assertEqual(result, {"plot": "dummy_plot"})  # Expect fallback

    @patch("app.backend.llm_engine.LLM.create_completion")
    def test_with_valid_context_and_response(self, mock_create):
        """Test a valid context (prompt) and LLM response."""

        mock_response = {
            "choices": [
                {
                    "text": '```json\n{\n  "plot_type": "plot_bar",\n  "arguments": {\n    "data": "df",\n    "category_column": "category",\n    "value_column": "count"\n  }\n}\n```'
                }
            ]
        }
        mock_create.return_value = mock_response

        result = create_chart_dictionary(self.valid_prompt)
        expected = {
            "plot_type": "plot_bar",
            "arguments": {
                "data": "df",
                "category_column": "category",
                "value_column": "count",
            },
        }
        self.assertEqual(result, expected)

    def test_real_llm_response(self):
        """
        Test the function with a real LLM response.
        This is an integration test and should be run sparingly.
        """
        result = {
            "execution": {
                "data": [
                    {"category": "A", "count": 10},
                    {"category": "B", "count": 20},
                    {"category": "C", "count": 30},
                ],
                "row_count": 3,
                "columns": {"category": "str", "count": "int"},
                "sample_3_values": {"category": ["A", "B", "C"], "count": [10, 20, 30]},
            }
        }
        plot_context = build_visualization_context(result["execution"])
        prompt = format_plot_selection_instructions(plot_context)

        result = create_chart_dictionary(prompt)

        self.assertIsInstance(result, dict)

        # Validate required keys in the result
        self.assertIn("plot_type", result)
        self.assertIn("arguments", result)

        # Optionally, validate specific plot types or arguments based on the prompt
        if result["plot_type"] == "plot_bar":
            self.assertIn("category_column", result["arguments"])
            self.assertIn("value_column", result["arguments"])


if __name__ == "__main__":
    unittest.main()
