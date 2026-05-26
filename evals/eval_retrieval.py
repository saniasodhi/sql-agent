"""
measures retrieval quality, separate from end-to-end accuracy.

recall@k = of the tables a question NEEDS, what fraction did the retriever return
in its top-k? we care most about whether ALL needed tables are present (full recall),
because a missing table usually means the agent can't answer.
"""

import argparse
from src.retriever import SchemaRetriever
from evals.golden_questions import GOLDEN_QUESTIONS
from evals.required_tables import REQUIRED_TABLES


def evaluate_retrieval(top_k: int):
    retriever = SchemaRetriever(include_decoys=True)

    total_needed = 0
    total_found = 0
    full_recall_count = 0  # questions where ALL needed tables were retrieved
    per_question = []

    for item in GOLDEN_QUESTIONS:
        qid = item["id"]
        needed = REQUIRED_TABLES.get(qid, set())
        if not needed:
            continue
        retrieved = set(retriever.retrieve(item["question"], top_k=top_k))

        found = needed & retrieved
        total_needed += len(needed)
        total_found += len(found)
        all_present = needed.issubset(retrieved)
        if all_present:
            full_recall_count += 1

        per_question.append({
            "id": qid,
            "needed": needed,
            "missing": needed - retrieved,
            "all_present": all_present,
        })

    n = len(per_question)
    micro_recall = total_found / total_needed * 100 if total_needed else 0
    full_recall_pct = full_recall_count / n * 100 if n else 0

    print(f"=== retrieval eval @ top_k={top_k} (41-table schema w/ decoys) ===")
    print(f"micro recall (needed tables found): {micro_recall:.1f}%")
    print(f"full recall (all needed tables present): {full_recall_count}/{n} = {full_recall_pct:.1f}%")
    print()
    misses = [pq for pq in per_question if not pq["all_present"]]
    if misses:
        print("questions missing a needed table:")
        for pq in misses:
            print(f"  Q{pq['id']}: missing {pq['missing']}")
    else:
        print("no misses — all needed tables retrieved for every question.")
    print()
    return full_recall_pct


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--sweep", action="store_true", help="try several top_k values")
    args = parser.parse_args()

    if args.sweep:
        for k in [3, 5, 8, 10]:
            evaluate_retrieval(k)
    else:
        evaluate_retrieval(5)


if __name__ == "__main__":
    main()