# Research Notes — XAI-IDS Project

Open questions, limitations, and research directions discovered during this project.
Each note links back to where it surfaced in the analysis pipeline.

---

## 1. Low-and-Slow Attack Detection via Temporal Sequencing

**Where it surfaced:** Step 6 (guess_passwd case study), Step 8 (local SHAP)

**The problem:** Credential brute-force attacks like guess_passwd deliberately keep connection counts at 1 to evade rate-based detection. NSL-KDD's feature set (volume and rate statistics) cannot distinguish a single failed login from normal failed traffic. The model sees count=1 and immediately classifies as normal.

**Why it matters:** Real-world IDS systems need to detect attacks that operate below the volume/rate noise floor. Current benchmark datasets (NSL-KDD, UNSW-NB15) don't provide the temporal or authentication-log features needed to detect these.

**Research direction:** Develop features that capture temporal *patterns* rather than just rates — e.g. "N failed login attempts from same source within M minutes" or "authentication log correlation across time windows." These require dwell-time context not available in single-connection records.

**Relevant papers to explore:**
- [Add: paper name on authentication anomaly detection — detection via login attempt sequencing — matters because credential attacks are widespread in real networks]
- [Add: paper name on temporal network analysis — feature engineering for time-series network data — matters because NSL-KDD loses temporal context]

---

## 2. Camouflage vs Data Starvation Separation

**Where it surfaced:** Section 7 (Discussion), when discovering guess_passwd has 53 train vs 1231 test examples

**The problem:** When a model misses an attack, you can't immediately attribute it to feature-space camouflage (genuine evasion) vs data starvation (model never saw enough examples). guess_passwd shows both symptoms simultaneously, and they're confounded.

guess_passwd: 53 training examples. warezmaster: 20 training examples. These are 23x and 47x gaps respectively. A model that saw 53 examples of something will naturally be worse at detecting it than something it saw 41,000 times (neptune).

**Why it matters:** Separates two distinct problems requiring different solutions. Camouflage suggests you need different features. Data starvation suggests you need more training data or better sampling strategies.

**Research direction:** Controlled ablation study — systematically vary training set size for a single attack type and measure recall vs sample count. If recall plateaus early, camouflage is dominant. If it climbs steadily, starvation was the bottleneck. Repeat for multiple attack types to build a taxonomy of which attacks are camouflaged vs starved.

**Relevant papers to explore:**
- [Add: SMOTE — synthetic minority oversampling technique — improves minority class performance via synthetic examples — matters because NSL-KDD is imbalanced and can't tell if misses are due to lack of examples]
- [Add: sample complexity in adversarial settings — how many examples needed to learn an evading attack — matters because we don't know if 53 examples of guess_passwd were enough]
- [Add: learning curves for imbalanced classification — empirical study of sample size vs recall — matters to understand the guess_passwd gap specifically]

**Concrete instance found (multiclass SHAP, 2026-07-25):** U2R looks like a clean example of the *starvation* side of this question, as opposed to R2L's *camouflage* side. U2R's SHAP beeswarm surfaces genuinely meaningful, domain-specific signal — `root_shell` and `num_file_creations`, literal privilege-escalation indicators, not statistical proxies (a correctly-predicted waterfall example shows `root_shell=1` contributing +1.35 on its own). That's real signal, unlike R2L where every feature stays diffuse near zero regardless of value. Yet U2R recall is still only 0.328 with only 52 training examples. With real signal demonstrably present, the bottleneck looks like insufficient examples to learn it reliably — not feature-space camouflage. This sets up a clean natural experiment for the ablation proposed below: vary training size for a family with a demonstrably real signature (U2R) vs. one with demonstrably weak signature (R2L), and compare how recall responds to more data in each case.

---

## 3. SHAP Camouflage Score as a Predictive Metric

**Where it surfaced:** Step 8 (local SHAP, camouflage scoring function)

**The finding:** Computing mean SHAP profiles per attack type and measuring cosine similarity to normal traffic vs caught attacks yields a "camouflage score" that correlates strongly with recall. High camouflage score predicts low recall almost monotonically.

Camouflage score = sim_to_normal - sim_to_caught

This is not a published technique — it's a logical extension of SHAP analysis — but it works empirically.

**Why it matters:** Provides an *explainable* metric for predicting which attack types will be hard to detect before even running the model. Could be used as a dataset evaluation tool: "this dataset's attack types are camouflaged according to [metric]."

**Concrete instance confirming this (re-verified from the raw force-plot data, not just the summary chart):** a `guess_passwd` row explained in `wf_guess_passwd.png` gets `f(x) = -7.512` (model's raw margin, strongly "normal"). A genuinely normal row explained in `wf_correct_normal.png` gets `f(x) = -5.431`. The model is *more* confident the guess_passwd row is normal than it is about an actual normal row — not a borderline miss, a confident wrong answer. Both top contributing features for that guess_passwd row (`src_bytes=129` → -2.84, `dst_host_srv_count=255` → -2.75) point the same direction real normal traffic does. This is the single clearest instance-level data point for the camouflage claim in the whole project.

**Research direction:** Formalize this as a proper metric. Does it generalize to other datasets (UNSW-NB15, CICIDS2017)? Does it work for other model families (tree vs linear vs neural)? Is it theoretically justified (does cosine similarity in SHAP space have a principled interpretation)?

**Relevant papers to explore:**
- [Add: SHAP for model introspection — using SHAP beyond feature importance to understand decision patterns — matters because we're using SHAP to compare attack similarity, not just explain individual predictions]
- [Add: adversarial examples in network traffic — how attacks evade in feature space — matters because camouflage score is measuring a form of adversarial evasion]

---

## 4. Behavioral Transfer Between Attack Families

**Where it surfaced:** Step 4 (generalization gap), when saint and mscan had high recall despite being unseen

**The finding:** Several unseen attack types still got partially detected: saint 99.7%, udpstorm 100%, apache2 65.9%, mscan 67.9%. These attacks were never in training data but share behavioral patterns with attacks that were (e.g., saint and mscan are scanners like ipsweep and portsweep).

This means the model learned something about *attack behavior* that transferred across types, not just memorized labels.

**Why it matters:** Suggests generalization to novel attacks is possible if you engineer features around behavioral signatures rather than attack-type-specific patterns. Could improve real-world deployment.

**Research direction:** Identify what behavioral properties make attacks transferable. Is it the communication pattern (one connection vs many)? The service targeted (common vs rare)? The error rate? Deliberately engineer features that capture these abstractions and test whether they improve generalization to held-out attack types.

**Relevant papers to explore:**
- [Add: transfer learning in cybersecurity — leveraging patterns from known attacks to detect novel ones — matters because we observed transfer happening implicitly in tree models]
- [Add: attack taxonomy and feature engineering — designing features around attack primitives not attack names — matters to capture behavioral transfer explicitly]
- [Add: domain adaptation for IDS — adapting detectors to new attack landscapes — matters because real deployments face novel attacks constantly]

---

## 5. Adversarial Robustness of IDS Models

**Where it surfaced:** Step 6 (guess_passwd), Step 7 (discussion), when recognizing guess_passwd is an adversarial attack on the feature space

**The problem:** guess_passwd is essentially an adversarial input crafted to minimize the SHAP signal on the model's top features. It deliberately keeps count=1 (the feature that normally screams DoS), targets high-traffic services (the feature that signals normal), uses moderate bytes (doesn't trigger byte-volume alarms). It's optimizing against the model's known decision boundaries.

This is adversarial ML, except the adversary is a real attacker, not a researcher.

**Why it matters:** IDS models are deployed against adversaries who actively try to evade them. Understanding guess_passwd as an adversarial attack formalizes the threat model.

**Research direction:** Pose IDS evasion as an adversarial optimization problem. Can you generate synthetic guess_passwd-like attacks by minimizing SHAP signal on top features? Does the resulting synthetic attack actually work (fool the model)? Can you defend against it by training on adversarially crafted examples (adversarial training)?

**Relevant papers to explore:**
- [Add: adversarial examples in ML — generating inputs to fool classifiers — matters because credential brute-force is an implicit adversarial attack]
- [Add: robustness of tree models to adversarial inputs — are tree ensembles more/less robust than neural nets — matters for IDS deployment choices]
- [Add: evasion attacks on IDS systems — literature on network-based evasion — matters to ground guess_passwd in the broader adversarial ML context]

---

## 6. Within-Attack-Type Imbalance vs Overall Imbalance

**Where it surfaced:** Step 9 (multiclass), when discovering the training distribution

**The problem:** NSL-KDD's class imbalance has two levels:

- **overall:** normal (67k) vs attack (58k) — fairly balanced
- **within attack:** neptune (41k) vs sqlattack (2) — four orders of magnitude

`scale_pos_weight` only addresses the overall binary imbalance. It does nothing about the 20,000x gap between neptune and loadmodule (9 examples).

This means rare attack types were systematically under-represented during training, making data starvation and camouflage impossible to separate for them.

**Why it matters:** Explains why warezmaster (20 train, 944 test) and guess_passwd (53 train, 1231 test) are so hard — not just because they're camouflaged, but because the model was barely trained on them.

**Research direction:** Develop sampling strategies that account for within-class imbalance. Class-balanced sampling? Adaptive resampling per epoch? How does this interact with SMOTE or other oversampling techniques?

**Relevant papers to explore:**
- [Add: loss weighting for imbalanced multiclass — scaling loss per-class for skewed distributions — matters because standard class weights don't capture the neptune-vs-sqlattack gap]
- [Add: curriculum learning in imbalanced settings — training on rare classes early — matters to give the model meaningful exposure to attack types it barely sees]

**Confirmed (multiclass model, 2026-07-25):** U2R received the highest `sample_weight` of any class (484.5x, vs. DoS's 0.5486) and still only reached 0.328 recall — rootkit 0/13, ps 4/15, xterm 5/13, buffer_overflow 8/20. Directly validates this note's prediction: balancing loss across the 5 families does nothing for the imbalance *within* a family. See section 10 for the related but distinct DoS finding.

---

## 7. Generalization to Modern Datasets

**Where it surfaced:** Step 4 (generalization gap), Step 8 (discussion)

**The observation:** NSL-KDD is from 1999. The attack landscape has changed dramatically. Whether the findings here (volume/rate blindness, behavioral transfer, camouflage via low-count evasion) hold on modern datasets is an open question.

UNSW-NB15 is newer (2015) and has more realistic traffic. CICIDS2017 is even more realistic but large and noisy.

**Why it matters:** Determines whether this project's insights are specific to NSL-KDD's quirks or reflect fundamental IDS challenges.

**Research direction:** Repeat this analysis on UNSW-NB15 and CICIDS2017. Do the same attack types get missed? Do the top features change? Does the volume/rate blind spot persist? This is the next phase of the project.

**Relevant papers to explore:**
- Zoghi & Serpen, "UNSW-NB15 Computer Security Dataset: Analysis through Visualization" (arXiv:2101.05067; Security and Privacy, 2024) — PCA/t-SNE/K-means analysis shows severe imbalance (Worms = 0.007% of records) and genuine class *overlap* between Exploits/Fuzzers/Normal in feature space — matters because some UNSW-NB15 "model confusion" may reflect ambiguous ground truth, not model weakness, the same risk this project already found with NSL-KDD's rare classes.
- Engelen, Rimmer & Joosen, "Troubleshooting an Intrusion Detection Dataset: the CICIDS2017 Case Study" (WTMC 2021) — CICFlowMeter closes flows on the first FIN packet instead of both sides (violates RFC 793), producing ~26% of the dataset as mislabeled TCP-teardown fragments; a Random Forest was shown to overfit on those artifact features rather than real attack behavior — matters because published near-perfect CICIDS2017 scores are partly measuring memorized artifacts, not detection ability, directly relevant to this project's own "is the model finding real signal or a shortcut" question (see sections 3 and 11).
- Rosay, Carlier, Cheval & Leroux, "From CIC-IDS2017 to LYCOS-IDS2017: A corrected dataset for better performance" (WI-IAT 2021) — found duplicate and miscalculated CICFlowMeter features, released a corrected dataset (LYCOS-IDS2017) — matters as the direct fix path when this project reaches CICIDS2017, instead of using the raw UNB release.
- [Add: dataset shift in cybersecurity — how real-world traffic differs from benchmarks — matters because datasets aren't representative]

---

## 8. Feature Engineering for Temporal Context

**Where it surfaced:** Step 1-2 (EDA), throughout, implicit in the camouflage findings

**The limitation:** NSL-KDD's features describe a single connection record in isolation. There's no temporal context — you don't know if this is connection #1 or #1000 from this source, or whether the last connection was 1 second or 1 hour ago.

This is why attacks like guess_passwd (which exploit temporal patterns across multiple connections) are invisible.

**Why it matters:** Real IDS systems operate on streaming data and can maintain state across connections. NSL-KDD throws that away.

**Research direction:** Augment NSL-KDD-style features with temporal windows. For each connection, compute rolling statistics over the past N connections from the same source/service pair. Does this surface guess_passwd? What window sizes matter?

**Relevant papers to explore:**
- [Add: stream mining for IDS — detecting patterns in continuous connection streams — matters because real IDS sees sequences, not isolated records]
- [Add: stateful intrusion detection — maintaining per-source state — matters for slow attack detection]

---

## 9. Explainability as a Model Selection Criterion

**Where it surfaced:** Throughout (Step 5-10), implicit in SHAP analysis

**The observation:** XGBoost was chosen partly because it's fast to train, but also because SHAP works well with tree models. Linear models are more explainable (simpler to understand), but tree models are more powerful for this data. The trade-off was resolved by using SHAP to explain the black-box tree model.

But this is a design choice, not inevitable. What if you forced a linear model via feature engineering? What if you used neural networks with SHAP?

**Why it matters:** Explainability shouldn't be an afterthought. It should influence model selection from the start.

**Research direction:** Design IDS models where explainability is a first-class constraint, not a post-hoc patch. What do you lose in predictive power if you insist on linear or tree-depth-limited models? Can SHAP on neural networks match the insights from SHAP on trees?

**Relevant papers to explore:**
- [Add: explainability-accuracy trade-offs — can you have both in IDS — matters for deployment where both detection and trust matter]
- [Add: inherently interpretable models for cybersecurity — designing interpretable-by-design classifiers — matters to avoid the "black box detector" problem]

---

## 10. DoS Family Generalization Asymmetry (Multiclass)

**Where it surfaced:** Step 9 (`step9_multiclass.ipynb`), 2026-07-25, while breaking down the multiclass model's per-family recall.

**The finding:** DoS's aggregate recall (0.762) hides a sharp split. Classic volumetric DoS types — `neptune`, `smurf`, `back`, `teardrop`, `pod` — hit ~99-100% recall. But `apache2` (4/737 = 0.5%), `mailbomb` (0/293), `processtable` (0/685), and `udpstorm` (0/2) are essentially all missed, and almost all of that goes to the `normal` prediction rather than another attack family (confusion matrix: DoS→normal = 1681 vs. DoS→Probe = 91, ~18x skew).

Verified via direct count on `KDDTrain.txt`: `neptune` alone is 41,214 of DoS's 45,927 training examples (89.7%). `apache2`/`mailbomb`/`processtable`/`udpstorm` have **zero** training examples. The model's learned concept of "DoS" is essentially neptune's volumetric-flood signature (high `count`, high `serror_rate`); the missed types are behaviorally different — slow, application-layer resource exhaustion, not packet floods — so there's no feature-level resemblance for the model to generalize from.

**Why it's surprising:** section 4 of this doc already documented "behavioral transfer" — Probe's unseen-in-train types (`saint`, `mscan`) got caught anyway because they behave like known scanners (`ipsweep`/`portsweep`). That pattern does **not** repeat for DoS. And it's not just "unseen attacks are hard" in general — the *binary* model (the one behind `missanalysis.ipynb`) already caught these same DoS types reasonably well (`apache2` 65.9% recall, `udpstorm` 100% recall, per section 4). So going from binary → multiclass, the model didn't just fail to assign the right family to `apache2`/`udpstorm` — it lost the ability to flag them as anomalous at all.

**Working hypothesis:** behavioral transfer isn't universal, it depends on how behaviorally *homogeneous* a family's known training members are. Probe's known members (`satan`, `ipsweep`, `portsweep`, `nmap`) all do fundamentally the same thing — touch many ports/hosts systematically — so "scanning behavior" is one coherent, tool-agnostic signature the model can learn once and generalize across variants. DoS's taxonomy groups attacks by *attacker intent* ("deny service"), not by feature-space behavior — volumetric floods and application-layer exhaustion are mechanically nothing alike, so a model trained almost entirely on neptune's flood signature has nothing to transfer from when it meets apache2.

**Why it matters:** suggests you could predict, before testing, which attack families will generalize to unseen variants and which won't — by measuring within-family behavioral variance among the *known* training members. High variance (like DoS) → don't expect transfer. Low variance (like Probe) → transfer is plausible.

**Research direction:** formalize "within-family behavioral homogeneity" as a measurable quantity (e.g. variance of SHAP profiles or raw feature profiles across a family's training members) and test whether it actually predicts recall on that family's unseen-in-train members, across NSL-KDD and eventually UNSW-NB15.

**Relevant papers to explore:**
- [Add: attack taxonomy critique — does grouping by attacker intent vs. by network behavior change what's learnable — matters because NSL-KDD's DoS/Probe/R2L/U2R labels are intent-based, not behavior-based]
- [Add: within-class variance as a generalization predictor — literature on when transfer learning works vs. fails based on source-class diversity — matters to formalize the hypothesis above]

---

## 11. "Normal" as an Implicit Default Class (Structural Blind Spot)

**Where it surfaced:** Step 10, comparing the `normal` SHAP beeswarm against the attack-class beeswarms — but it's actually the unifying mechanism behind section 10's DoS finding and the original R2L camouflage finding, not a separate one-off.

**The finding:** every attack class here has features that argue *for* it. DoS has neptune's volumetric-flood signature (`count`, `flag`). U2R has `root_shell`/`num_file_creations` — genuine privilege-escalation indicators. `normal` doesn't have an equivalent positive signature: its top SHAP features (`dst_host_srv_count`, `src_bytes`) are the *same* features driving the attack classes, just flipped in sign. Nothing is uniquely diagnostic *for* normal the way `root_shell` is uniquely diagnostic for U2R.

**Why it matters:** in this softmax multiclass setup, that means `normal` functions less like a learned class and more like a leftover bucket — whatever doesn't strongly match one of the specific learned attack signatures falls into it by default. That's a meaningfully weaker bar for an attacker to clear than "statistically resemble real normal traffic." `apache2` wasn't called normal because it successfully disguised itself as legitimate web traffic — it was called normal because it simply didn't match neptune's flood pattern, and there was no separate check verifying "does this actually look like real normal traffic" to catch that gap. This is also the unifying explanation for why `guess_passwd` (genuine camouflage — it actively resembles normal) and `apache2`/`mailbomb` (genuinely different behavior, just never learned) both land in the same bucket for entirely different reasons: the architecture has no way to distinguish "this looks like normal" from "this doesn't look like anything I know."

**Research direction:** if class probabilities were available (the `multi:softmax` vs `multi:softprob` tradeoff already flagged in the model config), check whether misclassified-as-normal attacks get a *confident* normal prediction (model actively fooled) vs. a low-confidence one (model uncertain, sitting at a boundary) — those are different severities of the same failure. Also worth testing architecturally: does a two-stage design — a dedicated binary "is this anomalous at all" gate trained explicitly on genuine normal traffic, followed by a family classifier only for whatever gets flagged — produce a real, positive `normal` signature instead of a leftover one? That's a different model architecture to test, not just a hyperparameter change.

**Relevant papers to explore:**
- [Add: open-set recognition / out-of-distribution detection — models correctly saying "I don't recognize this" instead of defaulting to a known class — matters because this is exactly the capability missing for `normal` here]
- [Add: hierarchical/cascade classifiers for IDS — binary anomaly gate followed by family classification — matters as a direct architectural fix to test against the current flat 5-way softmax]

---

## Summary Table: Papers to Explore

| Topic | Paper Name | One-Line Takeaway | Why It Matters Here |
|-------|-----------|-----------------|-------------------|
| Temporal anomaly detection | [TBD] | Detect attacks via login attempt sequences over time | Guess_passwd is invisible without temporal features |
| SMOTE & oversampling | Chawla et al., SMOTE (2002) | Generate synthetic minority examples to balance training | Warezmaster has 20 training examples vs 944 test |
| Sample complexity | [TBD] | How many examples does a model need to learn an attack | Separating data starvation from camouflage |
| Transfer learning in cybersecurity | [TBD] | Leveraging patterns from known attacks for novel detection | Saint/mscan have high recall despite being unseen |
| Adversarial examples in networks | [TBD] | Generating inputs that fool IDS systems | Guess_passwd is an adversarial attack on feature space |
| Stream mining for IDS | [TBD] | Detecting patterns in continuous connection streams | NSL-KDD loses temporal context of connections |
| Dataset evaluation for cybersecurity | [TBD] | Benchmarking dataset properties and limitations | NSL-KDD is 1999, does it still reflect real attacks |
| Explainability-accuracy trade-offs | [TBD] | Measuring cost of interpretability | Tree models + SHAP vs linear + simplicity |

---

## Next Steps for Research

1. **Immediate (this project):**
   - Run SMOTE oversampling on training data, measure recall improvement on data-starved attacks
   - Repeat analysis on UNSW-NB15, check if findings generalize
   - Formalize camouflage score metric and test on other model families
   - Test the within-family behavioral homogeneity hypothesis (section 10): does it predict which families generalize to unseen attack types?

2. **Medium-term:**
   - Controlled ablation: vary training set size per attack type, measure sample complexity
   - Adversarial optimization: can you generate attacks by minimizing SHAP signal on top features?
   - Temporal feature engineering: add rolling statistics to NSL-KDD features, rerun analysis

3. **Long-term:**
   - Survey: document which attacks are camouflaged vs starved across multiple datasets
   - System design: build an IDS where explainability constrains model selection
   - Deployment study: test on real network traffic, see if temporal blindness persists
