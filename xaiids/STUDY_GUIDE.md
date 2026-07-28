# Study Guide — Everything to Know Cold on This Project

Written 2026-07-26, after the multiclass + SHAP phase. Read this before any interview or
whenever you need to re-derive the project fast.

## 1. The pitch — why this project exists

Portfolio project for an ML Research Engineer pivot from an IT/security background. The
claim is deliberately not "here's an accurate model" — it's "here's a model I can explain
and justify." Accuracy and explainability, proven together, not one traded for the other.

Progression: binary detection (Phase 1, done) → multiclass diagnosis (Phase 2, done
tonight) → cross-dataset generalization test on UNSW-NB15 and CICIDS2017 (not started).

## 2. Project structure

**Phase 1 (binary, NSL-KDD, complete):** `eda1`, `modelcomparison`, `actualtest`,
`modelcompimprove`, `shap`, `shap1`, `localshap`, `localshap1`, `missanalysis`. XGBoost,
attack-vs-normal, `scale_pos_weight` for imbalance.

**Phase 2 (multiclass, NSL-KDD, complete tonight):** `step9_multiclass.ipynb` (5-class
model: DoS/Probe/R2L/U2R/normal), `step10_multiclass_shap.ipynb` (per-class SHAP).

**Not started:** UNSW-NB15, then CICIDS2017.

**Known debt, say this unprompted if asked about code quality:** `Untitled*.ipynb` scratch
files still sitting in `nsl-kdd/notebooks/`; no shared `utils.py`/`config.py`; step9 and
step10 each retrain their own copy of the model instead of sharing one saved artifact.

## 3. Core ML vocabulary — the stuff that was actually confusing, now locked in

- **X / y / train / test:** X = the question side (features), y = the answer side
  (target). Train = what the model studies from. Test = a pop quiz using rows it never
  saw, so a good test score means it learned a real pattern, not just memorized rows.
- **Why `LabelEncoder` gets fit on train+test combined:** prevents a crash if a category
  value only appears in test. Not leakage — it never touches `y`, no predictive
  relationship is learned, it's just a fixed string-to-number lookup table.
- **`class_weights` / `sample_weight`:** formula = `total_rows / (n_classes × class_count)`.
  Rare classes get bigger weight so the training loss doesn't ignore them. U2R (52 rows)
  got 484.5x — the highest of any class.
- **`multi:softmax` vs `multi:softprob`:** softmax returns only the winning class number,
  throwing away confidence scores. Real, fixable limitation — softprob would let you tell
  a confidently-wrong miss from an uncertain, borderline one.
- **Precision vs recall vs F1 vs support:** recall = of all real X, how many caught.
  Precision = of everything called X, how many actually were X. F1 = harmonic mean of the
  two (punishes lopsided cases — R2L's 0.99 precision / 0.12 recall averages to a
  misleading 0.55 in a plain mean, but F1 correctly reports 0.21). Support = raw count of
  real examples of that class — small support means don't trust the metric (e.g. udpstorm,
  n=2).
- **Macro avg vs weighted avg:** macro treats every class equally regardless of size;
  weighted lets big classes dominate. The gap between them here (0.62 vs 0.74) is itself a
  finding — it shows performance is concentrated in the big classes.
- **SHAP, one sentence:** a SHAP value is how much one feature pushed one specific
  prediction away from the model's average baseline; `base_value + sum(all SHAP values) =
  final prediction`, always. Multiclass means 5 separate SHAP explanations per row, one
  per class, computed together.
- **The `isinstance(shap_values_raw, list)` check:** defensive code for a real shap-library
  version inconsistency (old versions return a list of arrays, new versions return one 3D
  array). Normalize once right after the library call instead of scattering version checks
  everywhere downstream — that's the actual lesson, not just this one line.

## 4. The numbers — know these cold

- Multiclass: **0.7709 accuracy**, 0.74 weighted F1.
- Per-family recall: **DoS 0.762, Probe 0.796, R2L 0.118, U2R 0.328.**
- R2L: 0.99 precision / 0.12 recall / 0.21 F1 — model almost never says R2L, right when it
  does.
- 86% of real R2L rows get predicted `normal` (2474 of 2887).
- DoS→normal = 1681 vs. DoS→Probe = 91 — misses collapse into `normal`, not into other
  attack types (~18x skew).
- `neptune` = 41,214 of DoS's 45,927 training rows = **89.7%**.
- `apache2`/`mailbomb`/`processtable`/`udpstorm` = **zero** training examples, near-zero
  multiclass recall — despite `apache2` (65.9%) and `udpstorm` (100%) recall in the
  original *binary* model. Real regression, not just "unseen attacks are hard."
- U2R: 52 training examples, highest class weight of any class (484.5x), still only 0.328
  recall.

## 5. The findings that make this research, not just a model

- **Camouflage (`guess_passwd`, R2L):** genuinely resembles normal traffic — seen in
  training (53 examples) and still 0% recall. Proven two ways: raw feature box plots show
  its distribution overlapping normal's, and its mean SHAP profile mirrors normal's almost
  feature-for-feature. A data/feature-space problem, not a sample-size problem.
- **Unseen-attack problem (most other 0-recall R2L types):** `httptunnel`, `sendmail`,
  `named`, `xlock`, `worm`, `snmpguess`, `snmpgetattack`, `xsnoop` — zero training examples,
  a completely different mechanism from camouflage even though the symptom (0% recall)
  looks identical.
- **DoS/Probe generalization asymmetry:** Probe's unseen types (`saint`, `mscan`) survive
  via "behavioral transfer" to known scanners (same mechanical behavior: touch many
  ports/hosts). DoS's unseen types (`apache2` etc.) don't transfer, because DoS's learned
  signature is almost entirely `neptune`'s volumetric flood, and application-layer DoS
  looks nothing like a flood. Working hypothesis: transfer depends on how behaviorally
  *homogeneous* a family's known training members are — Probe is uniform (all scanning),
  DoS is not (floods vs. app-layer exhaustion).
- **U2R has real signal, not camouflage:** `root_shell`, `num_file_creations` — genuine
  privilege-escalation indicators, not generic traffic stats. Bottlenecked by data
  starvation (52 examples), not feature ambiguity. Clean contrast case against R2L.
- **The big one — "normal" as an implicit default class:** every attack family has
  features that argue *for* it. Normal doesn't — its top SHAP features are just the attack
  features with the sign flipped. In a softmax multiclass setup this means normal is a
  leftover bucket, not a learned class: whatever doesn't strongly match a known attack
  signature defaults into it, regardless of whether it actually resembles real normal
  traffic. This is the unifying mechanism behind both the DoS and R2L findings above, and
  it's an architecture-level claim, not an NSL-KDD quirk — worth testing for reproducibility
  once UNSW-NB15/CICIDS2017 are online.

## 6. Honest limitations — say these before someone asks

- NSL-KDD is a 1999/2009 dataset, the most recognizable "beginner tutorial" benchmark in
  this field. Stopping at an accuracy number on it would read as tutorial-tier. The
  mitigation is everything in section 5 — mechanism-level findings, not just a score — plus
  testing generalization on newer datasets next.
- `multi:softmax` throws away confidence scores that would help diagnose borderline misses.
- step9/step10 duplicate training code instead of sharing one saved model artifact.
- The waterfall examples are literally "whichever correctly-classified row comes first in
  the file," not curated or representative — a real limitation if asked how those examples
  were chosen.
- UNSW-NB15 has documented severe imbalance and real class overlap (Zoghi & Serpen, 2024).
  CICIDS2017 has a serious, published labeling/feature-leakage bug in CICFlowMeter
  affecting ~26% of the dataset (Engelen et al., WTMC 2021) — plan is to use LYCOS-IDS2017
  or Engelen's corrected release instead of the raw UNB CSVs, and to drop IP/port/timestamp
  columns on both datasets regardless.

## 7. What's next

1. Clean up `Untitled*.ipynb` scratch files in `nsl-kdd/notebooks/`.
2. UNSW-NB15 (feature alignment, apply the imbalance/overlap lessons above), then
   CICIDS2017 (corrected version only).
3. Camouflage-vs-starvation ablation: vary training size for U2R vs. R2L, see whether
   recall climbs (starvation) or plateaus early (camouflage) — deliberately scheduled after
   the base project progresses further, not before.
4. Read the two directly-relevant papers before/during the CICIDS2017 phase: the SHAP +
   strategic-sampling paper (arXiv 2602.19087, applied to CIC-IDS2017 itself) and the SDN
   multiclass-imbalance + XAI paper (Scientific Reports, 2026).

## 8. The 30-second version

"I built an explainable intrusion detection pipeline on NSL-KDD — binary first, then
extended to multiclass to diagnose *which* of four attack families a connection belongs
to, XGBoost with SHAP throughout. The interesting part isn't the 77% accuracy, it's what's
underneath it: some attack types get missed because they're genuinely camouflaged as
normal traffic — I proved that with feature comparisons, not just a low score. Others get
missed purely from too little training data despite having a real, meaningful signal.
And there's a structural finding that 'normal' isn't actually a learned class in this kind
of model, it's leftover space, which is why unfamiliar attacks default into it. I'm about
to test whether that last one is a general property of this kind of architecture or just an
artifact of this one old dataset, by rerunning the same analysis on a newer one."
