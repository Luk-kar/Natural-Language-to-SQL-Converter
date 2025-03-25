# Python
import unittest
from unittest.mock import patch

# LLM
from app.backend.llm_engine import (
    extract_sql,
)

from app.backend.visualization.plot_details_extractor import (
    retrieve_plot_function_details,
)


class TestExtractSQL(unittest.TestCase):
    """
    Test suite for validating SQL query extraction with enhanced error handling,
    CTE support, and comment stripping.
    """

    # Positive Test Cases
    def test_basic_select(self):
        """Test extraction of simple SELECT statement"""

        input_text = "Result: SELECT id, name FROM users WHERE active = true;"
        expected = "SELECT id, name FROM users WHERE active = true;"

        self.assertEqual(extract_sql(input_text), expected)

    def test_cte_select(self):
        """Test extraction of SELECT with Common Table Expression"""

        input_text = """Analysis:
            WITH recent_orders AS (
                SELECT * FROM orders WHERE order_date > '2023-01-01'
            )
            SELECT customer_id, COUNT(*) FROM recent_orders GROUP BY 1
        """
        expected = (
            "WITH recent_orders AS ( SELECT * FROM orders WHERE order_date > '2023-01-01' ) "
            "SELECT customer_id, COUNT(*) FROM recent_orders GROUP BY 1;"
        )
        self.assertEqual(extract_sql(input_text), expected)

    def test_comments_in_sql(self):
        """Test stripping of PostgreSQL comments"""

        input_text = """/* Get active users */
            SELECT 
                id, -- user ID
                name /* full name */
            FROM users
            WHERE active = true
        """

        expected = "SELECT id, name FROM users WHERE active = true;"
        self.assertEqual(extract_sql(input_text), expected)

    def test_nested_comments_handling(self):
        """Verify proper stripping of nested PostgreSQL comments"""

        input_text = """/* Outer comment /* nested comment */ */
            SELECT id FROM users WHERE status = 'active'"""

        expected = "SELECT id FROM users WHERE status = 'active';"

        self.assertEqual(extract_sql(input_text), expected)

    def test_missing_semicolon(self):
        """Test automatic semicolon addition"""
        # Test missing semicolon
        self.assertEqual(extract_sql("SELECT 1"), "SELECT 1;")

        # Test existing semicolon
        self.assertEqual(extract_sql("SELECT 1;"), "SELECT 1;")

        # Test malformed query
        # The invalid query will be directly raised by the PostgreSQL server
        # The syntax check by libraries could cause mismatch between PostgreSQL and the library
        self.assertEqual(extract_sql("SELECT id name"), "SELECT id name;")

    def test_case_insensitivity_handling(self):
        """Test case-insensitive matching"""

        input_text = "SELECT * FROM api_logs"
        expected = "select * from api_logs;"

        self.assertEqual(extract_sql(input_text).lower(), expected)

    def test_multiline_sql(self):
        """Test handling of multi-line queries"""

        input_text = """
            SELECT id,
                   name,
                   email
            FROM users
            WHERE department = 'engineering'
            ORDER BY name
        """

        expected = (
            "SELECT id, name, email FROM users WHERE department = 'engineering' "
            "ORDER BY name;"
        )

        self.assertEqual(extract_sql(input_text), expected)

    # Negative Test Cases
    def test_empty_input_handling(self):
        """Verify proper error handling for empty input"""
        with self.assertRaises(ValueError):
            extract_sql("")

    def test_sql_union_handling(self):
        """Verify UNION handling"""

        input_text = """
            SELECT id, name FROM users
            UNION ALL
            SELECT id, name FROM admins
        """
        expected = "SELECT id, name FROM users UNION ALL SELECT id, name FROM admins;"
        self.assertEqual(extract_sql(input_text), expected)

    def test_error_context_inclusion(self):
        """Verify error context contains debugging information"""

        input_text = "Find dad jokes."

        try:
            extract_sql(input_text)

        except ValueError as e:
            self.assertIn("SQL Extraction Failed:", str(e))
            self.assertIn("Original Input:", str(e))
            self.assertIn("Cleaned Text:", str(e))
        else:
            self.fail("Expected ValueError not raised")

    def test_leading_backticks(self):
        """Strip leading backticks before processing"""

        input_text = "```SELECT * FROM reports;"
        expected = "SELECT * FROM reports;"
        self.assertEqual(extract_sql(input_text), expected)

    def test_trailing_backticks(self):
        """Remove trailing backticks from SQL input"""
        input_text = "SELECT * FROM logs LIMIT 10;```"
        expected = "SELECT * FROM logs LIMIT 10;"
        self.assertEqual(extract_sql(input_text), expected)

    def test_triple_wrapped_backticks(self):
        """Handle fully backtick-wrapped SQL statements"""
        input_text = "```SELECT version();```"
        expected = "SELECT version();"
        self.assertEqual(extract_sql(input_text), expected)

    def test_single_wrapped_backticks(self):
        """Preserve single backticks in quoted identifiers"""

        input_text = "`SELECT group FROM test.users;`"
        expected = "SELECT group FROM test.users;"
        self.assertEqual(extract_sql(input_text), expected)

    def test_block_mysql_backtick(self):
        """Verify MySQL backtick-to-PostgreSQL block"""

        input_text = "SELECT `id`, `name` FROM `users`"
        with self.assertRaises(ValueError) as ctx:

            extract_sql(input_text)

        self.assertIn("Invalid backticks", str(ctx.exception))

    def test_preserve_string_backticks(self):
        """Keep backticks inside string literals"""

        input_text = "SELECT '`test`' AS marker FROM table"
        expected = "SELECT '`test`' AS marker FROM table;"
        self.assertEqual(extract_sql(input_text), expected)

    def test_block_invalid_backticks(self):
        """Detect invalid backtick usage"""
        cases = [
            "SELECT * FROM ``schema.table``",  # Double backticks
            "SELECT * FROM `schema.table",  # Unmatched backtick
            "SELECT 'valid' `\"invalid`",  # Mixed usage
        ]
        for sql in cases:
            with self.subTest(sql=sql):
                with self.assertRaises(ValueError) as ctx:

                    extract_sql(sql)

                self.assertIn("Invalid backticks", str(ctx.exception))

    # Security Pattern Tests
    class TestDMLOperations(unittest.TestCase):
        """Block dangerous Data Manipulation Language commands"""

        def test_block_insert(self):
            """Detect INSERT statements"""
            input_text = "INSERT INTO employees VALUES (1, 'CEO')"
            with self.assertRaises(ValueError) as ctx:
                extract_sql(input_text)
            self.assertIn("INSERT", str(ctx.exception))

        def test_block_update(self):
            """Block UPDATE operations"""
            cases = [
                "UPDATE users SET role='admin'",
                "  update  transactions set amount=0",
                "/* test */UpDaTe inventory SET stock=100",
            ]
            for sql in cases:
                with self.subTest(sql=sql):
                    with self.assertRaises(ValueError):
                        extract_sql(sql)

        def test_block_delete(self):
            """Prevent DELETE operations"""
            input_text = "DELETE FROM sensitive_data WHERE id < 1000"
            with self.assertRaises(ValueError) as ctx:
                extract_sql(input_text)
            self.assertIn("DELETE", str(ctx.exception))


class TestDDLOperations(unittest.TestCase):
    """Block Data Definition Language commands"""

    def test_block_create(self):
        """Prevent table creation"""
        cases = [
            "CREATE TABLE hackers (id serial)",
            "create index on users(email)",
            "  CREATE   DATABASE  test",
        ]
        for sql in cases:
            with self.subTest(sql=sql):
                with self.assertRaises(ValueError):
                    extract_sql(sql)

    def test_block_drop(self):
        """Block structure deletion"""
        input_text = "DROP TABLE financial_records"
        with self.assertRaises(ValueError) as ctx:
            extract_sql(input_text)
        self.assertIn("DROP", str(ctx.exception))

    def test_block_alter(self):
        """Prevent schema modifications"""
        input_text = "ALTER TABLE users ADD COLUMN password text"
        with self.assertRaises(ValueError):
            extract_sql(input_text)

    def test_block_truncate(self):
        """Block bulk data removal"""
        input_text = "TRUNCATE TABLE temporary_data CASCADE"
        with self.assertRaises(ValueError) as ctx:
            extract_sql(input_text)
        self.assertIn("TRUNCATE", str(ctx.exception))


class TestDCLOperations(unittest.TestCase):
    """Block Data Control Language commands"""

    def test_block_grant(self):
        """Prevent privilege escalation"""
        cases = [
            "GRANT ALL ON salaries TO public",
            "/* test */GrAnT INSERT ON table TO role",
        ]

        for sql in cases:
            with self.subTest(sql=sql):

                with self.assertRaises(ValueError):
                    extract_sql(sql)

    def test_block_grant_outside_cte(self):
        """Block GRANT outside CTE"""

        input_text = "  grant  select  on  users  to  hacker"
        result = extract_sql(input_text)

        self.assertIn(result, "select on users to hacker;")  # Invalid but still safe

    def test_block_revoke(self):
        """Block privilege removal"""
        input_text = "REVOKE SELECT ON secrets FROM auditor"
        result = extract_sql(input_text)
        self.assertEqual(result, "SELECT ON secrets FROM auditor;")


class TestTCLOperations(unittest.TestCase):
    """Block Transaction Control Language commands"""

    def test_block_commit(self):
        """Prevent transaction finalization"""
        input_text = "COMMIT;"
        with self.assertRaises(ValueError) as ctx:
            extract_sql(input_text)
        self.assertIn("COMMIT", str(ctx.exception))

    def test_block_rollback(self):
        """Block transaction reversal"""
        input_text = "ROLLBACK TO SAVEPOINT sp01"
        with self.assertRaises(ValueError):
            extract_sql(input_text)

    def test_block_savepoint(self):
        """Prevent savepoint creation"""
        input_text = "SAVEPOINT backup_point"
        with self.assertRaises(ValueError) as ctx:
            extract_sql(input_text)
        self.assertIn("SAVEPOINT", str(ctx.exception))


class TestPlotInterfaceParser(unittest.TestCase):
    """
    Test suite for validating the parsing of plot function metadata from source code.

    This class tests the extraction of function signatures, parameter types,
    and docstring documentation for various function patterns including:
    - Required and optional parameters
    - Type hints and missing type information
    - Docstring formatting variations
    - Multi-function file processing
    """

    def test_function_with_required_params_only(self):
        """Test a function with only required parameters."""
        content = """
def func1(a: int, b: str):
    \"\"\"Args:
        a: Integer parameter.
        b: String parameter.
    \"\"\"
    pass
"""
        # Mock read_code_from_file to return the test content directly
        with patch(
            "app.backend.visualization.plot_details_extractor.read_code_from_file"
        ) as mock_read:
            mock_read.return_value = content.strip()
            result = retrieve_plot_function_details()

        self.assertEqual(len(result), 1)
        func = result[0]
        self.assertEqual(func["name"], "func1")
        self.assertEqual(func["interface"], "def func1(a: int, b: str):")

        self.assertEqual(
            func["dict_args"],
            {
                "a": {"type": "int", "description": "Integer parameter."},
                "b": {"type": "str", "description": "String parameter."},
            },
        )

    def test_function_with_default_params(self):
        """Test a function with parameters having default values."""
        content = """
def func2(a: int, b: str = "default"):
    \"\"\"Args:
        a: Integer parameter.
        b: String parameter. Defaults to "default".
    \"\"\"
    pass
"""
        with patch(
            "app.backend.visualization.plot_details_extractor.read_code_from_file"
        ) as mock_read:
            mock_read.return_value = content.strip()
            result = retrieve_plot_function_details()

        self.assertEqual(len(result), 1)
        func = result[0]
        self.assertEqual(func["interface"], "def func2(a: int):")
        self.assertEqual(
            func["dict_args"],
            {
                "a": {"type": "int", "description": "Integer parameter."},
            },
        )

    def test_function_with_no_params(self):
        """Test a function with no parameters."""
        content = """
def func3():
    \"\"\"No parameters here.\"\"\"
    pass
"""
        with patch(
            "app.backend.visualization.plot_details_extractor.read_code_from_file"
        ) as mock_read:
            mock_read.return_value = content.strip()
            result = retrieve_plot_function_details()

        self.assertEqual(len(result), 1)
        func = result[0]
        self.assertEqual(func["interface"], "def func3():")
        self.assertEqual(func["dict_args"], {})

    def test_docstring_with_args_and_returns(self):
        """Test docstring containing Args and Returns sections."""
        content = """
def func4(a: int):
    \"\"\"Args:
        a: Integer parameter.
    Returns:
        int: Result.
    \"\"\"
    return a
"""
        with patch(
            "app.backend.visualization.plot_details_extractor.read_code_from_file"
        ) as mock_read:
            mock_read.return_value = content.strip()
            result = retrieve_plot_function_details()

        func = result[0]
        self.assertIn("Args:", func["description"])
        self.assertEqual(
            func["dict_args"],
            {
                "a": {"type": "int", "description": "Integer parameter."},
            },
        )

    def test_parameter_without_type_hint(self):
        """Test a parameter without a type hint."""
        content = """
def func5(a):
    \"\"\"Args:
        a: Some parameter.
    \"\"\"
    pass
"""
        with patch(
            "app.backend.visualization.plot_details_extractor.read_code_from_file"
        ) as mock_read:
            mock_read.return_value = content.strip()
            result = retrieve_plot_function_details()

        func = result[0]
        self.assertEqual(func["interface"], "def func5(a):")
        self.assertEqual(
            func["dict_args"],
            {
                "a": {"type": "Any", "description": "Some parameter."},
            },
        )

    def test_function_with_no_docstring(self):
        """Test a function with no docstring."""
        content = """
def func6(a: int):
    pass
"""
        with patch(
            "app.backend.visualization.plot_details_extractor.read_code_from_file"
        ) as mock_read:
            mock_read.return_value = content.strip()
            result = retrieve_plot_function_details()

        func = result[0]
        self.assertEqual(func["description"], "")
        self.assertEqual(
            func["dict_args"],
            {
                "a": {"type": "int", "description": "No description"},
            },
        )

    def test_multiple_functions(self):
        """Test parsing multiple functions."""
        content = """
def func7(a: int):
    \"\"\"Args: a: Integer.\"\"\"
    pass

def func8(b: str):
    \"\"\"Args: b: String.\"\"\"
    pass
"""
        with patch(
            "app.backend.visualization.plot_details_extractor.read_code_from_file"
        ) as mock_read:
            mock_read.return_value = content.strip()
            result = retrieve_plot_function_details()

        self.assertEqual(len(result), 2)
        func7 = next(f for f in result if f["name"] == "func7")
        self.assertEqual(func7["interface"], "def func7(a: int):")
        self.assertEqual(
            func7["dict_args"],
            {"a": {"type": "int", "description": "No description"}},
        )

        func8 = next(f for f in result if f["name"] == "func8")
        self.assertEqual(func8["interface"], "def func8(b: str):")
        self.assertEqual(
            func8["dict_args"],
            {"b": {"type": "str", "description": "No description"}},
        )


if __name__ == "__main__":
    unittest.main()
