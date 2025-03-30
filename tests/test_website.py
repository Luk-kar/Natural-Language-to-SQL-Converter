"""
End-to-end validation of Flask web interface and user interaction flows.

This module tests critical frontend components through:
- Endpoint response validation
- HTML template rendering checks
- Form submission error handling
- Backend service integration mocking
- User-facing error message propagation

Validates complete request/response cycles using Flask's test client while
isolating external dependencies through patching of LLM and database systems.
"""

# Python
import unittest
from unittest.mock import patch

# Main Flask app
from app.app import flask_app
from flask import jsonify


class TestIndexEndpoint(unittest.TestCase):
    """
    Test suite for core index endpoint functionality and error handling.

    Validates:
    - SQL generation workflow from natural language questions
    - Schema description request processing
    - Error handling and user feedback mechanisms
    - HTML template rendering of both results and errors
    - Integration with mocked LLM and database services

    Tests verify proper system behavior through:
    - Response status code validation
    - HTML content assertions
    - Mocked backend service interactions
    - Edge case simulations (exceptions, malformed inputs)
    """

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
        self.assertIn("<table>", html)
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


class TestChartTabAvailability(unittest.TestCase):
    """
    Test chart tab availability based on data validity and plot compatibility.
    Validates both visual presentation and backend flag propagation.
    """

    def setUp(self):
        self.app = flask_app.test_client()
        self.app.testing = True

    @patch("app.backend.routes.execute_query")
    @patch("app.backend.llm_engine.LLM")
    @patch("app.backend.routes.get_schema")
    def test_chart_tab_enabled_on_valid_data_and_plots(
        self, mock_get_schema, mock_llm, mock_execute_query
    ):
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
        self.assertIn('data-tab="chart"', html)
        self.assertIn('class="tab-link " data-tab="chart"', html)
        self.assertIn('class="tab-link active" data-tab="query-results"', html)
        self.assertNotIn('class="tab-link disabled" data-tab="chart"', html)

    @patch("app.backend.routes.execute_query")
    @patch("app.backend.llm_engine.LLM")
    @patch("app.backend.routes.get_schema")
    def test_chart_tab_disabled_when_unavailable(
        self, mock_get_schema, mock_llm, mock_execute_query
    ):
        """
        Test chart tab is disabled when:
        - Data exists but is incompatible for visualization (non-numeric columns)
        - Backend flags chart_available=False
        - Validate visual presentation reflects disabled state
        """
        # Setup dummy schema
        dummy_schema = "dummy schema text"
        mock_get_schema.return_value = dummy_schema

        # Setup dummy LLM response for SQL generation
        dummy_sql = "SELECT name FROM users;"  # Single non-numeric column
        dummy_llm_response = {"choices": [{"text": dummy_sql}]}
        mock_llm.create_completion.return_value = dummy_llm_response

        # Setup dummy execution result with non-plottable data
        dummy_execution = {
            "columns": ["name"],
            "data": [("Alice",), ("Bob",)],  # No numeric data for plotting
        }
        mock_execute_query.return_value = dummy_execution

        # Issue POST request
        response = self.app.post("/", data={"question": "Get non-plottable data"})
        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)

        # Verify SQL appears in output
        self.assertIn(dummy_sql, html)

        # Validate chart tab is disabled
        self.assertIn('data-tab="chart"', html)  # Tab exists
        self.assertIn(
            'class="tab-link disabled" data-tab="chart"', html
        )  # Disabled state

        # Validate correct active tab
        self.assertIn('class="tab-link active" data-tab="query-results"', html)
        self.assertNotIn('class="tab-link active" data-tab="chart"', html)

    @patch("app.backend.routes.execute_query")
    @patch("app.backend.llm_engine.LLM")
    @patch("app.backend.routes.get_schema")
    def test_chart_tab_disabled_on_empty_data(
        self, mock_get_schema, mock_llm, mock_execute_query
    ):
        """
        Test chart tab disabled when query returns empty dataset:
        - Valid columns but no rows
        - Backend should set chart_available=False
        - Frontend should show disabled chart tab
        - Verify empty state UI components
        """
        # Setup dummy schema and LLM
        dummy_schema = "dummy schema text"
        mock_get_schema.return_value = dummy_schema
        dummy_sql = "SELECT * FROM empty_table;"
        mock_llm.create_completion.return_value = {"choices": [{"text": dummy_sql}]}

        # Mock empty dataset response
        mock_execute_query.return_value = {
            "columns": ["id", "name"],
            "data": [],  # Empty data array
        }

        response = self.app.post("/", data={"question": "Get empty dataset"})
        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)

        # Verify empty state components
        self.assertIn("No results found", html)  # Empty state message

        # Verify chart tab state
        self.assertIn('data-tab="chart"', html)  # Tab exists
        self.assertIn('class="tab-link disabled" data-tab="chart"', html)  # Disabled
        self.assertIn(
            'class="tab-link active" data-tab="query-results"', html
        )  # Correct active

    @patch("app.backend.routes.execute_query")
    @patch("app.backend.llm_engine.LLM")
    @patch("app.backend.routes.get_schema")
    def test_chart_tab_disabled_on_execution_error(
        self, mock_get_schema, mock_llm, mock_execute_query
    ):
        """
        Test chart tab disabled when query execution fails:
        - Backend returns error in execution result
        - Verify error message appears
        - Chart tab should be disabled despite valid SQL
        """
        # Setup mocks
        dummy_schema = "dummy schema text"
        mock_get_schema.return_value = dummy_schema
        dummy_sql = "SELECT * FROM invalid_table;"
        mock_llm.create_completion.return_value = {"choices": [{"text": dummy_sql}]}

        # Mock error response
        mock_execute_query.return_value = {
            "error": "Table 'invalid_table' doesn't exist"
        }

        response = self.app.post("/", data={"question": "Get invalid data"})
        html = response.get_data(as_text=True)

        # Verify error state
        self.assertIn("Execution Error", html)

        # Validate chart tab state
        self.assertIn('class="tab-link disabled" data-tab="chart"', html)
        self.assertIn('class="tab-link active" data-tab="query-results"', html)

    def test_generate_plots_endpoint_no_data(self):
        """
        Test /generate_plots endpoint error handling:
        - No session data available
        - Session data exists but no execution results
        - Should return JSON error response
        """
        # Test case 1: No session data
        response = self.app.get("/generate_plots")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json, {"error": "No data available for plotting"})

        # Test case 2: Invalid session data
        with self.app.session_transaction() as sess:
            sess["result"] = {"execution": {"columns": []}}  # Missing data key

        response = self.app.get("/generate_plots")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json, {"error": "No dataset available for plotting"})

    @patch("app.backend.routes.generate_visualization_artifacts")
    def test_generate_plots_endpoint_success(self, mock_generate_plots):
        """
        Test successful plot generation workflow:
        - Valid session data exists
        - Visualization artifacts generated properly
        - Returns Bokeh plot configuration
        """
        # Setup valid session data
        test_data = {
            "execution": {"columns": ["x", "y"], "data": [[1, 10], [2, 20], [3, 30]]}
        }

        # Create application context using the actual Flask app
        with flask_app.app_context():
            # Mock visualization output within app context
            dummy_plot = {"type": "line", "data": {}}
            mock_generate_plots.return_value = jsonify(dummy_plot)

            # Set session data using test client's session transaction
            with self.app.session_transaction() as sess:
                sess["result"] = test_data

        # Make request - test client automatically handles app context
        response = self.app.get("/generate_plots")

        # Verify response
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json, dummy_plot)
        mock_generate_plots.assert_called_once_with(test_data["execution"])


if __name__ == "__main__":
    unittest.main()
