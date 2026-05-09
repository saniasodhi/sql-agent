## Progress
- [x] Day 1: Dev environment
- [x] Day 2: Project scaffolding
- [x] Day 3: First LLM call
- [x] Day 4: Database setup & SQL practice
- [x] Day 5: Python ↔ SQLite + schema extractor
- [x] Day 6: MVP — text_to_sql + nl_query end-to-end
- [x] Day 7: First eval harness — 70% baseline accuracy
- [x] Day 9: Few-shot examples in prompt → ZZ%
- [ ] Day 10: Expand the golden dataset to 25-30 questions 

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

Execution accuracy on the internal golden dataset (10 questions on the Chinook database):

| Strategy                              | Model     | Accuracy | Avg Latency |
| ------------------------------------- | --------- | -------- | ----------- |
| Single-shot + schema                  | Haiku 4.5 | 70%    | 1.31s       |
| + Retry loop on errors (max 3 tries)  | Haiku 4.5 | 80%    | 1.76s       |
| + Few-shot prompting (4 examples)     | Haiku 4.5 | 90%    | 1.01s       |

See [BASELINE.md](BASELINE.md) for the full progression.