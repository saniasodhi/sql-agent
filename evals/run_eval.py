"""
Day 7: First eval harness.

For each question in the golden dataset:
  1. Generate SQL with the agent.
  2. Execute the agent's SQL on the database.
  3. Execute the GOLD SQL on the database.
  4. Compare results. Match = correct. Mismatch or error = wrong.

Prints a per-question report and an overall accuracy score.
"""

import time
from src.agent import text_to_sql
from src.db import run_query
from evals.golden_questions import GOLDEN_QUESTIONS


def normalize_results(results) -> list[tuple]:
    """
    Turn a list of dicts into a sorted list of value-tuples for comparison.

    Why sort? Because two queries can return the same rows in different orders
    and still be "correct" — unless the question explicitly asked for an order.
    For now we treat any row-order as equivalent. Day 12 we'll get fancier.
    """
    if results is None:
        return []
    # Each row is a dict; convert to a tuple of its values.
    # Sort so that ordering doesn't break equality checks.
    return sorted(tuple(row.values()) for row in results)


def evaluate_one(item: dict) -> dict:
    """
    Run the agent on one question and compare against the gold answer.
    Returns a result dict for logging.
    """
    qid = item["id"]
    question = item["question"]
    gold_sql = item["gold_sql"]

    # 1. Get agent's SQL. Time it so we can report latency.
    t0 = time.time()
    try:
        agent_sql = text_to_sql(question)
    except Exception as e:
        return {
            "id": qid,
            "question": question,
            "passed": False,
            "reason": f"Agent crashed: {e}",
            "agent_sql": None,
            "latency_s": round(time.time() - t0, 2),
        }
    latency = round(time.time() - t0, 2)

    # 2. Try to execute the agent's SQL.
    try:
        agent_results = run_query(agent_sql)
    except Exception as e:
        return {
            "id": qid,
            "question": question,
            "passed": False,
            "reason": f"Agent SQL failed to execute: {e}",
            "agent_sql": agent_sql,
            "latency_s": latency,
        }

    # 3. Execute the gold SQL — should always work.
    gold_results = run_query(gold_sql)

    # 4. Compare normalized results.
    agent_norm = normalize_results(agent_results)
    gold_norm = normalize_results(gold_results)

    if agent_norm == gold_norm:
        return {
            "id": qid,
            "question": question,
            "passed": True,
            "reason": "Match",
            "agent_sql": agent_sql,
            "latency_s": latency,
        }
    else:
        return {
            "id": qid,
            "question": question,
            "passed": False,
            "reason": f"Result mismatch. Agent got {len(agent_results)} rows, gold got {len(gold_results)} rows.",
            "agent_sql": agent_sql,
            "latency_s": latency,
            "agent_results_preview": agent_results[:3],
            "gold_results_preview": gold_results[:3],
        }


def main():
    print(f"Running eval on {len(GOLDEN_QUESTIONS)} questions...\n")

    results = []
    for item in GOLDEN_QUESTIONS:
        result = evaluate_one(item)
        results.append(result)

        # Per-question line
        status = "✅" if result["passed"] else "❌"
        print(f"{status} Q{result['id']}: {result['question']}")
        print(f"   SQL: {result.get('agent_sql', '<crashed>')}")
        print(f"   {result['reason']}  ({result['latency_s']}s)")
        if not result["passed"] and "agent_results_preview" in result:
            print(f"   Agent rows: {result['agent_results_preview']}")
            print(f"   Gold  rows: {result['gold_results_preview']}")
        print()

    # Summary
    total = len(results)
    passed = sum(1 for r in results if r["passed"])
    accuracy = passed / total * 100
    avg_latency = sum(r["latency_s"] for r in results) / total

    print("=" * 60)
    print(f"RESULTS: {passed}/{total} passed = {accuracy:.1f}% execution accuracy")
    print(f"Average latency: {avg_latency:.2f}s per question")
    print("=" * 60)


if __name__ == "__main__":
    main()