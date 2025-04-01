import unittest
from unittest.mock import patch
from flask import Flask
from app.backend.routes import flask_app


class SQLDisplayTests(unittest.TestCase):
    """
    Test suite for SQL query display functionality including:
    - Query expansion/collapse behavior
    - Clause highlighting and tooltips
    - Interactive element states
    - Error handling in query display components

    Validates through:
    - Template rendering assertions
    - Session data validation
    - HTML element existence checks
    - CSS class assertions
    - JavaScript interaction simulations
    """

    def setUp(self):
        self.app = flask_app.test_client()
        self.app.testing = True

    @patch("app.backend.routes.execute_query")
    @patch("app.backend.llm_engine.LLM")
    @patch("app.backend.routes.get_schema")
    def test_expand_long_query(self, mock_get_schema, mock_llm, mock_execute_query):
        """Verify expansion workflow for queries exceeding 200 characters"""
        # Setup long query
        long_query = "SELECT " + "a" * 300
        mock_get_schema.return_value = "dummy schema"
        mock_llm.create_completion.return_value = {"choices": [{"text": long_query}]}
        mock_execute_query.return_value = {"columns": ["a"], "data": [[1]]}

        # Initial request
        response = self.app.post("/", data={"question": "Test long query"})
        html = response.get_data(as_text=True)

        # Verify initial state
        self.assertIn("...", html)  # Truncation indicator
        self.assertIn("Show full query", html)
        self.assertNotIn("sql-info-icon", html)

        # Simulate expansion click by modifying session data
        with self.app.session_transaction() as sess:
            sess["result"]["sql"] = long_query  # Set full SQL
            sess["result"]["execution"] = {"columns": ["a"], "data": [[1]]}

        # Get updated response
        expanded_response = self.app.get("/")
        expanded_html = expanded_response.get_data(as_text=True)

        # Verify expanded state
        self.assertNotIn("...", expanded_html)
        self.assertNotIn("Show full query", expanded_html)
        self.assertIn("sql-info-icon", expanded_html)

    @patch("app.backend.routes.execute_query")
    @patch("app.backend.llm_engine.LLM")
    @patch("app.backend.routes.get_schema")
    def test_short_query_display(self, mock_get_schema, mock_llm, mock_execute_query):
        """Verify non-expanded state for queries under 200 characters"""
        short_query = "SELECT * FROM users"
        mock_get_schema.return_value = "dummy schema"
        mock_llm.create_completion.return_value = {"choices": [{"text": short_query}]}
        mock_execute_query.return_value = {"columns": ["id"], "data": [[1]]}

        response = self.app.post("/", data={"question": "Test short query"})
        html = response.get_data(as_text=True)

        # Verify non-expanded state
        self.assertNotIn("...", html)
        self.assertNotIn("Show full query", html)
        self.assertIn("sql-info-icon", html)
        self.assertIn(short_query, html)

    @patch("app.backend.routes.execute_query")
    @patch("app.backend.llm_engine.LLM")
    @patch("app.backend.routes.get_schema")
    def test_clause_tooltips_expanded(
        self, mock_get_schema, mock_llm, mock_execute_query
    ):
        """Verify tooltip generation in expanded query state"""
        test_query = "SELECT id, name FROM users WHERE active = true"
        mock_get_schema.return_value = "dummy schema"
        mock_llm.create_completion.return_value = {"choices": [{"text": test_query}]}
        mock_execute_query.return_value = {"columns": ["id"], "data": [[1]]}

        # Set expanded state in session
        with self.app.session_transaction() as sess:
            sess["result"] = {
                "sql": test_query,
                "execution": {"columns": ["id"], "data": [[1]]},
            }

        response = self.app.get("/")
        html = response.get_data(as_text=True)

        # Verify clause markup
        self.assertIn('class="sql-clause"', html)
        self.assertIn('title="placeholder"', html)
        self.assertIn('data-clause-type="SELECT"', html)
        self.assertIn('data-clause-type="FROM"', html)
        self.assertIn('data-clause-type="WHERE"', html)

    @patch("app.backend.routes.execute_query")
    @patch("app.backend.llm_engine.LLM")
    @patch("app.backend.routes.get_schema")
    def test_clause_tooltips_non_expanded(
        self, mock_get_schema, mock_llm, mock_execute_query
    ):
        """Verify tooltip generation in non-expanded state"""
        test_query = "SELECT * FROM products"  # Short query
        mock_get_schema.return_value = "dummy schema"
        mock_llm.create_completion.return_value = {"choices": [{"text": test_query}]}
        mock_execute_query.return_value = {"columns": ["id"], "data": [[1]]}

        response = self.app.post("/", data={"question": "Test tooltips"})
        html = response.get_data(as_text=True)

        # Verify clause markup
        self.assertIn('class="sql-clause"', html)
        self.assertIn('title="placeholder"', html)
        self.assertIn('data-clause-type="SELECT"', html)
        self.assertIn('data-clause-type="FROM"', html)

    @patch("app.backend.routes.execute_query")
    @patch("app.backend.llm_engine.LLM")
    @patch("app.backend.routes.get_schema")
    def test_query_display_errors(self, mock_get_schema, mock_llm, mock_execute_query):
        """Verify error states in query display"""
        # Setup error response
        mock_get_schema.return_value = "dummy schema"
        mock_llm.create_completion.return_value = {
            "choices": [{"text": "INVALID QUERY"}]
        }
        mock_execute_query.return_value = {"error": "Syntax error"}

        response = self.app.post("/", data={"question": "Test error"})
        html = response.get_data(as_text=True)

        # Verify error display
        self.assertIn("error_execution.html", html)
        self.assertNotIn("sql-clause", html)
        self.assertNotIn("sql-info-icon", html)
