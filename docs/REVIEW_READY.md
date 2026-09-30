# Review index

What to review, and where each piece of evidence lives. The plan is in the
[roadmap](../ROADMAP.md) and the history in the [progress log](SPRINT_PROGRESS.md).
The earlier, longer version of this index is kept at
[commit 51a3bb3](https://github.com/500ft/autonomous-racing-systems/blob/51a3bb3f89be136e7912ef4f7164f713410cc708/docs/REVIEW_READY.md).

Nothing in this repository has had an independent review yet. "Ready for
review" means only that.

## Review now

1. **Week of 2026-09-19 packet** ([README](../evidence/week-2026-09-19/README.md)).
   Equipment inventory, bench logger, load-cell calibration tooling, fixture
   feasibility and decision screens, the tip-mass attachment study and the
   [W1.8 nominal report](W1_8_NOMINAL_REPORT.md). Verify its file hashes with
   `python3 scripts/build_week_manifest.py --verify`.
2. **Mast assembly acceptance** ([host notes](../cad/solidworks/README.md),
   [result](../runs/mast_assembly_20260929/assembly_result.json)).

Two findings to check first:

- A passing median R² does not mean the test will usually pass. At 0.3 µm
  indicator repeatability a full two-axis test passes the fit check about 72%
  of the time.
- Both frozen numerical gates can pass while an uncorrected root rotation
  leaves the fitted stiffness 19.4% wrong. Measuring root motion is required,
  not optional.

## Reproduce

Start with the [README quick start](../README.md#quick-start). The
[reading guide](START_HERE.md#reproduce-by-environment) covers the other three
environments (CAD, legacy simulation, ROS 2).

## Evidence records

| Folder | What it holds |
| --- | --- |
| [week-2026-09-19](../evidence/week-2026-09-19/README.md) | The packet above, with a hash manifest |
| [item11](../evidence/item11/report.md) | ROS 2 bag conversion regression captures |
| [review-2026-09-09](../evidence/review-2026-09-09/README.md) | Adversarial review of the CAD tooling and the hosted CI check |
| [task-day3-2026-09-09](../evidence/task-day3-2026-09-09/README.md) | Mast input request sheet checks |
| [task-2026-09-09](../evidence/task-2026-09-09/README.md) | Parametric tube generator handoff |
| [task-2026-09-08](../evidence/task-2026-09-08/README.md) | Mast input register |
| [sprint-2026-09-05](../evidence/sprint-2026-09-05/evaluation.md) | Test-evaluator hardening: baseline, failing and passing logs, six spot checks |
| [presentation-2026-09-10](../evidence/presentation-2026-09-10/README.md) | README presentation checks |

## Asking for a review

When a reviewer is available, send them this:

> Please review 500ft/autonomous-racing-systems at the current `main`. Start
> with docs/REVIEW_READY.md and the week-of-2026-09-19 packet. The main
> questions are whether the static-test plan (fixture stiffness, root-motion
> correction, calibration) can produce a trustworthy stiffness measurement,
> and whether the FEA and attachment study support 285.5 Hz as the reported
> first mode. No physical measurement exists yet.
