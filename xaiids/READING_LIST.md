# Reading List — Research Papers for This Project

Built 2026-07-28. Every entry below was checked against a live search before being
included — venue/DOI confirmed where possible. Two papers from the original pasted
list could NOT be verified under their stated titles; they're listed separately at
the bottom, not folded into the main list, so they don't get treated as confirmed
sources by mistake.

## Tier 1 — read before/during UNSW-NB15 and CICIDS2017 (most directly relevant)

1. **Zoghi & Serpen, "UNSW-NB15 Computer Security Dataset: Analysis through
   Visualization"** (arXiv:2101.05067; Security and Privacy, 2024)
   PCA/t-SNE/K-means shows severe class imbalance (Worms = 0.007% of records) and
   genuine feature-space overlap between Exploits/Fuzzers/Normal. Read this before
   touching UNSW-NB15 — it tells you which "model confusion" is actually ambiguous
   ground truth, the same risk already found with NSL-KDD's rare classes.

2. **"An efficient and interpretable intrusion detection framework for
   software-defined networks with multi-class imbalanced data using genetic and
   GAN-based optimization"** (Scientific Reports / Nature, 2026)
   https://www.nature.com/articles/s41598-026-58514-x
   Multiclass + imbalanced + SHAP/LIME/Morris sensitivity on a network IDS —
   methodologically the closest published match to this project's Phase 2 work.
   Worth reading for how they handle class imbalance (GAN augmentation + genetic
   feature selection) as an alternative to this project's sample-weight approach.

3. **"Detecting Cybersecurity Threats by Integrating Explainable AI with SHAP
   Interpretability and Strategic Data Sampling"** (arXiv:2602.19087, Feb 2026)
   Applied directly to CIC-IDS2017. Strategic sampling methodology + automated data
   leakage prevention + SHAP — read this specifically when starting the CICIDS2017
   phase, it's solving the exact sampling/leakage problems that dataset is known for.

4. **Engelen, Rimmer & Joosen, "Troubleshooting an Intrusion Detection Dataset: the
   CICIDS2017 Case Study"** (WTMC 2021)
   CICFlowMeter closes flows on the first FIN packet instead of both sides
   (violates RFC 793), producing ~26% of the dataset as mislabeled TCP-teardown
   fragments; a Random Forest was shown to overfit on those artifact features
   rather than real attack behavior. Mandatory reading before using raw CICIDS2017 —
   published near-perfect scores on it are partly measuring this artifact.

5. **Rosay, Carlier, Cheval & Leroux, "From CIC-IDS2017 to LYCOS-IDS2017: A
   corrected dataset for better performance"** (WI-IAT 2021)
   The fix for #4 — release notes for the corrected dataset to actually use instead
   of the raw UNB CICIDS2017 CSVs.

## Tier 2 — useful context, not urgent

6. **"Evaluating explainable AI for deep learning-based network intrusion
   detection system alert classification"** (arXiv:2506.07882)
   Closest verifiable match to the "explaining alerts to security analysts" paper
   from the original list (title didn't match exactly, but same theme: LSTM + four
   XAI methods — LIME, SHAP, Integrated Gradients, DeepLIFT — for turning model
   output into analyst-facing explanations). Useful for the "so what does this SHAP
   value mean to a human" framing, less useful methodologically since it's deep
   learning, not tree-based.

7. **"NIDS-β*: an explainable large language based framework for contextual
   intrusion resilience in network security"** (Frontiers in AI, 2026)
   https://www.frontiersin.org/journals/artificial-intelligence/articles/10.3389/frai.2026.1746661/full
   Confirmed real. LLM + SHAP + attention for contextual alert explanation, 98.6%/
   97.8% on CIC-IDS2018/UNSW-NB15. Not core-relevant to this project's tree-based
   approach, but a legitimate future-direction idea if you ever want to add an
   LLM-explanation layer on top of the SHAP output.

8. **"XAI FL-IDS: A Federated Learning and SHAP-Based Explainable Framework for
   Distributed Intrusion Detection Systems"** (arXiv:2605.19448)
   Confirmed real. Federated learning + SHAP, 10 clients, Edge-IIoTset dataset.
   Worth flagging: reported accuracy is modest (88.4% train / 88.2% test) — this is
   not a strong benchmark to cite for "state of the art," it's more a proof-of-concept
   for the federated + SHAP combination. Only relevant if you want to explore
   federated learning as a separate research direction later, per your MEMORY.md
   roadmap.

## Could not verify — treat with caution, do not cite without re-checking

- **"Enhancing IoT network security with explainable deep learning-based intrusion
  detection systems"** (claimed Nature, 1D-CNN + SHAP, ~93% F1) — no exact title
  match found in Nature or elsewhere. Closest real papers found instead: "Smart deep
  learning model for enhanced IoT intrusion detection" (Scientific Reports,
  s41598-025-06363-5) and "Interpretable intrusion detection for IoT environments
  using a self-attention-based explainable AI framework" (Scientific Reports,
  s41598-025-23750-0) — neither matches the stated title/numbers exactly. Possible
  the original title was paraphrased or mistranslated; don't cite the 93% F1 figure
  without finding the actual source.

- **"Resilient federated intrusion detection with explainable AI: a robust
  CNN-LSTM architecture for extreme non-IID data distributions"** — no matching
  paper found under this title anywhere in search results. Several adjacent federated
  IDS papers exist (FedXAI, FD-IDS, EdgeDetect) but none match this title. Do not
  cite this one until you can locate the actual source.

## Already in RESEARCH_NOTES.md

Papers #1, #4, and #5 above were already logged in `RESEARCH_NOTES.md` section 7
from the earlier dataset-flaw research pass — this file is the fuller, tiered
version with the rest of the pasted list checked and folded in.
