# Eval Baselines

This file tracks how the system improved over time.
Each row is a snapshot — the date, the eval setup, and the score.

| Date       | Day | Eval Set                | Model     | Strategy                   | Accuracy | Avg Latency |
| ---------- | --- | ----------------------- | --------- | -------------------------- | -------- | ----------- |
| 2026-05-XX | 7   | golden_questions (10)   | Haiku 4.5 | Single-shot, schema        | 70%    | 1.31s       |
| 2026-05-XX | 8   | golden_questions (10)   | Haiku 4.5 | + Retry loop (max 3)       | 80%    | 1.76s      |
| 2026-05-XX | 9   | golden_questions (10)   | Haiku 4.5 | + Few-shot (4 examples)    | 90%    | 1.01s       |
| 2026-05-15 | 10  | golden_questions (30)   | Haiku 4.5 | + Few-shot (4 examples)    | 83.3%    | 1.42s       |
| 2026-05-18 | 11  | golden_questions (30)   | Haiku 4.5 | + Few-shot (4 examples)    | 90%    | 1.36s       | - took 3 tries to get the matcher right. lessons in NOTES.

- day 12: + self-critique step before executing. **93.3%**
  - latency roughly doubled (extra LLM call per question). critic revised ~28/30 drafts.

- day 13: model comparison (haiku vs sonnet), rounding fix in matcher (4dp -> 2dp).
  - haiku 4.5: **93% strict**
  - sonnet 4.6: **87% strict, 30/30 verified** (4 misses are correct-but-differently-formatted)
  - decision: ship haiku. cheaper, faster, and the literal output style matches the matcher. sonnet is at least as correct.