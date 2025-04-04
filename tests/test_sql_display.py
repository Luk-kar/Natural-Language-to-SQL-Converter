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


class TestSqlTooltips(unittest.TestCase):
    """
    Tests SQL clause parsing and DOM transformations using regex and HTML templates
    dynamically extracted from the JavaScript implementation.
    """

    @classmethod
    def setUpClass(cls):
        # Read the JavaScript file content
        js_path = "app/frontend/static/js/sql_query_display/sql_handler.js"
        with open(js_path, "r", encoding="utf-8") as f:
            js_content = f.read()

        # Extract regex patterns from clauseOrder
        clause_regex = re.compile(
            r"type:\s*'([^']+)',\s*regex:\s*/(.*?)/(\w*)", re.DOTALL
        )
        matches = clause_regex.findall(js_content)
        cls.clause_order = []

        for type_, pattern, flags in matches:
            # Convert JS regex flags to Python flags (only 'i' handled here)
            re_flags = re.IGNORECASE if "i" in flags else 0
            cls.clause_order.append(
                {"type": type_, "regex": re.compile(pattern, re_flags)}
            )

        clauses_required = [
            "WITH",
            "SELECT",
            "UNION",
            "FROM",
            "WHERE",
            "GROUP BY",
            "ORDER BY",
            "LIMIT",
        ]

        # Ensure all required clauses are present
        for clause_definition in clauses_required:
            if not any(
                _clause_entry["type"] == clause_definition
                for _clause_entry in cls.clause_order
            ):
                raise ValueError(f"Missing regex for clause: {clause_definition}")

        # Extract HTML template from processSqlClauses
        template_regex = re.compile(r"map\(clause\s*=>\s*`([^`]+)`", re.DOTALL)
        template_match = template_regex.search(js_content)
        if not template_match:
            raise ValueError("HTML template not found in JS code")
        html_template = template_match.group(1)
        # Convert JS template placeholders to Python format
        html_template = html_template.replace("${clause.type}", "{type}")
        html_template = html_template.replace("${clause.text}", "{text}")
        cls.html_template = html_template

    def setUp(self):
        self.maxDiff = None

    def js_process_sql_clauses(self, pre_element):
        """Python port of processSqlClauses using extracted template"""
        sql = pre_element.text  # Preserve original whitespace
        clauses = self.js_parse_sql_clauses(sql)

        new_content = []
        for clause in clauses:
            span = self.html_template.format(type=clause["type"], text=clause["text"])
            new_content.append(span)
        return " ".join(new_content)

    def js_parse_sql_clauses(self, sql):
        """Python port of parseSqlClauses using extracted regexes"""
        remaining = sql
        clauses = []

        for rule in self.clause_order:
            match = rule["regex"].search(remaining)
            if match:
                clause_text = match.group().strip()
                clauses.append({"type": rule["type"], "text": clause_text})
                remaining = remaining[match.end() :]

        return clauses

    def test_unexpanded_short_query_tooltips(self):
        # Initial render for short query (same as before)
        initial_html = """
        <div class="sql-container">
            <div class="sql-display-wrapper">
                <pre class="sql-display">SELECT name, email FROM users WHERE active = true</pre>
                <span class="sql-info-icon">ⓘ</span>
            </div>
        </div>
        """
        soup = BeautifulSoup(initial_html, "html.parser")
        pre = soup.find("pre", class_="sql-display")

        processed_html = self.js_process_sql_clauses(pre)
        processed_soup = BeautifulSoup(processed_html, "html.parser")

        clauses = processed_soup.find_all("span", class_="sql-clause")
        self.assertGreater(len(clauses), 0)

        for clause in clauses:
            self.assertIn("data-clause-type", clause.attrs)
            self.assertIn(clause["data-clause-type"], ["SELECT", "FROM", "WHERE"])
            self.assertEqual(clause["title"], "placeholder")

    def test_expanded_query_tooltips(self):
        # Test with long SQL (same as before)
        long_sql = (
            "SELECT * FROM ("
            + "sensor_data JOIN weather ON sensor_data.location = weather.location " * 4
            + ")"
        )
        truncated_html = f"""
        <div class="sql-container">
            <div class="sql-display-wrapper">
                <pre class="sql-display">{long_sql[:200]}...</pre>
                <span class="show-full-query" data-full="{long_sql}">Show full query</span>
            </div>
        </div>
        """
        soup = BeautifulSoup(truncated_html, "html.parser")

        full_sql = soup.find("span", class_="show-full-query")["data-full"]
        expanded_pre = soup.new_tag("pre", **{"class": "sql-display"})
        expanded_pre.string = full_sql

        processed_html = self.js_process_sql_clauses(expanded_pre)
        processed_soup = BeautifulSoup(processed_html, "html.parser")

        clauses = processed_soup.find_all("span", class_="sql-clause")
        clause_types = {c["data-clause-type"] for c in clauses}
        self.assertIn("SELECT", clause_types)
        self.assertIn("FROM", clause_types)

        for clause in clauses:
            self.assertTrue(clause.has_attr("title"))
            self.assertGreater(len(clause["title"]), 3)

    def test_clause_parsing_edge_cases(self):
        test_cases = [
            (
                "WITH cte AS (SELECT id FROM tbl) SELECT id FROM cte",
                ["WITH", "SELECT", "FROM", "SELECT", "FROM"],
            ),
            (
                "SELECT name FROM users UNION SELECT email FROM contacts",
                ["SELECT", "FROM", "UNION", "SELECT", "FROM"],
            ),
            (
                "SELECT * FROM (SELECT * FROM subquery) AS sq WHERE sq.id > 100",
                ["SELECT", "FROM", "SELECT", "FROM", "WHERE"],
            ),
        ]

        for sql, expected in test_cases:
            clauses = self.js_parse_sql_clauses(sql)
            detected_types = [c["type"] for c in clauses]
            self.assertEqual(detected_types, expected)


if __name__ == "__main__":
    unittest.main()
