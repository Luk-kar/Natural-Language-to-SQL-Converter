# Python
import unittest

# Third-party
from app.backend.routes import flask_app


class TestSQLExplanationEndpoints(unittest.TestCase):
    def setUp(self):
        self.client = flask_app.test_client()
        flask_app.config["TESTING"] = True

    @patch("app.backend.routes.generate_clause_explanation_response")
    def test_generate_clause_explanation_endpoint(self, mock_generate):
        # Mock the response from the explanation generator
        mock_generate.return_value = "This selects columns from users table"

        # Test data
        test_data = {
            "clause": "SELECT name, age",
            "fullSql": "SELECT name, age FROM users",
            "clauseId": "123",
        }

        # Make request
        response = self.client.post("/generate_clause_explanation", json=test_data)

        # Verify response
        self.assertEqual(response.status_code, 200)
        response_data = response.get_json()

        self.assertEqual(
            response_data,
            {"clauseId": "123", "explanation": "This selects columns from users table"},
        )

    def test_error_handling(self):
        # Test missing required fields
        bad_data = {"clause": "SELECT test"}
        response = self.client.post("/generate_clause_explanation", json=bad_data)
        self.assertEqual(response.status_code, 400)


if __name__ == "__main__":
    unittest.main()
