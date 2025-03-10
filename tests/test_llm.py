# Python
import unittest

# LLM
from backend.llm_engine import get_llm, generate_sql, generate_describe


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


if __name__ == "__main__":
    unittest.main()
