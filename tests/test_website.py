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

        print(response.data)
        print(response.status_code)
        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)

        # Verify that the generated SQL is included.
        self.assertIn(dummy_sql, html)

        # Verify that the table with query results appears.
        self.assertIn('data-tab="chart"', html)
        self.assertIn('class="tab-link " data-tab="chart"', html)
        self.assertIn('class="tab-link active" data-tab="query-results"', html)
        self.assertNotIn('class="tab-link disabled" data-tab="chart"', html)

    # @patch("app.backend.routes.execute_query")
    # @patch(
    #     "app.backend.visualization.plot_artifact_generator.build_visualization_context"
    # )
    # @patch("app.backend.llm_engine.LLM")
    # @patch("app.backend.routes.get_schema")
    # def test_chart_tab_enabled_on_valid_data_and_plots(
    #     self, mock_get_schema, mock_llm, mock_build_context, mock_execute_query
    # ):
    #     """Chart tab should be enabled when valid data exists and plots are possible"""

    #     # Setup valid data response
    #     mock_execute_query.return_value = {
    #         "columns": ["x", "y"],
    #         "data": [[1, 10], [2, 20], [3, 30]],
    #     }

    #     # Mock visualization context with compatible plots
    #     mock_build_context.return_value = {
    #         "compatible_plots": [{"name": "plot_bar"}],
    #         "data_context": {"columns": {"x": "int", "y": "int"}},
    #     }

    #     response = self.app.post("/", data={"question": "Valid data question"})
    #     html = response.get_data(as_text=True)

    #     # Verify chart tab is enabled


#     @patch("app.backend.routes.execute_query")
#     @patch("app.backend.routes.get_schema")
#     def test_chart_tab_disabled_on_no_data(self, mock_get_schema, mock_execute_query):
#         """Chart tab should be disabled when query returns no data"""

#         # Setup empty data response
#         mock_execute_query.return_value = {"columns": ["x", "y"], "data": []}

#         response = self.app.post("/", data={"question": "Empty data question"})
#         html = response.get_data(as_text=True)

#         # Verify chart tab is disabled
#         self.assertIn('data-tab="chart"', html)
#         self.assertIn('class="tab-link disabled" data-tab="chart"', html)

#     @patch("app.backend.routes.execute_query")
#     @patch(
#         "app.backend.visualization.plot_artifact_generator.build_visualization_context"
#     )
#     @patch("app.backend.routes.get_schema")
#     def test_chart_tab_disabled_on_incompatible_plots(
#         self, mock_get_schema, mock_build_context, mock_execute_query
#     ):
#         """Chart tab should be disabled when no compatible plots available"""

#         # Setup valid data but incompatible plots
#         mock_execute_query.return_value = {"columns": ["id"], "data": [[1], [2], [3]]}
#         mock_build_context.return_value = {
#             "compatible_plots": [],
#             "data_context": {"columns": {"id": "int"}},
#         }

#         response = self.app.post("/", data={"question": "Incompatible plot question"})
#         html = response.get_data(as_text=True)

#         # Verify chart tab is disabled
#         self.assertIn('data-tab="chart"', html)
#         self.assertIn('class="tab-link disabled" data-tab="chart"', html)

#     @patch("app.backend.routes.execute_query")
#     @patch("app.backend.routes.get_schema")
#     def test_chart_tab_disabled_on_execution_error(
#         self, mock_get_schema, mock_execute_query
#     ):
#         """Chart tab should be disabled when query execution has error"""

#         # Setup error response
#         mock_execute_query.return_value = {
#             "error": "Invalid column name",
#             "data": [[1], [2], [3]],
#         }

#         response = self.app.post("/", data={"question": "Error question"})
#         html = response.get_data(as_text=True)

#         # Verify chart tab is disabled
#         self.assertIn('data-tab="chart"', html)
#         self.assertIn('class="tab-link disabled" data-tab="chart"', html)

#     def test_generate_plots_endpoint_no_data(self):
#         """Should return error when generating plots without valid data"""

#         with self.app.session_transaction() as sess:
#             sess["result"] = None  # Clear session data

#         response = self.app.get("/generate_plots")

#         self.assertEqual(response.status_code, 200)
#         self.assertIn("No data available", response.get_json()["error"])

#     @patch(
#         "app.backend.visualization.plot_artifact_generator.generate_visualization_artifacts"
#     )
#     def test_generate_plots_endpoint_success(self, mock_generate):
#         """Should return plot JSON when valid data exists"""

#         # Setup mock plot generation
#         with flask_app.app_context():
#             mock_generate.return_value = jsonify({"chart": "dummy_plot_data"})

#         with self.app.session_transaction() as sess:
#             sess["result"] = {
#                 "execution": {"columns": ["x", "y"], "data": [[1, 10], [2, 20]]}
#             }

#         response = self.app.get("/generate_plots")

#         self.assertEqual(response.status_code, 200)
#         self.assertIn("chart", response.get_json())


if __name__ == "__main__":
    unittest.main()
