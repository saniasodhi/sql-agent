"""
The SQL-Agent core.

Day 8 update: now with a retry loop.

Pipeline:
  1. Generate SQL from question + schema.
  2. Try to execute it.
  3. If it fails, tell the model what broke and ask it to fix.
  4. Repeat up to MAX_ATTEMPTS times.

This is the simplest possible "agent loop": act -> observe -> retry.
"""

import re
import sqlite3
from anthropic import Anthropic
from dotenv import load_dotenv

from src.db import get_schema, run_query

# Load env vars and create one shared Claude client.
load_dotenv()
_client = Anthropic()

# How many tries before we give up.
MAX_ATTEMPTS = 3

# Default model. Haiku is cheap and good enough for most queries.
DEFAULT_MODEL = "claude-haiku-4-5-20251001"


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
    """Strip markdown fences and whitespace from a SQL response."""
    s = raw.strip()
    fence_pattern = r"^```(?:sql)?\s*(.*?)\s*```$"
    match = re.match(fence_pattern, s, flags=re.DOTALL | re.IGNORECASE)
    if match:
        s = match.group(1).strip()
    return s


def _call_claude(messages: list[dict], system_prompt: str, model: str) -> str:
    """
    Thin wrapper around the Anthropic client.
    Note: we pass `messages` (a list) instead of a single question, because
    on retries we need to send the conversation history (previous SQL + error).
    """
    response = _client.messages.create(
        model=model,
        max_tokens=1024,
        system=system_prompt,
        messages=messages,
    )
    return response.content[0].text


def text_to_sql(
    question: str,
    schema: str | None = None,
    model: str = DEFAULT_MODEL,
    max_attempts: int = MAX_ATTEMPTS,
    verbose: bool = False,
) -> dict:
    """
    Convert a natural language question into an executed SQL query, with retries.

    Returns a dict with:
      - "sql": the final SQL query string (or "-- UNANSWERABLE")
      - "results": the rows returned by the query, or None if all attempts failed
      - "error": the last error message, or None on success
      - "attempts": how many tries it took (1, 2, or 3)
      - "trace": a list of {sql, error} pairs for each attempt (for debugging)
    """
    if schema is None:
        schema = get_schema()

    system_prompt = SQL_SYSTEM_PROMPT_TEMPLATE.format(schema=schema)

    # We build up the conversation as we go.
    # Start with just the user's question.
    messages = [{"role": "user", "content": question}]

    trace = []

    for attempt in range(1, max_attempts + 1):
        # 1. Get SQL from the model.
        raw = _call_claude(messages, system_prompt, model)
        sql = _clean_sql(raw)

        if verbose:
            print(f"  Attempt {attempt}: {sql[:80]}...")

        # 2. Handle the explicit "I can't answer" sentinel.
        if sql.strip().startswith("-- UNANSWERABLE"):
            return {
                "sql": sql,
                "results": None,
                "error": "Model marked the question as unanswerable.",
                "attempts": attempt,
                "trace": trace + [{"sql": sql, "error": "unanswerable"}],
            }

        # 3. Try to execute it.
        try:
            results = run_query(sql)
            # Success! Return immediately.
            return {
                "sql": sql,
                "results": results,
                "error": None,
                "attempts": attempt,
                "trace": trace + [{"sql": sql, "error": None}],
            }
        except sqlite3.Error as e:
            error_msg = str(e)
            trace.append({"sql": sql, "error": error_msg})

            if verbose:
                print(f"    -> failed: {error_msg}")

            # 4. If we have attempts left, append a retry message.
            #    The model now sees: original question, its broken SQL, and the error.
            if attempt < max_attempts:
                # First, add the model's broken response to the conversation
                # so the next call sees what was tried.
                messages.append({"role": "assistant", "content": sql})
                # Then add a user message describing the error and asking for a fix.
                messages.append({
                    "role": "user",
                    "content": (
                        f"That query failed with this error:\n\n{error_msg}\n\n"
                        "Please fix the query and return ONLY the corrected SQL — "
                        "no explanations, no markdown."
                    ),
                })

    # 5. All attempts exhausted.
    last = trace[-1] if trace else {"sql": None, "error": "no attempts made"}
    return {
        "sql": last["sql"],
        "results": None,
        "error": f"Failed after {max_attempts} attempts. Last error: {last['error']}",
        "attempts": max_attempts,
        "trace": trace,
    }


def nl_query(question: str, **kwargs) -> dict:
    """
    Backwards-compatible wrapper. Returns the same shape as before plus extras.
    Kept so existing callers (like the eval) keep working without changes.
    """
    result = text_to_sql(question, **kwargs)
    return {
        "question": question,
        "sql": result["sql"],
        "results": result["results"],
        "error": result["error"],
        "attempts": result["attempts"],
        "trace": result["trace"],
    }


if __name__ == "__main__":
    # Quick manual test with verbose output so you can watch the loop.
    questions = [
        "Which 3 customers spent the most money?",
        "What is the longest track in the database?",
        # An intentionally fuzzy question to see if retries help:
        "How much money did we make from German invoices?",
    ]

    for q in questions:
        print(f"\n=== {q} ===")
        result = nl_query(q, verbose=True)
        print(f"Final SQL ({result['attempts']} attempt(s)): {result['sql']}")
        if result["error"]:
            print(f"ERROR: {result['error']}")
        else:
            print(f"Results ({len(result['results'])} rows): {result['results'][:3]}")