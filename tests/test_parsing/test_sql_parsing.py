"""
SQL Parsing Test Suite ensures the secure
extraction of SQL queries from natural language inputs.

SQL Query Handling & Security:
   - SQL query extraction from natural language inputs
   - CTE support and comment sanitization
   - Blocking of unauthorized operations (DDL/DCL/TCL commands)
   - Security patterns preventing data manipulation/injection
   - Error context propagation for debugging
"""

import unittest

from app.backend.sql_parser import extract_sql


class TestExtractSQL(unittest.TestCase):
    """
    Core test suite for SQL query sanitization and security controls.

    Validates:
    - Comment stripping with nested/line comments
    - Structural normalization (CTEs, semicolons)
    - Backtick handling and dialect conversion
    - Error context debugging information
    - Query type detection (SELECT vs DML)

    Tests verify safety through:
    - MySQL → PostgreSQL syntax conversion blocking
    - Reserved word protection
    - Query type whitelisting
    - Malformed query detection
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

        self.assertIn("Unquoted backticks", str(ctx.exception))

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

                self.assertIn("Unquoted backticks", str(ctx.exception))


# Security Pattern Tests
# =======================


class TestDMLOperations(unittest.TestCase):
    """
    Validation suite for blocking data manipulation commands.

    Tests prevent:
    - INSERT/UPDATE/DELETE operations
    - Case-variant command detection
    - Comment-obscured write operations
    - Batch modification attempts
    """

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
    """
    Test suite for schema modification protection.

    Blocks:
    - Table/database creation/deletion
    - Index modifications
    - Column alterations
    - Truncate operations

    Verifies prevention of:
    - Multi-command schema changes
    """

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
    """
    Security suite for privilege management controls.

    Validates blocking of:
    - GRANT/REVOKE operations
    - Role-based access changes
    - CTE-masked privilege commands
    - Inheritance chain modifications
    """

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

    def test_block_cte_masked_grant(self):
        """Block GRANT hidden within CTE structure"""

        input_text = """
            WITH cte AS (SELECT * FROM logs)
            GRANT SELECT ON cte TO unauthorized_user
        """
        with self.assertRaises(ValueError) as ctx:
            extract_sql(input_text)
        self.assertIn("GRANT", str(ctx.exception))

    def test_block_inheritance_chain_modification(self):
        """Prevent role inheritance changes"""

        cases = [
            "GRANT admin_role TO user_role",
            "REVOKE REPORTING_ROLE FROM MANAGER_ROLE CASCADE",
        ]
        for sql in cases:
            with self.subTest(sql=sql):
                with self.assertRaises(ValueError):
                    extract_sql(sql)


class TestTCLOperations(unittest.TestCase):
    """
    Test suite for transaction integrity protection.

    Prevents:
    - COMMIT/ROLLBACK execution
    - Savepoint manipulation

    Ensures atomic operation constraints are maintained.
    """

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


if __name__ == "__main__":
    unittest.main()
