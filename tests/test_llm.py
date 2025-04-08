"""
End-to-end validation of LLM-powered analysis and visualization pipelines.

This module tests core natural language processing capabilities including:
- SQL generation from natural language questions
- Schema description synthesis
- Visualization configuration parsing
- LLM response format handling

Validates both live LLM interactions and mocked response parsing through:
- Query structure verification
- Error condition simulations
- Cross-component integration
- Data type and format compliance
"""

# Python
import unittest
from unittest.mock import patch

# Visualization
from app.backend.visualization.plot_context_selector import (
    build_visualization_context,
)
from app.backend.visualization.plot_instruction_prompt_formatter import (
    format_plot_selection_instructions,
)

# LLM
from app.backend.llm_engine import (
    get_llm,
    generate_sql,
    generate_describe,
    create_chart_dictionary,
    generate_clause_explanation_response,
)


class TestGenerateSQLLive(unittest.TestCase):
    """
    Validation suite for SQL query generation using live LLM.

    Tests verify:
    - Proper SQL syntax scaffolding (SELECT statements, semicolon termination)
    - Schema context integration
    - LLM instance lifecycle management
    - Basic query validity checks

    Uses simplified schema structures to isolate query generation logic.
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


class TestGenerateDescribe(unittest.TestCase):
    """
    Test suite for natural language schema description generation.

    Validates:
    - Descriptive text synthesis from table structures
    - Empty schema handling and error propagation
    - Output content validation (non-SQL, non-empty responses)
    - Data type and comment incorporation

    Ensures descriptions maintain analytical utility without exposing
    raw database implementation details.
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

    def test_generate_describe_negative_empty_schema(self):
        # When schema is empty, the function should raise a ValueError.
        dummy_schema = ""
        dummy_question = "Describe the users table."

        with self.assertRaises(ValueError) as context:
            generate_describe(dummy_schema, dummy_question)

        self.assertIn("Database schema is empty", str(context.exception))


class TestChartDictionaryResponses(unittest.TestCase):
    """
    Validation of visualization configuration parsing.

    Tests handle:
    - JSON code block extraction from LLM responses
    - Python dictionary syntax adaptation
    - Malformed response error handling
    - Schema/plot compatibility enforcement
    - Cross-component context formatting (data <> visualization)

    Includes both unit tests with mocked LLM responses and
    integration tests with live model interactions (sparingly executed).
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
                    "text": '{"plot_type": "pie", "arguments: {"values": "count"}}'  # Missing quote
                }
            ]
        }
        mock_create.return_value = mock_response

        with self.assertRaises(ValueError) as cm:
            create_chart_dictionary("dummy_prompt")

        self.assertIn(
            "Failed to generate a valid chart configuration", str(cm.exception)
        )

    @patch("app.backend.llm_engine.LLM.create_completion")
    def test_response_not_a_dict(self, mock_create):

        mock_response = {
            "choices": [
                {"text": '["plot_type", "arguments"]'}  # Returns list instead of dict
            ]
        }
        mock_create.return_value = mock_response

        with self.assertRaises(ValueError) as cm:
            create_chart_dictionary("dummy_prompt")

        self.assertIn(
            "Failed to generate a valid chart configuration", str(cm.exception)
        )

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

        try:
            result = create_chart_dictionary(prompt)
        except ValueError as e:

            if "Failed to generate a valid chart configuration" in str(e):
                self.fail(f"LLM returned incomplete response: {str(e)}")

            else:
                raise

        self.assertIsInstance(result, dict)

        # Validate required keys in the result
        self.assertIn("plot_type", result)
        self.assertIn("arguments", result)

        # Optionally, validate specific plot types or arguments based on the prompt
        if result["plot_type"] == "plot_bar":
            self.assertIn("category_column", result["arguments"])
            self.assertIn("value_column", result["arguments"])


class TestGenerateClauseExplanationResponse(unittest.TestCase):
    """
    Test suite for LLM-powered SQL clause explanation generation.

    Validates:
    - Correct prompt construction from clause/SQL components
    - Input validation for empty clause or SQL query
    - Proper handling of LLM responses
    - Error propagation for invalid inputs
    """

    @classmethod
    def setUpClass(cls):
        """Initialize LLM instance for all tests."""
        get_llm()

    @patch("app.backend.llm_engine.LLM.create_completion")
    def test_valid_clause_explanation(self, mock_llm):
        """Test successful explanation generation with valid inputs."""

        # Configure mock
        mock_response = {"choices": [{"text": "Filters users older than 30"}]}
        mock_llm.return_value = mock_response

        # Test inputs
        clause = "WHERE age > 30"
        full_sql = "SELECT name FROM users WHERE age > 30;"

        # Generate explanation
        result = generate_clause_explanation_response(clause, full_sql)

        # Validate prompt construction
        expected_prompt = f"""Given this SQL query:
{full_sql}
Explain this specific part of the query: 
'{clause}'
Keep the explanation concise (1-2 sentences) and focus on its role in the overall query. Use simple language."""
        mock_llm.assert_called_once_with(prompt=expected_prompt, temperature=0.4)

        # Validate response handling
        self.assertIsInstance(result, str)
        self.assertGreater(len(result.strip()), 0)
        self.assertNotIn("SELECT", result.upper())

    def test_empty_clause_validation(self):
        """Test empty clause raises descriptive error."""

        with self.assertRaises(ValueError) as context:
            generate_clause_explanation_response("", "SELECT * FROM users")

        self.assertIn("Clause cannot be empty".lower(), str(context.exception).lower())
        self.assertIn(
            "provide meaningful SQL segment".lower(), str(context.exception).lower()
        )

    def test_empty_sql_validation(self):
        """Test empty SQL query raises context-aware error."""

        with self.assertRaises(ValueError) as context:
            generate_clause_explanation_response("SELECT *", "")

        self.assertIn(
            "full sql cannot be empty non-empty string".lower(),
            str(context.exception).lower(),
        )
        self.assertIn("Provide full context".lower(), str(context.exception).lower())

    @patch("app.backend.llm_engine.LLM.create_completion")
    def test_response_format_handling(self, mock_llm):
        """Test handling of various LLM response formats."""

        # Test markdown stripping
        mock_llm.return_value = {
            "choices": [{"text": "**Explanation**: This does something"}]
        }

        result = generate_clause_explanation_response(
            "FROM table", "SELECT * FROM table"
        )
        self.assertNotIn("**Explanation**", result)

        # Test code block handling
        mock_llm.return_value = {
            "choices": [
                {"text": "```\nThis is a code block\n``` And some explanations"}
            ]
        }

        result = generate_clause_explanation_response(
            "JOIN users", "SELECT * FROM orders JOIN users"
        )
        self.assertNotIn("```", result)

    @patch("app.backend.llm_engine.LLM.create_completion")
    def test_long_response_truncation(self, mock_llm):
        """Test excessive response length handling."""

        mock_llm.return_value = {"choices": [{"text": "1234567890" * 151}]}

        result = generate_clause_explanation_response(
            "LIMIT 10", "SELECT * FROM logs LIMIT 10"
        )
        self.assertEquals(len(result), 1500)


if __name__ == "__main__":
    unittest.main()
