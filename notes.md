## eval matcher lessons (day 11)

took 3 iterations to get the result matcher right:
- v1: strict tuple equality. failed valid answers because agent's extra ID columns made the tuples different shapes.
- v2: positional match (first N agent cols vs gold cols). failed because agent puts ID first, real data after — so positions misaligned.
- v3: match by column name (case-insensitive), with values-only fallback for single-column gold. works.

real lesson: eval design is its own engineering problem. you can have a perfect agent and a busted harness that says it's 60%. always look at WHAT'S failing before trusting the number.

## day 12: self-critique

added a step where the model reviews its own draft sql before executing. catches some logical errors that retries can't (since retries only kick in on execution errors, not wrong-but-runnable sql).

tradeoff: 2x latency on the first attempt. for a real product this is fine; for the eval it just means slower runs.

## day 13: model comparison + a real eval lesson

haiku 4.5: 93% strict, ~2.5s
sonnet 4.6: 87% strict, ~5.2s — BUT all 4 remaining "failures" are correct answers formatted differently:
- Q5/Q20/Q29: sonnet combines FirstName+LastName into one "CustomerName" column. gold keeps them separate. same data.
- Q15: sonnet names columns Genre/TotalRevenue instead of Name/revenue. same data.

so sonnet's *verified* accuracy is 30/30. it lost points for being more human-friendly (combining names, rounding durations) — exactly the things a real user would prefer.

big lesson: a strict matcher punishes the smarter model. real benchmarks (BIRD) report both strict execution accuracy AND verified/soft accuracy for this reason. my matcher rewards literal column dumps over thoughtful formatting.

decision: stick with haiku for the eval (cheaper, faster, and the matcher likes its literal style), but note that sonnet is at least as correct and arguably produces nicer output. would re-evaluate if i cared about output formatting for end users.

## day 15: why schema retrieval

problem: we dump the whole schema into every prompt. fine for chinook (11 tables, ~700 tokens) but breaks on real dbs (100s-1000s of tables):
- doesn't fit in context
- irrelevant tables confuse the model -> wrong table picks
- pay for the whole schema on every call

plan:
- day 15 (today): made a fake 41-table schema (11 real + 30 decoys) to simulate the problem
- day 16: build a retriever that picks the relevant tables for a question (start simple: keyword/embedding match)
- day 17: wire retrieval into the agent, eval "retrieve relevant tables" vs "dump everything", compare accuracy + tokens
