"""
Contains functions to interact with a PostgreSQL database.
"""

# Python
import os
import logging

# Database
import psycopg2

# Database Configuration
DB_CONFIG = {
    "host": os.getenv("DB_HOST"),
    "port": os.getenv("DB_PORT"),
    "database": os.getenv("DB_NAME"),
    "user": os.getenv("DB_USER_READONLY"),
    "password": os.getenv("DB_PASSWORD_READONLY"),
}


def get_schema():
    """Retrieve database schema from PostgreSQL"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()

        # Get tables and columns
        cur.execute(
            """
            SELECT 
                table_schema,
                table_name, 
                column_name, 
                data_type, 
                col_description((table_schema || '.' || table_name)::regclass, ordinal_position) AS column_comment
            FROM information_schema.columns 
            WHERE table_schema = 'public'
            ORDER BY table_name, ordinal_position;
            """
        )

        results = cur.fetchall()

        if not results:
            raise ValueError("No tables or columns found in the public schema.")

        schema = []
        current_table = None
        for table_schema, table, column, dtype, comment in results:  # Fixed unpacking
            if table != current_table:
                schema.append(f"\nTable {table_schema}.{table}:")
                schema.append("|Column|Data Type|Comment|")
                schema.append("|------|---------|-------|")
                current_table = table
            schema.append(f"|{column}|({dtype})|{comment}|")

        return "\n".join(schema)

    except Exception as e:
        logging.error("Schema retrieval error:\n%s", str(e))
        raise  # Re-raise the exception for better error handling
    finally:
        if "conn" in locals():
            conn.close()


def execute_query(sql: str):
    """Execute SELECT SQL query on PostgreSQL"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        cur.execute(sql)

        if cur.description:  # For SELECT queries
            columns = [desc[0] for desc in cur.description]
            results = cur.fetchall()
            return {"columns": columns, "data": results}
        else:  # For non-SELECT queries
            raise ValueError("Only SELECT queries are supported.")

    except Exception as e:
        return {"error": str(e)}
    finally:
        if "conn" in locals():
            conn.close()
