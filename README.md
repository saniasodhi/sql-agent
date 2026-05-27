## demo

run the web app locally:

```bash
pip install -r requirements.txt
cp .env.example .env   # add your anthropic api key
streamlit run app.py
```

then open http://localhost:8501. type a question, watch it retrieve tables, write SQL, and return the answer.

## Progress
- [x] Day 1: Dev environment
- [x] Day 2: Project scaffolding
- [x] Day 3: First LLM call
- [x] Day 4: Database setup & SQL practice
- [x] Day 5: Python ↔ SQLite + schema extractor
- [x] Day 6: MVP — text_to_sql + nl_query end-to-end
- [x] Day 7: First eval harness — 70% baseline accuracy
- [x] Day 9: Few-shot examples in prompt → 90%
- [x] Day 10: Expand the golden dataset to 30 questions 
- [x] Day 13: Comparing Haiku and Sonnet 
- [x] Day 18: Making the streamlit app


## Example

```python
from src.agent import nl_query

result = nl_query("Which 3 customers spent the most money?")
print(result["sql"])
# SELECT c.FirstName, c.LastName, SUM(i.Total) AS total_spent ...

print(result["results"])
# [{'FirstName': 'Helena', 'LastName': 'Holý', 'total_spent': 49.62}, ...]
```

## Results
## results

execution accuracy on the internal golden eval (30 questions, chinook db):

| model       | strategy             | strict accuracy | verified* | avg latency |
| ----------- | -------------------- | --------------- | --------- | ----------- |
| haiku 4.5   | single-shot + schema | 70%             | —         | 2.3s        |
| haiku 4.5   | + retry loop         | 80%             | —         | 2.5s        |
| haiku 4.5   | + self-critique      | 93%             | —         | 2.5s        |
| sonnet 4.6  | + self-critique      | 87%             | 30/30     | 5.2s        |

*"verified" = manually checked the strict-match failures. sonnet's 4 misses are all
correct answers formatted differently (combining FirstName+LastName into one column,
or renaming `revenue`→`TotalRevenue`). the strict matcher penalizes the more
human-friendly output. see NOTES.md.

takeaway: a strict result matcher rewards literal column dumps over thoughtful
formatting — the smarter model gets penalized for being smarter. real benchmarks
(BIRD) report both strict and "soft" accuracy for exactly this reason. shipping
haiku for cost/speed; sonnet is at least as correct.

By day 14, I built a text-to-SQL agent with self-correction, evaluated it against a 30-question benchmark with proper execution-accuracy matching, and improved it from 70% to 93% through retry loops, few-shot prompting, and self-critique — then compared models to make a cost-vs-quality decision.

### schema retrieval (RAG)

dumping the full schema doesn't scale past small databases — and it turns out it
also *hurts accuracy*. i added embedding-based retrieval (sentence-transformers,
local) that fetches only the relevant tables per question. tested on a 41-table
schema (11 real chinook + 30 decoys):

| schema strategy        | accuracy | avg schema size | wall time |
| ---------------------- | -------- | --------------- | --------- |
| dump all 41 tables     | 90.0%    | ~2408 tokens    | 225s      |
| retrieve top-5 tables  | 90.0%    | ~449 tokens     | 71s       |
| retrieve top-8 tables  | 93.3%    | ~635 tokens     | 95s       |

retrieval at top-8 *beat* the full-schema baseline (93.3% vs 90%) while using ~4x
fewer schema tokens and running ~2.4x faster. irrelevant tables act as noise that
distracts the model — retrieving only relevant ones improves accuracy and cost at
the same time. this is the feature that makes the agent viable on real databases
with hundreds of tables.

See [BASELINE.md](BASELINE.md) for the full progression.