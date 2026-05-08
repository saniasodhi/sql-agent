"""
Day 8: Eval harness, updated to use the retry-aware agent.

Now also reports:
  - average attempts per question (how often did retries kick in)
  - retry success rate (of the failures-on-attempt-1, how many recovered)
"""

import time
from src.agent import text_to_sql
from src.db import run_query
from evals.golden_questions import GOLDEN_QUESTIONS


def normalize_results(results) -> list[tuple]:
    if results is None:
        return []
    return sorted(tuple(row.values()) for row in results)


def evaluate_one(item: dict) -> dict:
    qid = item["id"]
    question = item["question"]
    gold_sql = item["gold_sql"]

    t0 = time.time()
    try:
        agent_out = text_to_sql(question)
    except Exception as e:
        return {
            "id": qid,
            "question": question,
            "passed": False,
            "reason": f"Agent crashed: {e}",
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
            "reason": f"Agent gave up: {agent_out['error']}",
            "agent_sql": agent_sql,
            "attempts": attempts,
            "latency_s": latency,
        }

    # Run the gold SQL for comparison.
    gold_results = run_query(gold_sql)

    if normalize_results(agent_results) == normalize_results(gold_results):
        return {
            "id": qid,
            "question": question,
            "passed": True,
            "reason": "Match",
            "agent_sql": agent_sql,
            "attempts": attempts,
            "latency_s": latency,
        }
    else:
        return {
            "id": qid,
            "question": question,
            "passed": False,
            "reason": (
                f"Result mismatch. Agent got {len(agent_results)} rows, "
                f"gold got {len(gold_results)} rows."
            ),
            "agent_sql": agent_sql,
            "attempts": attempts,
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

        status = "✅" if result["passed"] else "❌"
        print(f"{status} Q{result['id']}: {result['question']}")
        print(f"   SQL: {result.get('agent_sql', '<crashed>')}")
        print(f"   {result['reason']}  ({result['latency_s']}s, {result['attempts']} attempt(s))")
        if not result["passed"] and "agent_results_preview" in result:
            print(f"   Agent rows: {result['agent_results_preview']}")
            print(f"   Gold  rows: {result['gold_results_preview']}")
        print()

    total = len(results)
    passed = sum(1 for r in results if r["passed"])
    accuracy = passed / total * 100
    avg_latency = sum(r["latency_s"] for r in results) / total
    avg_attempts = sum(r["attempts"] for r in results) / total
    needed_retry = sum(1 for r in results if r["attempts"] > 1)
    recovered = sum(1 for r in results if r["passed"] and r["attempts"] > 1)

    print("=" * 60)
    print(f"RESULTS: {passed}/{total} passed = {accuracy:.1f}% execution accuracy")
    print(f"Average latency: {avg_latency:.2f}s per question")
    print(f"Average attempts: {avg_attempts:.2f} per question")
    print(f"Questions that needed a retry: {needed_retry}")
    print(f"Questions that recovered via retry: {recovered}")
    print("=" * 60)


if __name__ == "__main__":
    main()