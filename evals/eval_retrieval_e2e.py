"""
end-to-end experiment: does retrieval match dump-everything accuracy
while using fewer tokens?

runs the full eval under three schema conditions and reports accuracy + avg schema size.
"""

import time
from src.agent import text_to_sql
from src.retriever import SchemaRetriever
from src.schema_tools import full_schema_string
from src.db import run_query
from evals.golden_questions import GOLDEN_QUESTIONS
from evals.run_eval import _as_rows_of_dicts, _results_match


def run_condition(label, schema_fn):
    """
    schema_fn(question) -> (schema_string, n_tables) for that question.
    """
    passed = 0
    total_schema_chars = 0
    t0 = time.time()

    for item in GOLDEN_QUESTIONS:
        question = item["question"]
        schema_str, n_tables = schema_fn(question)
        total_schema_chars += len(schema_str)

        out = text_to_sql(question, schema=schema_str)
        if out["results"] is not None:
            gold = run_query(item["gold_sql"])
            ok, _ = _results_match(_as_rows_of_dicts(out["results"]), _as_rows_of_dicts(gold))
            if ok:
                passed += 1

    n = len(GOLDEN_QUESTIONS)
    wall = time.time() - t0
    avg_chars = total_schema_chars / n
    print(f"{label:<28} acc={passed}/{n} ({passed/n*100:.1f}%)  "
          f"avg_schema_chars={avg_chars:.0f} (~{avg_chars/4:.0f} tok)  wall={wall:.0f}s")
    return passed / n * 100, avg_chars


def main():
    print("building retriever...")
    retriever = SchemaRetriever(include_decoys=True)

    # condition 1: dump all 41 tables
    full = full_schema_string(include_decoys=True)
    full_n = full.count("CREATE TABLE")
    def dump_everything(_q):
        return full, full_n

    # condition 2 & 3: retrieval at different k
    def retrieve_k(k):
        def fn(q):
            s = retriever.retrieve_schema_string(q, top_k=k)
            return s, k
        return fn

    print("\nrunning conditions (each runs the full 30-question eval)...\n")
    run_condition("dump everything (41 tbl)", dump_everything)
    run_condition("retrieval top_k=5", retrieve_k(5))
    run_condition("retrieval top_k=8", retrieve_k(8))


if __name__ == "__main__":
    main()