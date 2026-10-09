# Prior work: withholding a simulated controller ranking

Added 2026-10-09 from the literature review of that date (abstract-level, web
search only, forward citations not searched). Grading scheme: [README](README.md).
BibTeX for the three entries is in [references.bib](references.bib).

Scope: the [roadmap](../ROADMAP.md) question. Can dispersion in the predicted
performance difference between controllers, across physically justified
vehicle models, identify rankings that will reverse on the real car? Three
sources frame it: a formal root, the nearest test of an abstain rule, and the
nearest empirical ground truth.

## Entries

| Citation | Link | Why it matters here | Ab | Ev |
|---|---|---|---|---|
| **Song, E.; Nelson, B. L. (2019). *Input–Output Uncertainty Comparisons for Discrete Optimization via Simulation.* Operations Research.** | [10.1287/opre.2018.1796](https://doi.org/10.1287/opre.2018.1796) | Formal root. Ranking and selection of simulated systems when every system shares the same uncertain input model. The procedure reports which systems cannot be separated under that uncertainty and withholds a choice between them. This repo's dispersion rule is a special case: a physically justified ensemble of vehicle models stands in for the input-distribution uncertainty. | 3 | C |
| Kadir, N. (2026). *RankCert: When Can Simulated Learners Safely Select an AI Tutor? Robust Decision Certification Under Structural Uncertainty.* arXiv:2609.26069. Preprint, single author. | <https://arxiv.org/abs/2609.26069> | Nearest test of an abstain rule. Domain is AI-tutor policies, not vehicles. It certifies a ranking only when several predictively adequate model families agree, otherwise it abstains. Reported result: at comparable coverage the multi-model abstain rule did not reduce selective risk relative to a confidence-gated point certificate, and it certified only 3.75 percent of settings. Consequence here: the dispersion rule must be compared against a confidence-gate baseline at matched coverage, and beating it is the pre-registered success criterion ([roadmap M3](../ROADMAP.md#m3-calibrate-a-controller-difference-abstention-rule)). | 3 | D |
| **Kresse, F. G. (2024). *Deep off-policy evaluation with autonomous racing cars.* Thesis, TU Wien.** | <https://repositum.tuwien.at/handle/20.500.12708/201148> · [code](https://github.com/HyberionBrew/f110_ope_benchmark) | Nearest empirical source and the origin of the archives this repo [qualified](../reports/ope_qualification.md). Publishes a real ranking of 15 controllers under four reward definitions, simulator rollouts of the same 15 from the recorded real start poses, and Spearman rank correlations of its estimators, including model-based ones, against that ground truth. A raw simulator-versus-car ranking reversal rate for F1TENTH is therefore computable from published data. It is the reference calculation for this repo, not a contribution. | 3 | B |

Grades were assigned from abstracts and the published code tree, not from a
full read of each source. Song and Nelson is graded C because the review did
not confirm an experimental validation beyond simulation studies; raise it only
after reading the paper.

## Gap

A physical-platform test of an abstain rule driven by model disagreement was
not found in the 2026-10-09 review (abstract-level, web search only, forward
citations not searched). Kadir 2026 tests the rule on simulated learners. Song
and Nelson 2019 test it on simulated systems. Kresse 2024 supplies real ground
truth but evaluates estimators, not an abstain rule.

## What this changes

Nothing in the data or results. The roadmap's M3 text records the baseline,
the registered prediction and the scope limit added from this review under the
owner instruction of 2026-10-09. The [contact record](../docs/ope_author_request.txt)
summarises the dataset author's reply of the same date.
