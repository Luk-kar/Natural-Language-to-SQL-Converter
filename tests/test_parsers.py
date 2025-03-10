# Python
import unittest

# LLM
from backend.llm_engine import (
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


if __name__ == "__main__":
    unittest.main()
