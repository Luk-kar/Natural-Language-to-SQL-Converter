import unittest
from unittest.mock import patch, MagicMock
from psycopg2 import ProgrammingError
import psycopg2

from backend.app import (
    get_schema,
    execute_query,
    DB_CONFIG,
)

# Dummy data for testing get_schema
DUMMY_SCHEMA_ROWS = [
    ("public", "table1", "id", "integer", "Primary key"),
    ("public", "table1", "name", "text", "User name"),
    ("public", "table2", "date", "date", "Creation date"),
]


class DummyCursor:
    def __init__(self, rows):
        self.rows = rows

    def execute(self, query):
        pass

    def fetchall(self):
        return self.rows

    def close(self):
        pass


class DummyConnection:
    def __init__(self, rows):
        self.rows = rows

    def cursor(self):
        return DummyCursor(self.rows)

    def close(self):
        pass


def dummy_connect(*args, **kwargs):
    """Mocked function to simulate a successful PostgreSQL connection."""
    return DummyConnection(DUMMY_SCHEMA_ROWS)


class SchemaRetrievalTests(unittest.TestCase):

    @patch("psycopg2.connect", side_effect=dummy_connect)
    def test_get_schema_success(self, mock_connect):

        result = get_schema()

        # Ensure the result is not empty and is a string.
        self.assertIsInstance(result, str)
        self.assertGreater(len(result.strip()), 0, "Schema output should not be empty")

        # Check that the result contains basic field names (if they appear in the prompt or dummy output).
        # Note: Since the actual output is formatted as a Markdown table, we should check for the expected text.
        expected_table_header = "Table public.table1:"
        expected_md_header = "|Column|Data Type|Comment|"
        self.assertIn(expected_table_header, result)
        self.assertIn(expected_md_header, result)

        # Check that each required field (based on dummy data) is present in the result.
        self.assertIn("|id|(integer)|Primary key|", result)
        self.assertIn("|name|(text)|User name|", result)
        self.assertIn("Table public.table2:", result)
        self.assertIn("|date|(date)|Creation date|", result)

    @patch(
        "psycopg2.connect", side_effect=psycopg2.OperationalError("Connection failed")
    )
    @patch("logging.error")  # Suppresses logging.error messages during the test
    def test_get_schema_no_connection(self, mock_connect, mock_log_error):

        # Ensure that get_schema raises an exception when connection fails.
        with self.assertRaises(psycopg2.OperationalError) as context:
            get_schema()

        # Optionally, check that the exception message contains expected text.
        self.assertIn("Connection failed", str(context.exception))


class TestExecuteQuery(unittest.TestCase):

    @patch("psycopg2.connect")
    def test_execute_query_success(self, mock_connect):
        """Test successful execution of a SELECT query"""
        # Setup mock database objects
        mock_cursor = MagicMock()
        mock_cursor.description = [("id",), ("name",)]  # Simulate columns
        mock_cursor.fetchall.return_value = [(1, "Alice"), (2, "Bob")]

        mock_conn = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn

        # Execute test query
        test_sql = "SELECT id, name FROM table1"
        result = execute_query(test_sql)

        # Verify results
        self.assertEqual(
            result, {"columns": ["id", "name"], "data": [(1, "Alice"), (2, "Bob")]}
        )
        mock_connect.assert_called_once_with(**DB_CONFIG)
        mock_cursor.execute.assert_called_once_with(test_sql)
        mock_conn.close.assert_called_once()

    @patch("psycopg2.connect")
    def test_execute_query_non_select(self, mock_connect):
        """Test non-SELECT query raises error"""
        mock_cursor = MagicMock()
        mock_cursor.description = None  # Non-SELECT queries have no description

        mock_conn = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn

        # Execute test query
        test_sql = "INSERT INTO table1 VALUES (1, 'Alice')"
        result = execute_query(test_sql)

        # Verify error handling
        self.assertIn("error", result)
        self.assertIn("Only SELECT queries are supported", result["error"])
        mock_conn.close.assert_called_once()

    @patch("psycopg2.connect")
    def test_execute_query_invalid_sql(self, mock_connect):
        """Test invalid SQL syntax handling"""
        mock_cursor = MagicMock()
        mock_cursor.execute.side_effect = ProgrammingError("Syntax error")

        mock_conn = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn

        # Execute test query
        test_sql = "SELECT FROM invalid_table"
        result = execute_query(test_sql)

        # Verify error handling
        self.assertIn("error", result)
        self.assertIn("Syntax error", result["error"])
        mock_conn.close.assert_called_once()

    @patch("psycopg2.connect")
    def test_execute_query_connection_error(self, mock_connect):
        """Test database connection failure"""
        mock_connect.side_effect = psycopg2.OperationalError("Connection refused")

        # Execute test query
        test_sql = "SELECT * FROM secret_table"
        result = execute_query(test_sql)

        # Verify error handling
        self.assertIn("error", result)
        self.assertIn("Connection refused", result["error"])


if __name__ == "__main__":
    unittest.main()
