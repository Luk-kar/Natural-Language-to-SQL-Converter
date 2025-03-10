# Python
import unittest
from unittest.mock import patch

# Main Flask app
from app.main import flask_app


class TestIndexEndpoint(unittest.TestCase):
    def setUp(self):
        # Set up the Flask test client
        self.app = flask_app.test_client()
        self.app.testing = True

    @patch("app.backend.routes.execute_query")
    @patch("app.backend.llm_engine.LLM")
    @patch("app.backend.routes.get_schema")
    def test_post_sql_generation(self, mock_get_schema, mock_llm, mock_execute_query):
        """
        Test a POST request for SQL generation:
        - get_schema returns a dummy schema.
        - The LLM's create_completion method returns a known SQL query.
        - execute_query returns a result with columns and data rows.
        - The rendered output should include the SQL query and a table with rows.
        """
        # Setup dummy schema
        dummy_schema = "dummy schema text"
        mock_get_schema.return_value = dummy_schema

        # Setup dummy LLM response for SQL generation.
        dummy_sql = "SELECT * FROM users;"
        dummy_llm_response = {"choices": [{"text": dummy_sql}]}
        # Set create_completion on the dummy llm.
        mock_llm.create_completion.return_value = dummy_llm_response

        # Setup dummy execution result with columns and rows.
        dummy_execution = {
            "columns": ["id", "name"],
            "data": [(1, "Alice"), (2, "Bob")],
        }
        mock_execute_query.return_value = dummy_execution

        # Issue a POST request with a question that triggers SQL generation.
        response = self.app.post("/", data={"question": "Get all users"})
        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)

        # Verify that the generated SQL is included.
        self.assertIn(dummy_sql, html)

        # Verify that the table with query results appears.
        self.assertIn('<table border="1">', html)
        self.assertIn("<th>id</th>", html)
        self.assertIn("<th>name</th>", html)
        self.assertIn("<td>1</td>", html)
        self.assertIn("<td>Alice</td>", html)
        self.assertIn("<td>2</td>", html)
        self.assertIn("<td>Bob</td>", html)

    @patch("app.backend.routes.get_schema")
    @patch("app.backend.llm_engine.LLM")
    def test_post_describe(self, mock_llm, mock_get_schema):
        """
        Test a POST request for describing the database schema.
        - A dummy schema and question (starting with "DESCRIBE:") are provided.
        - The LLM's create_completion method is patched to return a known description.
        - The rendered output should contain the generated description.
        """
        dummy_schema = "dummy schema text"
        mock_get_schema.return_value = dummy_schema

        dummy_response = {"choices": [{"text": "This table contains user records."}]}
        mock_llm.create_completion.return_value = dummy_response

        # Create POST request with a question that starts with "DESCRIBE:".
        response = self.app.post("/", data={"question": "DESCRIBE: users table"})
        self.assertEqual(response.status_code, 200)
        data = response.get_data(as_text=True)

        # Verify that the dummy description appears in the rendered output.
        self.assertIn("This table contains user records.", data)

    @patch("app.backend.routes.get_schema", side_effect=Exception("Test error"))
    def test_post_error_handling(self, mock_get_schema):
        """
        Test error handling.
        - The get_schema function is patched to raise an Exception.
        - The rendered output should contain the error message.
        """
        response = self.app.post("/", data={"question": "Get all users"})
        self.assertEqual(response.status_code, 200)
        data = response.get_data(as_text=True)
        self.assertIn("Test error", data)


if __name__ == "__main__":
    unittest.main()
