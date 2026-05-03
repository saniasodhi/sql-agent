"""
Database utilities for the SQL-Agent project.
Wraps SQLite operations so the rest of the codebase doesn't worry about connections, cursors, or row-to-dict conversion.
"""

import sqlite3
from pathlib import Path
from typing import Any

# Path to our database. Using pathlib makes this work on any OS.
DB_PATH = Path(__file__).parent.parent / "data" / "raw" / "chinook.db"


def run_query(sql: str, db_path: Path = DB_PATH) -> list[dict[str, Any]]:
    """
    Run a SQL query and return the results as a list of dictionaries.

    Args:
        sql: The SQL query string.
        db_path: Path to the SQLite database file. Defaults to Chinook.

    Returns:
        A list of rows. Each row is a dict mapping column name -> value.
        Returns an empty list if the query produces no results.

    Raises:
        sqlite3.Error: If the SQL is invalid or the query fails.
    """
    # `with` block ensures the connection is closed even if an error happens.
    with sqlite3.connect(db_path) as conn:
        # row_factory makes results behave like dicts instead of plain tuples.
        # We can write row["Name"] instead of row[0].
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(sql)
        rows = cursor.fetchall()
        # Convert each sqlite3.Row to a regular dict for cleaner output.
        return [dict(row) for row in rows]

def get_schema(db_path: Path = DB_PATH) -> str:
    """
    Extract the database schema as a human-readable string.
    Returns CREATE TABLE statements for all tables — perfect for stuffing into an LLM prompt.

    Returns:
        A string with one CREATE TABLE statement per table, separated by blank lines.
    """
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        # sqlite_master is a built-in table that stores metadata about every table.
        # We skip internal SQLite tables (names starting with "sqlite_").
        cursor.execute("""
            SELECT sql
            FROM sqlite_master
            WHERE type = 'table'
              AND name NOT LIKE 'sqlite_%'
            ORDER BY name;
        """)
        statements = [row[0] for row in cursor.fetchall() if row[0]]
        return "\n\n".join(statements)

if __name__ == "__main__":
    print("=== Schema ===")
    print(get_schema())
    print()
    print("=== Sample query ===")
    results = run_query("SELECT Name FROM Artist ORDER BY Name LIMIT 5;")
    for row in results:
        print(f"  - {row['Name']}")