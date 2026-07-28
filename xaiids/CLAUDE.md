# CLAUDE.md — XAI-IDS

## What We're Trying to Do
Portfolio project proving two things at once: I can build a working intrusion detection classifier, AND I can make its decisions explainable to someone who isn't an ML engineer (a security analyst, a hiring manager). This is the core pitch — not "here's a model with 95% accuracy," but "here's a model I can explain and justify."

Bigger picture: this is a stepping stone in a cybersecurity → ML/AI engineering pivot. It should demonstrate depth in both fields at once — security domain knowledge (what attack types mean, why certain features matter) and ML engineering rigor (clean pipeline, proper evaluation, interpretability tooling).

Two datasets (NSL-KDD, then UNSW-NB15) so the story isn't "it works on one dataset" but "the approach generalizes." Binary first, multiclass next — same reasoning, build the simple story before the complex one.

## Code Rules
- Python 3.9+, scikit-learn + SHAP (primary), PyTorch if going neural
- Complete runnable code blocks, no snippets
- Always include docstrings for functions (input/output shapes)
- Show SHAP evidence for every feature importance claim
- Assume reader doesn't know networking—explain like briefing a CEO

## Output Format
- Lead with findings, then SHAP plots, then "why it matters"
- Model metrics: accuracy, F1, inference time
- For comparisons: "Tree = fast SHAP, neural = visual attention"

## GitHub Repo
Repo path: [INSERT YOUR GITHUB LINK]
- Look here for actual data samples, notebooks, preprocessing logic
- Pull from here when I need context about your pipeline

## Research Notes
Running log of papers, techniques, or ideas worth remembering — not decisions (those go in MEMORY.md), just things I've read or want to try.
- [Add: paper/technique name — one-line takeaway — why it might matter here]
- Example format: "SHAP TreeExplainer paper (Lundberg 2020) — exact Shapley values for trees in polynomial time, not just approximation — relevant since we're tree-based for speed"

