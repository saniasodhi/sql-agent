# Eval Baselines

This file tracks how the system improved over time.
Each row is a snapshot — the date, the eval setup, and the score.

| Date       | Day | Eval Set                | Model     | Strategy                   | Accuracy | Avg Latency |
| ---------- | --- | ----------------------- | --------- | -------------------------- | -------- | ----------- |
| 2026-XX-XX | 7   | golden_questions (10)   | Haiku 4.5 | Single-shot, schema        | 70%    | 1.31s       |
| 2026-XX-XX | 8   | golden_questions (10)   | Haiku 4.5 | + Retry loop (max 3)       | 80%    | 1.76s      |
| 2026-XX-XX | 9   | golden_questions (10)   | Haiku 4.5 | + Few-shot (4 examples)    | 90%    | 1.01s       |