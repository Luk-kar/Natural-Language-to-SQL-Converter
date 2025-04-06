# Python
import os
import re
import unittest

# Third-party
from flask import Flask, template_rendered
from bs4 import BeautifulSoup


class TestSqlRenderingByLength(unittest.TestCase):
    """
    Test suite for SQL container display behavior based on query length.

    Validates:
    - Proper rendering of the SQL display container for different input lengths
    - Full SQL display for queries shorter than or equal to 200 characters
    - Automatic truncation for queries exceeding 200 characters
    - Presence of an info icon for short queries
    - Visibility of the "show full query" expansion control for long queries
    - Correct preservation of the full SQL query in the expansion control
    - Edge case handling for queries exactly 200 characters long
    - Structural integrity of the HTML output using BeautifulSoup parsing
    - Ensures template resolution and rendering logic works as expected
    - Prevents unintended modifications to the SQL display logic

    Tests verify correct behavior through:
    - HTML structure validation using BeautifulSoup
    - String length assertions to enforce truncation rules
    - Presence and absence of expansion UI elements based on SQL length
    - Context-based template rendering to simulate Flask environment
    - Edge case coverage for SQL length boundary conditions
    """

    def setUp(self):
        # Get the absolute path to the project root
        self.project_root = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..")
        )

        # Configure Flask app with proper template path
        self.app = Flask(
            __name__,
            template_folder=os.path.join(
                self.project_root, "app", "frontend", "templates"
            ),
        )

        self.context = {}

    def render_template(self, context):
        """Helper to render templates with absolute path resolution"""
        template_path = os.path.join(
            "components", "results", "tabs", "table_result", "sql_display.html"
        )

        with self.app.test_request_context():
            rendered = None

            def record(sender, template, context, **extra):
                nonlocal rendered
                rendered = template.render(context)

            template_rendered.connect(record)
            template = self.app.jinja_env.get_template(template_path)
            rendered = template.render(context)

            return rendered

    def test_short_sql_rendering(self):
        """Test rendering with SQL shorter than 200 characters"""

        sql = "SELECT * FROM table WHERE id = 1"

        if len(sql) >= 200:
            raise ValueError("SQL string is too long for this test case.")

        context = {"result": {"sql": sql}}

        rendered = self.render_template(context)
        soup = BeautifulSoup(rendered, "html.parser")

        # Verify container structure
        container = soup.find(class_="sql-container")
        self.assertIsNotNone(container, "SQL container should exist")

        pre = soup.find("pre", class_="sql-display")
        self.assertIsNotNone(pre, "SQL pre element should exist")
        self.assertEqual(
            pre.text.strip(), sql, "Should show full SQL without truncation"
        )

        # Verify info icon exists and expansion link is hidden
        self.assertIsNotNone(
            soup.find("span", class_="sql-info-icon"),
            "Info icon should be present for short SQL",
        )
        self.assertIsNone(
            soup.find("span", class_="show-full-query"),
            "Show-full-query should be hidden for short SQL",
        )

    def test_long_sql_rendering(self):
        """Test rendering with SQL longer than 200 characters"""

        sql = (
            "WITH monthly_sales AS ("
            "  SELECT DATE_TRUNC('month', order_date) AS month, "
            "         SUM(total_amount) AS total_sales "
            "  FROM orders "
            "  WHERE order_date BETWEEN '2023-01-01' AND '2023-12-31' "
            "  GROUP BY 1"
            ") "
            "SELECT m.month, m.total_sales, "
            "       LAG(m.total_sales, 1) OVER (ORDER BY m.month) AS prev_month_sales, "
            "       (m.total_sales - LAG(m.total_sales, 1) OVER (ORDER BY m.month)) AS growth "
            "FROM monthly_sales m "
            "ORDER BY m.month DESC;"
        )
        if len(sql) <= 200:
            raise ValueError("SQL string is not long enough for this test case.")

        context = {"result": {"sql": sql}}

        rendered = self.render_template(context)
        soup = BeautifulSoup(rendered, "html.parser")

        # Verify truncation
        pre = soup.find("pre", class_="sql-display")
        expected_truncated = f"{sql[:200]}..."
        self.assertEqual(
            pre.text.strip(),
            expected_truncated,
            "Should truncate SQL to 200 chars + ellipsis",
        )

        # Verify expansion control exists with full SQL
        expand_control = soup.find("span", class_="show-full-query")
        self.assertIsNotNone(
            expand_control, "Show-full-query should be present for long SQL"
        )
        self.assertEqual(
            expand_control["data-full"],
            sql,
            "Expansion control should contain full SQL",
        )

    def test_edge_case_exact_200_chars(self):
        """Test SQL with exactly 200 characters shows full query"""

        sql = (
            "SELECT column1, column2, column3, column4, column5, column6, column7, column8"
            + " FROM extended_sample_table "
            + "WHERE column1>=100 AND column2<=500 AND column3<>0 "
            + "ORDER BY column4 ASC, column5 DESC LIMIT 75;"
        )
        if len(sql) != 200:
            raise ValueError(
                "SQL string is not exactly 200 characters for this test case."
            )

        context = {"result": {"sql": sql}}

        rendered = self.render_template(context)
        soup = BeautifulSoup(rendered, "html.parser")

        pre = soup.find("pre", class_="sql-display")
        self.assertEqual(
            len(pre.text.strip()),
            200,
            "Should show full 200-character SQL without truncation",
        )
        self.assertNotIn("...", pre.text, "Should not add ellipsis for exact 200 chars")


def upload_js_file() -> str:
    """
    Upload a JavaScript file and return its content.
    """
    js_path = os.path.join(
        "app", "frontend", "static", "js", "sql_query_display", "sql_handler.js"
    )
    file_path = os.path.join(js_path)
    with open(file_path, "r") as file:
        js_content = file.read()
    return js_content


def get_alias_regex_line(js_content: str) -> str:
    """
    Extract the line containing the alias regex from the JavaScript content.
    """
    # Define regex to match lines starting with optional spaces then "const aliasRegex" (case-insensitive)
    pattern = re.compile(r"^\s*const aliasRegex", re.IGNORECASE)
    for line in js_content.splitlines():
        if pattern.match(line):
            return line

    raise ValueError("Alias regex line not found in JavaScript content")


def check_alias_regex(alias_regex: str) -> bool:
    """
    Check if the alias regex is valid.
    """
    js_content = upload_js_file()
    alias_regex_line = get_alias_regex_line(js_content)

    return bool(alias_regex in alias_regex_line)


def check_window_start_regex(window_start_regex: str) -> bool:
    """
    Check if the window start regex is valid.
    """
    js_content = upload_js_file()
    window_start_regex_line = extract_window_start_regex(js_content)

    return bool(window_start_regex in window_start_regex_line)


def check_sql_clauses(sql_clauses: str) -> bool:

    pattern = re.compile(
        r"const\s+list_clauses\s*=\s*\[(.*?)\];", re.DOTALL | re.IGNORECASE
    )
    js_content = upload_js_file()
    match = pattern.search(js_content)
    if not match:
        raise ValueError("list_clauses not found in JS code")
    list_clauses_line = match.group(1)

    for clause in sql_clauses:
        if not clause.replace("\\", "") in list_clauses_line.replace("\\", ""):
            raise ValueError(
                rf"Clause '{clause}' not found in list_clauses:\n{list_clauses_line}"
            )


def transform_clause(clause: str) -> str:

    # Convert to uppercase to avoid case sensitivity issues
    upper_clause = clause.upper()

    # Replace literal "\s+" (ignoring case) with a space.
    # The regex r'\\s\+' matches a literal backslash, followed by "s" (or "S") and a literal plus sign.
    transformed = re.sub(r"\\s\+", " ", upper_clause, flags=re.IGNORECASE)

    # Remove any remaining backslashes.
    transformed = transformed.replace("\\", "")

    # Remove quotes and strip any extra whitespace.
    transformed = transformed.replace('"', "").strip()

    return transformed


def extract_window_start_regex(js_content: str) -> str:
    """
    Extract the windowStartRegex from the JavaScript content.
    """
    window_start_regex = re.compile(r"\s+const windowStartRegex.+;", re.IGNORECASE)
    window_start_match = window_start_regex.search(js_content)

    if not window_start_match:
        raise ValueError("windowStartRegex not found in JS code")

    window_start_line = window_start_match.group(0)
    window_start_regex = window_start_line.split("=")[1].strip().replace(";", "")

    if window_start_regex.endswith("gi"):
        window_start_regex = window_start_regex[:-3]

    return window_start_regex


def split_sql(sql: str):
    # List of SQL clauses.
    list_clauses = [
        "OVER",
        "WITH",
        "SELECT",
        "FROM",
        "WHERE",
        "INNER\\s+JOIN",
        "LEFT\\s+JOIN",
        "RIGHT\\s+JOIN",
        "FULL\\s+JOIN",
        "CROSS\\s+JOIN",
        "NATURAL\\s+JOIN",
        "JOIN",
        "ORDER\\s+BY",
        "GROUP\\s+BY",
        "HAVING",
        "LIMIT",
        "OFFSET",
        "UNION\\s+ALL",
        "UNION",
        "INTERSECT",
        "EXCEPT",
        "FETCH",
        "EXCLUDE",
    ]

    check_sql_clauses(list_clauses)

    # Preserve order while removing duplicates.
    unique_clauses = list(dict.fromkeys(list_clauses))
    # Adjust clause patterns to include leading whitespace or start of string, and use a word boundary.
    clause_patterns = [r"(?:\s+|^)" + clause + r"\b" for clause in unique_clauses]
    # Join the individual patterns using the OR operator.
    pattern_string = "|".join(clause_patterns)
    # Build a regular expression that uses a positive lookahead to split at each clause start.
    clause_regex = re.compile(r"(?={})".format(pattern_string), flags=re.IGNORECASE)
    # Split the SQL query using the generated regex.
    return clause_regex.split(sql)


def split_sql_with_window_functions(sql: str):
    parts = []
    current_index = 0
    # Pattern to locate a window function start: function(...) OVER (

    window_start_regex = r"""(\w+)\s*\([^)]*\)\s+OVER\s*\("""

    window_start_pattern = re.compile(window_start_regex, flags=re.IGNORECASE)

    if not check_window_start_regex(window_start_regex):
        raise ValueError("Window start regex is not valid")

    alias_regex = r"""\s+AS\s+([\w_]+|"[^"]*"|'[^']*')\b"""

    if not check_alias_regex(alias_regex):
        raise ValueError("Alias regex is not valid")

    # Pattern to match an optional alias after the OVER clause.
    alias_pattern = re.compile(alias_regex, flags=re.IGNORECASE)

    while current_index < len(sql):
        match = window_start_pattern.search(sql, pos=current_index)
        if not match:
            # Add any remaining part if no more window functions are found.
            parts.append(sql[current_index:])
            break

        window_start = match.start()
        # Append text before the window function.
        before_window = sql[current_index:window_start]
        if before_window:
            parts.append(before_window)

        # Now, find the end of the OVER clause's parentheses.
        paren_depth = 1
        index = match.end()  # Position after 'OVER ('
        while index < len(sql) and paren_depth > 0:
            if sql[index] == "(":
                paren_depth += 1
            elif sql[index] == ")":
                paren_depth -= 1
            index += 1
        window_end = index

        # Check for an alias after the closing parenthesis.
        alias_match = alias_pattern.search(sql, pos=window_end)
        if alias_match:
            window_end = alias_match.end()

        # Append the complete window function part.
        parts.append(sql[window_start:window_end])
        current_index = window_end

    # Return non-empty parts.
    return [part for part in parts if part.strip()]


def parse_sql_clauses(sql: str):
    window_parts = split_sql_with_window_functions(sql)
    result = []
    # Pattern to check if a part contains a window function (using "OVER (").
    over_pattern = re.compile(r"\bOVER\s*\(", flags=re.IGNORECASE)
    for part in window_parts:
        if over_pattern.search(part):
            result.append(part)
        else:
            # For non-window parts, split them into SQL clauses.
            clauses = split_sql(part)
            result.extend(clauses)
    # Filter out any empty or whitespace-only strings.
    return [p for p in result if p.strip()]


# --- Unit tests ---


class TestSQLParsing(unittest.TestCase):

    def test_split_sql(self):

        # When SQL starts with a clause, the first element may be an empty string.
        sql = "SELECT a, b FROM table WHERE a = 1 ORDER BY a"
        parts = split_sql(sql)
        # Expected behavior: split at positions where the clauses start.
        # The first element is empty because "SELECT" is at the beginning.
        self.assertTrue(parts[0] == "" or parts[0].strip() == "SELECT")
        # Check that at least all keywords are present in the split.
        joined = " ".join(parts)
        self.assertIn("SELECT", joined)
        self.assertIn("FROM", joined)
        self.assertIn("WHERE", joined)
        self.assertIn("ORDER BY", joined)

    def test_split_sql_with_window_functions(self):

        # SQL containing a window function.
        sql = "SELECT a, SUM(a) OVER (PARTITION BY id) AS sum_a FROM table"
        parts = split_sql_with_window_functions(sql)
        # Expected parts:
        # 1. "SELECT a, " (or similar, before the window function)
        # 2. "SUM(a) OVER (PARTITION BY id) AS sum_a"
        # 3. " FROM table"
        self.assertEqual(len(parts), 3)
        self.assertIn("SUM(a)", parts[1])
        self.assertIn("OVER (", parts[1])
        self.assertIn("AS sum_a", parts[1])

    def test_parse_sql_clauses_without_window(self):

        # SQL without window functions should be split by clauses.
        sql = "SELECT a, b FROM table WHERE a > 1 GROUP BY a HAVING COUNT(a) > 1"
        clauses = parse_sql_clauses(sql)
        # We expect multiple non-empty parts; check some keywords.
        joined = " ".join(clauses)
        self.assertIn("SELECT", joined)
        self.assertIn("FROM", joined)
        self.assertIn("WHERE", joined)
        self.assertIn("GROUP BY", joined)
        self.assertIn("HAVING", joined)

    def test_parse_sql_clauses_with_window(self):

        # SQL with window function and regular clauses.
        sql = (
            "SELECT a, SUM(a) OVER (PARTITION BY id) AS sum_a, "
            "b FROM table WHERE b > 100 ORDER BY a"
        )
        parts = parse_sql_clauses(sql)
        # Check that at least one part is the window function.
        window_parts = [
            p for p in parts if re.search(r"\bOVER\s*\(", p, flags=re.IGNORECASE)
        ]
        self.assertTrue(len(window_parts) >= 1)
        # And the remaining parts should contain other SQL clauses.
        joined = " ".join(parts)
        self.assertIn("SELECT", joined)
        self.assertIn("FROM", joined)
        self.assertIn("WHERE", joined)
        self.assertIn("ORDER BY", joined)


if __name__ == "__main__":
    unittest.main()
