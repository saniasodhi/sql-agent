"""
side-by-side model comparison on the golden eval set.
runs each configured model once, prints a table.
"""

import time
import argparse
from src.agent import text_to_sql
from src.db import run_query
from evals.golden_questions import GOLDEN_QUESTIONS
from evals.run_eval import evaluate_one


MODELS_TO_TEST = [
    "claude-haiku-4-5-20251001",
    "claude-sonnet-4-6",
]


def run_one_model(model):
    print(f"\n--- {model} ---")
    t_start = time.time()
    passed = 0
    total_attempts = 0
    failed_ids = []
    for item in GOLDEN_QUESTIONS:
        r = evaluate_one(item, model=model)
        if r["passed"]:
            passed += 1
        else:
            failed_ids.append(r["id"])
        total_attempts += r["attempts"]
    wall_time = time.time() - t_start
    n = len(GOLDEN_QUESTIONS)
    return {
        "model": model,
        "accuracy": passed / n * 100,
        "passed": passed,
        "total": n,
        "wall_time_s": round(wall_time, 1),
        "avg_attempts": round(total_attempts / n, 2),
        "failed_ids": failed_ids,
    }


def main():
    results = []
    for m in MODELS_TO_TEST:
        results.append(run_one_model(m))

    print("\n" + "=" * 70)
    print(f"{'model':<35} {'accuracy':>10} {'wall':>8} {'avg_att':>9}")
    print("-" * 70)
    for r in results:
        print(f"{r['model']:<35} {r['passed']}/{r['total']} ({r['accuracy']:.1f}%) {r['wall_time_s']:>6}s {r['avg_attempts']:>9}")
    print("=" * 70)
    for r in results:
        print(f"  {r['model']} failed: {r['failed_ids']}")


if __name__ == "__main__":
    main()