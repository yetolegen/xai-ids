# Multiclass Results — NSL-KDD (KDDTest+)

Model: XGBoost, `objective="multi:softmax"`, `n_estimators=100`, `max_depth=6`,
`learning_rate=0.1`, `random_state=42`, `sample_weight` = `total/(n_classes*count)`.

## Overall

Accuracy: **0.7709** (22,544 test rows)

| Class  | Precision | Recall | F1   | Support |
|--------|-----------|--------|------|---------|
| DoS    | 0.96      | 0.76   | 0.85 | 7458    |
| Probe  | 0.81      | 0.80   | 0.80 | 2421    |
| R2L    | 0.99      | 0.12   | 0.21 | 2887    |
| U2R    | 0.59      | 0.33   | 0.43 | 67      |
| normal | 0.68      | 0.97   | 0.80 | 9711    |

Macro avg F1: 0.62 — Weighted avg F1: 0.74 (the gap itself is a finding: performance
concentrates in the big classes).

## Confusion matrix (rows=actual, cols=predicted)

| actual\\pred | DoS  | Probe | R2L | U2R | normal |
|--------------|------|-------|-----|-----|--------|
| DoS          | 5686 | 91    | 0   | 0   | 1681   |
| Probe        | 166  | 1928  | 0   | 0   | 327    |
| R2L          | 0    | 64    | 341 | 8   | 2474   |
| U2R          | 0    | 3     | 1   | 22  | 41     |
| normal       | 83   | 217   | 4   | 5   | 9402   |

Derived: normal precision = 9402 / (1681+327+2474+41+9402) = **0.675** — a third of
everything predicted "normal" is actually a missed attack, despite normal's own
recall being 0.97.

## Per-attack-type recall within family (confirms which specific attacks drag each family down)

- **DoS** (0.762): `mailbomb`/`processtable`/`udpstorm`/`apache2` ≈ 0 recall, all zero
  training examples. `neptune`/`smurf`/`back`/`teardrop` ≈ 0.99–1.0.
- **Probe** (0.796): `mscan` ≈ 0.49-0.51 (partial), everything else ≥ 0.99.
- **R2L** (0.118): `guess_passwd`/`httptunnel`/`sendmail`/`named`/`snmpguess`/
  `snmpgetattack`/`xlock`/`xsnoop`/`worm` = 0.0 recall. `warezmaster` 0.26-0.36.
- **U2R** (0.328): `rootkit` 0.0, `ps` 0.27, `xterm` 0.38, `buffer_overflow` 0.40,
  `perl`/`sqlattack` 1.0 (very small support, 2 each).

## Known reproducibility note

Class-level recall for rare attack types (`mscan`, `warezmaster`, `multihop`) can
shift by a few rows between identical re-runs due to XGBoost's non-determinism under
multi-threading (`n_jobs=-1`) even with `random_state` fixed. Family-level recall
(DoS/Probe/R2L/U2R/normal) is stable across runs. If a re-run of `multiclass.ipynb`
shows numbers slightly different from this file at the per-attack-type level, that's
expected — re-run again or check the family-level numbers instead.
