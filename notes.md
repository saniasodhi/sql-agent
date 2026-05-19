## eval matcher lessons (day 11)

took 3 iterations to get the result matcher right:
- v1: strict tuple equality. failed valid answers because agent's extra ID columns made the tuples different shapes.
- v2: positional match (first N agent cols vs gold cols). failed because agent puts ID first, real data after — so positions misaligned.
- v3: match by column name (case-insensitive), with values-only fallback for single-column gold. works.

real lesson: eval design is its own engineering problem. you can have a perfect agent and a busted harness that says it's 60%. always look at WHAT'S failing before trusting the number.

## day 12: self-critique

added a step where the model reviews its own draft sql before executing. catches some logical errors that retries can't (since retries only kick in on execution errors, not wrong-but-runnable sql).

tradeoff: 2x latency on the first attempt. for a real product this is fine; for the eval it just means slower runs.