# Python
import unittest
from unittest.mock import patch, MagicMock

# Third-party
from app.backend.routes import flask_app
from app.backend.llm_engine import generate_describe


class TestSQLExplanationEndpoints(unittest.TestCase):
    def setUp(self):
        self.client = flask_app.test_client()
        flask_app.config["TESTING"] = True

    @patch("app.backend.routes.generate_clause_explanation_response")
    def test_generate_clause_explanation_endpoint(self, mock_generate):
        # Mock the response from the explanation generator
        mock_generate.return_value = {
            "choices": [{"text": "This selects columns from users table"}]
        }

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


class TestDescriptionGenerationEdgeCases(unittest.TestCase):
    @patch("app.backend.llm_engine.LLM")
    def test_empty_schema_handling(self, mock_llm):
        with self.assertRaises(ValueError):
            generate_describe("", "test question")

    @patch("app.backend.llm_engine.LLM")
    def test_special_characters_handling(self, mock_llm):
        mock_response = MagicMock()
        mock_response.choices = [MagicMock(text="Properly escaped response")]
        mock_llm.create_completion.return_value = mock_response

        result = generate_describe("Schema with 'special' characters", "Question?")
        self.assertEqual(result, "Properly escaped response")


if __name__ == "__main__":
    unittest.main()
