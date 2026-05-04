"""
The SQL-Agent core.

Today (Day 6) this is a single-shot text-to-SQL function:
  question + schema -> SQL string -> execution -> results.

Later (Day 8+) we'll add a retry loop, schema retrieval, and self-correction.
"""

import re
from src.llm import ask_claude
from src.db import get_schema, run_query


# The system prompt is the single most important piece of this whole project.
# Every word has been chosen carefully:
#   - Tells the model exactly what to output (SQL only)
#   - Tells it the dialect (SQLite, not Postgres / MySQL — those have different syntax)
#   - Forbids markdown fences (the #1 cause of broken outputs)
#   - Forbids explanations (the #2 cause)
#   - Provides the schema so the model knows what tables/columns exist
SQL_SYSTEM_PROMPT_TEMPLATE = """You are an expert SQLite SQL writer.

You will be given a question about a database and the database schema. Your job is to return a single SQLite SQL query that answers the question.

STRICT OUTPUT RULES:
- Return ONLY the SQL query. No explanations. No commentary.
- Do NOT wrap the query in markdown code fences (no ```sql or ```).
- The query must be valid SQLite syntax (not Postgres, not MySQL).
- End the query with a single semicolon.
- If the question cannot be answered with the given schema, return exactly: -- UNANSWERABLE

DATABASE SCHEMA:
{schema}
"""


def _clean_sql(raw: str) -> str:
    """
    Strip common LLM artifacts from a SQL response.
    Even with a good system prompt, models sometimes wrap output in markdown.
    Belt-and-suspenders: tell the model not to do it AND clean it up if it does.
    """
    s = raw.strip()

    # Remove ```sql ... ``` or ``` ... ``` fences if present.
    # The (?s) flag makes . match newlines.
    fence_pattern = r"^```(?:sql)?\s*(.*?)\s*```$"
    match = re.match(fence_pattern, s, flags=re.DOTALL | re.IGNORECASE)
    if match:
        s = match.group(1).strip()

    return s


def text_to_sql(question: str, schema: str | None = None) -> str:
    """
    Convert a natural language question to a SQLite SQL query.

    Args:
        question: The user's question in plain English.
        schema: The database schema as a string. If None, fetches the default
                Chinook schema via get_schema().

    Returns:
        A SQL query string. May be the literal string "-- UNANSWERABLE"
        if the model decided the question can't be answered.
    """
    if schema is None:
        schema = get_schema()

    system_prompt = SQL_SYSTEM_PROMPT_TEMPLATE.format(schema=schema)
    raw = ask_claude(question, system_prompt=system_prompt)
    return _clean_sql(raw)


def nl_query(question: str) -> dict:
    """
    End-to-end: take a natural language question, generate SQL, execute it,
    and return both the SQL and the results.

    Args:
        question: The user's question in plain English.

    Returns:
        A dict with keys:
          - "question": the original question
          - "sql": the generated SQL
          - "results": the rows returned by the query (or None if it failed)
          - "error": error message if the query failed (or None on success)
    """
    sql = text_to_sql(question)

    if sql.strip().startswith("-- UNANSWERABLE"):
        return {
            "question": question,
            "sql": sql,
            "results": None,
            "error": "Model marked the question as unanswerable.",
        }

    try:
        results = run_query(sql)
        return {
            "question": question,
            "sql": sql,
            "results": results,
            "error": None,
        }
    except Exception as e:
        return {
            "question": question,
            "sql": sql,
            "results": None,
            "error": str(e),
        }


if __name__ == "__main__":
    # Quick manual test on a few questions.
    questions = [
        "Which 3 customers spent the most money?",
        "How many tracks are there per genre? Give me the top 5.",
        "What is the longest track in the database?",
        "Who is the President of France?",  # unanswerable from this DB
    ]

    for q in questions:
        print(f"\n=== {q} ===")
        result = nl_query(q)
        print(f"SQL: {result['sql']}")
        if result["error"]:
            print(f"ERROR: {result['error']}")
        else:
            print(f"Results ({len(result['results'])} rows):")
            for row in result["results"][:5]:  # show at most 5 rows
                print(f"  {row}")