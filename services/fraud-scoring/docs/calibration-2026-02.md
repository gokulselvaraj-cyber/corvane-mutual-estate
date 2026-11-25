# Fraud score calibration report, February 2026

Author: Fraud Analytics (team-fraud-analytics). Applies to fraud-scoring 1.9.x, model `fraud-rules-2026.02+llm`.

## Why the refer threshold moved from 0.80 to 0.72

ADR-0011 (2024) set the refer threshold at **0.80**. In February 2026 we re-ran the rules on 41,212 claims
closed between 2024-07 and 2025-12, 1,904 of which were confirmed fraud by the counter-fraud team.

| Threshold | Referred | Precision | Recall | Counter-fraud hours / week |
|---|---|---|---|---|
| 0.80 | 1,612 | 0.71 | 0.60 | 96 |
| 0.76 | 2,018 | 0.66 | 0.70 | 121 |
| **0.72** | 2,437 | 0.61 | 0.78 | 146 |
| 0.68 | 3,120 | 0.53 | 0.87 | 187 |

The counter-fraud team agreed to absorb 146 hours a week, so `REFER_THRESHOLD` was set to **0.72** in
`corvane_fraud/settings.py` (release 1.9.0, 2026-03-02). **ADR-0011 has not been updated** and still says 0.80.
The hold threshold stays at 0.91.

## LLM triage

The LLM label (low / medium / high) is weighted 0.15. On the same sample it lifted recall at 0.72 from 0.74 to
0.78, mostly on Motor whiplash and Travel medical claims, which is why injury notes were added to the prompt in
1.7.0. That change was **not** covered by DPIA-2025-031, which assessed the narrative only (see FRAUD-412 for
masking of names and national IDs before the call).

## Per-line notes

- Motor and Travel carry the most weight from the LLM label.
- Cyber has too few closed claims (37) to calibrate; its weights are expert judgement only.
- Gadget early-claim window is the shortest-acting signal and produces the most false positives after upgrades.
