"""
eval harness for the sql-agent.

semantic result matching:
- single-column gold: compare by value only (column name doesn't matter).
  example: agent returns `invoice_count`, gold has `count`. same number, pass.
- multi-column gold: match agent columns to gold columns by name
  (case-insensitive). agent is allowed to return extra columns; we just project
  to the ones gold asked for. example: gold wants {FirstName, LastName,
  total_spent}, agent returns {CustomerId, FirstName, LastName, total_spent}
  -> we drop CustomerId and compare the rest. pass.
- row count must match; row order doesn't (unless the question is order-
  sensitive, which we don't enforce yet — TODO).
- floats are rounded to 4 decimals to avoid float-noise false negatives.
"""
import argparse
import time
from src.agent import text_to_sql
from src.db import run_query
from evals.golden_questions import GOLDEN_QUESTIONS


def _as_rows_of_dicts(results):
    if results is None:
        return []
    return [dict(row) for row in results]


def _norm_val(v):
    if v is None:
        return "__NONE__"
    if isinstance(v, float):
        return f"{round(v, 2)}"
    return str(v)


def _results_match(agent_rows, gold_rows):
    """
    Returns (passed: bool, reason: str).
    """
    if len(agent_rows) != len(gold_rows):
        return False, f"row count mismatch (agent {len(agent_rows)} vs gold {len(gold_rows)})"

    if not gold_rows:
        return True, "both empty"

    gold_cols = list(gold_rows[0].keys())

    # CASE 1: single-column gold. Ignore column names, compare values only.
    if len(gold_cols) == 1:
        agent_vals = []
        for row in agent_rows:
            vals = list(row.values())
            if len(vals) != 1:
                return False, f"single-column gold but agent returned {len(vals)} columns"
            agent_vals.append(_norm_val(vals[0]))
        gold_vals = [_norm_val(list(r.values())[0]) for r in gold_rows]
        if sorted(agent_vals) == sorted(gold_vals):
            return True, "match (single-col, values-only)"
        return False, "single-col values differ"

    # CASE 2: multi-column gold. Project agent to gold's columns by name (case-insensitive).
    def project(row):
        row_keys_lower = {k.lower(): k for k in row.keys()}
        out = []
        for c in gold_cols:
            if c.lower() not in row_keys_lower:
                return None
            actual_key = row_keys_lower[c.lower()]
            out.append(_norm_val(row[actual_key]))
        return tuple(out)

    agent_tuples = []
    for row in agent_rows:
        p = project(row)
        if p is None:
            return False, f"agent missing gold column(s) by name: {gold_cols}"
        agent_tuples.append(p)

    gold_tuples = []
    for row in gold_rows:
        gold_tuples.append(tuple(_norm_val(row[c]) for c in gold_cols))

    if sorted(agent_tuples) == sorted(gold_tuples):
        return True, "match"
    return False, "values differ"


def evaluate_one(item,model):
    qid = item["id"]
    question = item["question"]
    gold_sql = item["gold_sql"]

    t0 = time.time()
    try:
        agent_out = text_to_sql(question,model=model)
    except Exception as e:
        return {
            "id": qid,
            "question": question,
            "passed": False,
            "reason": f"agent crashed: {e}",
            "agent_sql": None,
            "attempts": 0,
            "latency_s": round(time.time() - t0, 2),
        }
    latency = round(time.time() - t0, 2)

    agent_sql = agent_out["sql"]
    agent_results = agent_out["results"]
    attempts = agent_out["attempts"]

    if agent_results is None:
        return {
            "id": qid,
            "question": question,
            "passed": False,
            "reason": f"agent gave up: {agent_out['error']}",
            "agent_sql": agent_sql,
            "attempts": attempts,
            "latency_s": latency,
        }

    gold_results = run_query(gold_sql)
    agent_rows = _as_rows_of_dicts(agent_results)
    gold_rows = _as_rows_of_dicts(gold_results)

    passed, reason = _results_match(agent_rows, gold_rows)

    if passed:
        return {
            "id": qid,
            "question": question,
            "passed": True,
            "reason": reason,
            "agent_sql": agent_sql,
            "attempts": attempts,
            "latency_s": latency,
        }
    else:
        return {
            "id": qid,
            "question": question,
            "passed": False,
            "reason": reason,
            "agent_sql": agent_sql,
            "attempts": attempts,
            "latency_s": latency,
            "agent_results_preview": agent_results[:3],
            "gold_results_preview": gold_results[:3],
        }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default="claude-haiku-4-5-20251001",
                        help="model id (e.g. claude-haiku-4-5-20251001, claude-sonnet-4-6)")
    args = parser.parse_args()

    print(f"running eval on {len(GOLDEN_QUESTIONS)} questions with model={args.model}...\n")

    results = []
    for item in GOLDEN_QUESTIONS:
        result = evaluate_one(item, model=args.model)
        results.append(result)

        status = "OK" if result["passed"] else "FAIL"
        print(f"[{status}] Q{result['id']}: {result['question']}")
        print(f"   sql: {result.get('agent_sql', '<crashed>')}")
        print(f"   {result['reason']}  ({result['latency_s']}s, {result['attempts']} attempt(s))")
        if not result["passed"] and "agent_results_preview" in result:
            print(f"   agent rows: {result['agent_results_preview']}")
            print(f"   gold  rows: {result['gold_results_preview']}")
        print()

    total = len(results)
    passed = sum(1 for r in results if r["passed"])
    accuracy = passed / total * 100
    avg_latency = sum(r["latency_s"] for r in results) / total
    avg_attempts = sum(r["attempts"] for r in results) / total
    needed_retry = sum(1 for r in results if r["attempts"] > 1)
    recovered = sum(1 for r in results if r["passed"] and r["attempts"] > 1)

    print("=" * 60)
    print(f"model: {args.model}")
    print(f"results: {passed}/{total} passed = {accuracy:.1f}% execution accuracy")
    print(f"avg latency: {avg_latency:.2f}s")
    print(f"avg attempts: {avg_attempts:.2f}")
    print(f"questions that needed a retry: {needed_retry}")
    print(f"questions that recovered via retry: {recovered}")
    print("=" * 60)


if __name__ == "__main__":
    main()