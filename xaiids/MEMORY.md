# MEMORY.md — XAI-IDS Project State

## Project Overview
**Explainable AI for Intrusion Detection Systems (XAI-IDS)**
- Portfolio project demonstrating: baseline IDS model + explainability layer + multi-dataset evaluation
- Goal: Show that ML can be both accurate AND interpretable in security context
- Audience: Hiring managers / ML engineer interviewers

## Current Phase
**Phase 1 (Complete):** Binary classification + SHAP analysis on NSL-KDD
**Phase 2 (In Progress):** Multiclass classification on NSL-KDD (done) + SHAP (done) + UNSW-NB15 (not started)

## What's Done

### NSL-KDD Binary Classification
- EDA complete (`eda1.ipynb`)
- Preprocessing pipeline: feature scaling, encoding, train/test split
- **Baseline model:** XGBoost (`XGBClassifier`, n_estimators=100, max_depth=6, learning_rate=0.1), binary attack/normal. A Random Forest run (`actualtest.ipynb`) and other ablations (`modelcomparison.ipynb`, `modelcompimprove.ipynb`) were comparison baselines, not the model carried into SHAP analysis.
- **Performance (XGB baseline, KDDTest+):** Accuracy 0.8079, Precision 0.9689, Recall 0.6846, F1 0.8023. A `scale_pos_weight`-tuned + depth-8 variant ("XGB + all improvements") trades a bit of accuracy/F1 for essentially the same recall (0.8035 acc, 0.7968 F1, 0.677 recall) — not a clear win, so the plain baseline is still the reference model.
- **SHAP analysis:** TreeExplainer on the XGB baseline; local + global SHAP in `shap.ipynb`/`shap1.ipynb`, `localshap.ipynb`/`localshap1.ipynb`; false-negative deep dive in `missanalysis.ipynb`.
- **Deliverable:** Full pipeline in `nsl-kdd/notebooks/` (see RESEARCH_NOTES.md for the analysis narrative — the notebooks aren't yet renamed/cleaned into a portfolio-ready sequence, see below)

### NSL-KDD Multiclass Classification (Phase 2, added 2026-07-25)
- `step9_multiclass.ipynb`: XGBoost multiclass (`multi:softmax`), 5 classes (DoS/Probe/R2L/U2R/normal), `sample_weight` balanced by inverse class frequency. **0.7709 accuracy, 0.74 weighted F1** on KDDTest+.
- Per-family recall: DoS 0.762, Probe 0.796, R2L 0.118, U2R 0.328.
- `step10_multiclass_shap.ipynb`: per-class TreeExplainer SHAP (stratified sample, 200/family), beeswarms per family, cross-family mean-SHAP heatmap, waterfall examples. Outputs in `nsl-kdd/figures/` and `nsl-kdd/notebooks/` (`mc_*.png`).
- See RESEARCH_NOTES.md section 10 for the DoS generalization-asymmetry finding this run surfaced.

### Actual Notebook Structure (as of 2026-07-25)
```
xai-ids/
├── nsl-kdd/
│   ├── data/README.md
│   └── notebooks/
│       ├── eda1.ipynb                 — EDA
│       ├── modelcomparison.ipynb      — early RF vs XGB comparison
│       ├── actualtest.ipynb           — RandomForest run (acc 0.77, F1 0.7588) — comparison baseline
│       ├── modelcompimprove.ipynb     — XGB ablations (baseline / log-transform / class-weight / all-improvements)
│       ├── shap.ipynb, shap1.ipynb    — global SHAP on XGB baseline
│       ├── localshap.ipynb, localshap1.ipynb — per-sample SHAP, guess_passwd case study
│       ├── missanalysis.ipynb         — false-negative / miss analysis
│       ├── step9_multiclass.ipynb     — 5-class XGBoost (DoS/Probe/R2L/U2R/normal), acc 0.7709
│       ├── step10_multiclass_shap.ipynb — per-class SHAP on the multiclass model
│       └── Untitled*.ipynb, X_train.csv, X_test.csv, y_train.csv, y_test.csv — scratch/export files, not yet organized
├── xaiids/ (CLAUDE.md, MEMORY.md, RESEARCH_NOTES.md)
└── README.md, DISCUSSION.md
```
**Known gap:** the `Untitled*.ipynb` scratch files and loose CSV exports in `nsl-kdd/notebooks/` still need to be cleaned up or removed before this is portfolio-facing — no `shared/utils.py` or `config.py` exists yet. A numbered sequence now exists for the multiclass step (step9/step10); the binary-phase notebooks (eda1, shap, missanalysis, etc.) are still unrenamed.

## Phase 2: Multiclass + UNSW-NB15

### Tasks
- [x] Convert existing binary model → multiclass (NSL-KDD has 5 attack types) — `step9_multiclass.ipynb`, 2026-07-25
- [x] SHAP multiclass interpretation (per-class Shapley values) — `step10_multiclass_shap.ipynb`, 2026-07-25
- [ ] Adapt preprocessing for UNSW-NB15 (different feature space)
- [ ] Compare model performance: does NSL-KDD→UNSW-NB15 generalize?
- [ ] Write comparative findings: what's consistent across datasets?

### Model Decision: Tree vs Neural?
**Current plan (tree-based):**
- Random Forest multiclass
- Why: SHAP is native, fast, portfolio-friendly
- Risk: Less "deep learning flex" in portfolio

**Alternative (hybrid — more impressive):**
- RF baseline + 1-2 layer MLP comparison
- Why: Shows you understand interpretability tradeoff (tree=explicit, neural=attention/saliency)
- Risk: More complex, attention mechanism explanation is harder

**[DECISION NEEDED]** — Stick with trees or add neural comparison?

## Data & Preprocessing

### NSL-KDD
- 125,973 samples, 41 features
- Classes: Normal, DoS, Probe, R2L, U2R (multiclass target)
- Current pipeline: [DESCRIBE YOUR PREPROCESSING — e.g., "StandardScaler on numeric, OneHotEncoder on symbolic, handle missing with median"]
- Feature engineering done? [YES/NO — describe if yes]

### UNSW-NB15 (not started)
- ~176k samples, 42 features
- Slightly different attack taxonomy
- Will need feature alignment investigation
- **Preprocessing decisions from dataset-flaw research (2026-07-26, sources in RESEARCH_NOTES.md section 7):** severe class imbalance (Normal 87%, Worms 0.007%) plus real class overlap between Exploits/Fuzzers/Normal — report per-class precision/recall/F1, never just aggregate accuracy. Drop IP/port/timestamp columns before training (infrastructure artifacts, not behavior). Consider using the CIC-UNSW-NB15 re-extraction (unb.ca/cic/datasets/cic-unsw-nb15.html) instead of the raw 2015 release for a cleaner, more standardized feature set.

### CICIDS2017 (not started)
- **Preprocessing decisions from dataset-flaw research (2026-07-26, sources in RESEARCH_NOTES.md section 7):** do not use the raw UNB CICIDS2017 CSVs as-is — CICFlowMeter's flow-construction bug mislabels ~26% of the dataset as attack-class "appendix" fragments, and models have been shown to overfit on those artifacts instead of real attack behavior. Use **LYCOS-IDS2017** (corrected release, lycos-ids.univ-lemans.fr) or Engelen et al.'s relabeled/payload-filtered data instead. Regardless of version used: drop Flow ID/Source-Dest IP/Timestamp columns, and bucket ports into categorical ranges rather than using raw port numbers (models have been shown to shortcut-learn on destination port alone).

## Key Findings (so far)

See RESEARCH_NOTES.md for full detail; summarized here:

- **guess_passwd evasion:** deliberately keeps connection count at 1 to stay under volume/rate-based detection — NSL-KDD's feature set can't distinguish it from normal traffic, so the model misses it (53 train / 1231 test examples).
- **Camouflage vs data starvation confound:** rare attacks (guess_passwd 53 train, warezmaster 20 train) are both under-sampled and behaviorally camouflaged, and the two effects can't be separated without a controlled ablation (planned, not yet run).
- **SHAP "camouflage score" (novel metric):** cosine similarity of an attack type's mean SHAP profile to normal vs. to caught attacks — correlates strongly with recall, i.e. predicts which attack types will be hard to detect before running the model. Not yet formalized/validated across model families or datasets.
- **Behavioral transfer:** unseen-at-train attacks still got partially detected when behaviorally similar to trained ones (saint 99.7%, udpstorm 100%, apache2 65.9%, mscan 67.9% recall) — model generalized on attack *behavior*, not just memorized labels.
- **Within-class imbalance:** overall normal/attack split is fairly balanced (67k/58k), but within "attack" there's a 20,000x range (neptune 41k train vs loadmodule 9 train) that `scale_pos_weight` does nothing to address — this is a likely bottleneck for the rarest classes independent of camouflage.
- **Multiclass confirms + sharpens the above (2026-07-25):** U2R got the highest `sample_weight` of any class (484.5x) and still only hit 0.328 recall — confirms weighting can't fix within-class imbalance (rootkit 0/13, ps 4/15). R2L's zero-recall attack types split into two distinct causes: unseen-in-train (httptunnel, sendmail, named, xlock, worm, snmpguess, snmpgetattack, xsnoop — the model never saw one example) vs. genuinely camouflaged despite training (guess_passwd, 53 train examples, still 0% recall).
- **DoS generalization asymmetry (see RESEARCH_NOTES.md section 10):** DoS's aggregate 0.762 recall hides a split — neptune-pattern DoS (neptune is 89.7% of DoS training data) hits ~99-100%, but unseen application-layer DoS (apache2, mailbomb, processtable, udpstorm — zero training examples) collapses to ~0%, unlike Probe's unseen types (saint, mscan) which held up via behavioral transfer to known scanners.
- **U2R has real signal, not camouflage (see RESEARCH_NOTES.md section 2):** U2R's SHAP beeswarm surfaces genuine, domain-meaningful features (`root_shell`, `num_file_creations` — actual privilege-escalation indicators), unlike R2L's diffuse near-zero signal. Recall is still only 0.328 — with real signal present but only 52 training examples, this looks like data starvation, not camouflage. Clean contrast case against R2L for the planned ablation study.
- **"Normal" is an implicit default class, not a learned one (see RESEARCH_NOTES.md section 11):** every attack family has features that argue *for* it (neptune's flood signature, U2R's root_shell), but `normal`'s top SHAP features are just the attack features with the sign flipped — nothing is uniquely diagnostic *for* normal. This is the unifying mechanism behind both the DoS and R2L findings: the model can't distinguish "this looks like normal" from "this doesn't match anything I've learned," so unfamiliar attacks default to `normal` regardless of whether they actually resemble legitimate traffic.

## Known Blockers

### Performance
- SHAP computation on full NSL-KDD can be slow (50k+ samples)
- **Solution:** Use sample-based SHAP (TreeExplainer is fast, but for large datasets consider sampling)

### Reproducibility
- Need to lock versions: scikit-learn, SHAP, pandas (for portfolio reproducibility)
- **Solution:** Create `requirements.txt` with exact versions

### Multiclass Complexity
- SHAP for multiclass: need separate explanations per class or global?
- **Current plan:** Per-class SHAP values (Shapley values for each attack type separately)

## Decisions Made

1. **Use NSL-KDD first, then UNSW-NB15** → Shows generalization on second dataset
2. **Binary before multiclass** → Simpler story to tell in portfolio
3. **SHAP over LIME for primary explainability** → Better for tree models, cleaner for portfolio narrative
4. **Jupyter notebooks (not scripts)** → More portfolio-friendly, easier to tell the story

## Next Immediate Step
Multiclass model + SHAP are done (`step9_multiclass.ipynb`, `step10_multiclass_shap.ipynb`). Next: clean up `Untitled*.ipynb` scratch files/checkpoints in `nsl-kdd/notebooks/`, then start UNSW-NB15 (data ingest + feature alignment against NSL-KDD's schema). The camouflage-vs-starvation ablation (RESEARCH_NOTES.md section 2) is scoped as a follow-up research task, deliberately after the base project (incl. UNSW-NB15) is further along — not before.

## Resources
- NSL-KDD: [Local path or download source]
- UNSW-NB15: [Local path or download source]
- SHAP docs: https://shap.readthedocs.io/
- Portfolio story outline: [Link to README or narrative doc if exists]

---

**Last Updated:** 2026-07-25
**Status:** Phase 1 complete. Phase 2 multiclass + SHAP complete (step9/step10, 0.7709 accuracy). UNSW-NB15 not started. Notebook cleanup (`Untitled*` scratch files) still pending.
