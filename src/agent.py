"""
text-to-sql agent with retry loop + self-critique.

flow:
  question -> draft SQL -> critique step (model reviews its own draft)
  -> possibly revised SQL -> execute -> retry on error (up to 3 times)
"""

import re
import sqlite3
from anthropic import Anthropic
from dotenv import load_dotenv

from src.db import get_schema, run_query
from src.few_shot import format_few_shot_block
from src.schema_tools import full_schema_string

load_dotenv()
_client = Anthropic()

MAX_ATTEMPTS = 3
DEFAULT_MODEL = "claude-haiku-4-5-20251001"


SQL_SYSTEM_PROMPT_TEMPLATE = """You are an expert SQLite SQL writer.

Given a question and a schema, return a single SQLite query.

Rules:
- return ONLY the SQL, no markdown, no explanation
- valid SQLite (not Postgres/MySQL)
- end with a semicolon
- if the question can't be answered with this schema, return: -- UNANSWERABLE

SCHEMA:
{schema}

{few_shot_block}
"""


CRITIC_SYSTEM_PROMPT_TEMPLATE = """You are a SQL reviewer. You will be given a database schema, a natural language question, and a draft SQL query. Your job: decide if the draft answers the question correctly.

Check for:
- wrong tables or columns
- missing JOINs
- missing WHERE filters mentioned in the question
- wrong aggregation (COUNT vs SUM vs AVG)
- wrong sort direction or limit
- missing GROUP BY when using aggregates

If the draft is correct, output exactly: OK
If the draft has a problem, output the CORRECTED SQL only (no markdown, no explanation, end with semicolon).

SCHEMA:
{schema}
"""


def _clean_sql(raw):
    s = raw.strip()
    fence = re.match(r"^```(?:sql)?\s*(.*?)\s*```$", s, flags=re.DOTALL | re.IGNORECASE)
    if fence:
        s = fence.group(1).strip()
    return s


def _call_claude(messages, system_prompt, model=DEFAULT_MODEL):
    response = _client.messages.create(
        model=model,
        max_tokens=1024,
        system=system_prompt,
        messages=messages,
    )
    return response.content[0].text


def _critique(question, draft_sql, schema, model=DEFAULT_MODEL):
    """
    Ask the model to review its own draft. Returns either the original SQL
    (if OK) or a revised version.
    """
    system = CRITIC_SYSTEM_PROMPT_TEMPLATE.format(schema=schema)
    user_msg = f"QUESTION: {question}\n\nDRAFT SQL:\n{draft_sql}"
    raw = _call_claude(
        [{"role": "user", "content": user_msg}],
        system_prompt=system,
        model=model,
    )
    cleaned = _clean_sql(raw)
    # if the critic said "OK" (in any form), keep the draft
    if cleaned.strip().upper().startswith("OK"):
        return draft_sql, "approved"
    return cleaned, "revised"


def text_to_sql(question, schema=None, retriever=None, top_k=5, model=DEFAULT_MODEL, max_attempts=MAX_ATTEMPTS, verbose=False, use_critic=True):
    """
    Returns dict with: sql, results, error, attempts, trace, critic_action, schema_tables

    schema resolution priority:
      1. if `schema` is passed explicitly, use it
      2. elif `retriever` is passed, retrieve top_k relevant tables for the question
      3. else fall back to the default full chinook schema
    """
    retrieved_tables = None
    if schema is None:
        if retriever is not None:
            schema = retriever.retrieve_schema_string(question, top_k=top_k)
            retrieved_tables = retriever.retrieve(question, top_k=top_k)
        else:
            schema = get_schema()

    system_prompt = SQL_SYSTEM_PROMPT_TEMPLATE.format(
        schema=schema,
        few_shot_block=format_few_shot_block(),
    )

    messages = [{"role": "user", "content": question}]
    trace = []
    critic_action = None

    for attempt in range(1, max_attempts + 1):
        # 1. generate (or regenerate) SQL
        raw = _call_claude(messages, system_prompt, model)
        sql = _clean_sql(raw)

        if verbose:
            print(f"  attempt {attempt} draft: {sql[:80]}")

        if sql.strip().startswith("-- UNANSWERABLE"):
            return {
                "sql": sql,
                "results": None,
                "error": "model marked unanswerable",
                "attempts": attempt,
                "trace": trace + [{"sql": sql, "error": "unanswerable"}],
                "critic_action": critic_action,
                "schema_tables": retrieved_tables,
            }

        # 2. critique step (only on first attempt; on retries we already have specific error feedback)
        if use_critic and attempt == 1:
            sql, critic_action = _critique(question, sql, schema, model)
            if verbose:
                print(f"  critic: {critic_action} -> {sql[:80]}")

        # 3. try to execute
        try:
            results = run_query(sql)
            return {
                "sql": sql,
                "results": results,
                "error": None,
                "attempts": attempt,
                "trace": trace + [{"sql": sql, "error": None}],
                "critic_action": critic_action,
                "schema_tables": retrieved_tables,
            }
        except sqlite3.Error as e:
            err = str(e)
            trace.append({"sql": sql, "error": err})
            if verbose:
                print(f"  failed: {err}")
            if attempt < max_attempts:
                messages.append({"role": "assistant", "content": sql})
                messages.append({
                    "role": "user",
                    "content": f"that query failed with this error:\n\n{err}\n\nfix it and return only the corrected SQL.",
                })

    last = trace[-1] if trace else {"sql": None, "error": "no attempts"}
    return {
        "sql": last["sql"],
        "results": None,
        "error": f"failed after {max_attempts} attempts. last error: {last['error']}",
        "attempts": max_attempts,
        "trace": trace,
        "critic_action": critic_action,
        "schema_tables": retrieved_tables,
    }


def nl_query(question, **kwargs):
    result = text_to_sql(question, **kwargs)
    return {
        "question": question,
        "sql": result["sql"],
        "results": result["results"],
        "error": result["error"],
        "attempts": result["attempts"],
        "trace": result["trace"],
        "critic_action": result.get("critic_action"),
        "schema_tables": result.get("schema_tables"),
    }


if __name__ == "__main__":
    questions = [
        "Which 3 customers spent the most money?",
        "What is the longest track in the database?",
    ]
    for q in questions:
        print(f"\n=== {q} ===")
        result = nl_query(q, verbose=True)
        print(f"final sql ({result['attempts']} attempt(s), critic={result['critic_action']}): {result['sql']}")
        if result["error"]:
            print(f"ERROR: {result['error']}")
        else:
            print(f"rows: {result['results'][:3]}")