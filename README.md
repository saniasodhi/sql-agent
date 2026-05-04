## Progress
- [x] Day 1: Dev environment
- [x] Day 2: Project scaffolding
- [x] Day 3: First LLM call
- [x] Day 4: Database setup & SQL practice
- [x] Day 5: Python ↔ SQLite + schema extractor
- [x] Day 6: MVP — text_to_sql + nl_query end-to-end
- [ ] Day 7: First eval harness — measure how often it works

## Example

```python
from src.agent import nl_query

result = nl_query("Which 3 customers spent the most money?")
print(result["sql"])
# SELECT c.FirstName, c.LastName, SUM(i.Total) AS total_spent ...

print(result["results"])
# [{'FirstName': 'Helena', 'LastName': 'Holý', 'total_spent': 49.62}, ...]
```