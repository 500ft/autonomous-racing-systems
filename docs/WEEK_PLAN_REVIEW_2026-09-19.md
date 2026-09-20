# Week plan 2026-09-19 → 25 — review, amendments and Day-1 record

Source: [WEEK_PLAN_2026-09-19_TO_25.txt](WEEK_PLAN_2026-09-19_TO_25.txt) (owner-authored, committed
verbatim). This file is the agent's critique, the amendments it proposes, and the Day-1 execution
record. Amendments are proposals until the owner merges this PR; the source text is not edited.

## Verdict

The plan is sound where it matters: separate nominal register, evidence labels on every number,
FEA rerun only on a trigger, no ledger row closed by nominal work, expected refusals recorded as
expected. Seven findings below; three change the order of work, four narrow scope so the week fits.

## Findings and amendments

| # | finding (verified against the repo) | amendment |
|---|---|---|
| 1 | **W1.6 discrepancy is real.** `16_mechanical_design_analysis.md` §3 selected-geometry table said M = 15.45 N·m with h_arm = 0.100 m. 15.45 = 128.76 × 0.120, the rejected baseline's arm; the selected value is 12.88 N·m (σ 34.3 MPa is consistent with 12.88, not 15.45). My own work order repeated it. | Fixed in this PR, pinned by `test_final_report.py`. |
| 2 | **Order of work.** The plan says "equations before numbers" but schedules W1.6 after W1.3–W1.5. Bolt count, size and clamp engagement come out of the load path, so modelling first means remodelling. | Day 2 = W1.2 + W1.6 (API + load-path equations). Day 3 = W1.3 + W1.4. Day 4 = W1.5 + W1.7 + W1.8. |
| 3 | **W2 cannot run in CI.** The closed-loop runner (`gym/roboracer/closed_loop.py`) takes `control_delay_steps` but no plant hook; wheelbase, mass and friction live in the F1TENTH gym `params` dict (`lf`, `lr`, `m`, `mu`). CI has no gym env; only the local `f1tenth-gym` conda env and the Docker image do. | W2.1 adds one `params` pass-through to `run_closed_loop`, nothing more. The sweep runs locally, results and config hash are committed, CI only re-validates the committed CSV (same pattern as every other study). Drop "under 15 min in CI"; keep "under 15 min on a laptop". Sensor dropout: out unless the EKF study already exposes it; do not add a dropout model this week. |
| 4 | **W1.5 cannot claim `MODEL_GEOMETRY_MATCH_ONLY`.** `fixture_contract.py --geometry` compares against the owner register, whose six rows are pending, so it refuses by design. | The nominal assembly is checked only against `cad/contract.json` entries this week. `--geometry` stays an RR-CAD-02 outcome (Day-4 plan A3). |
| 5 | **W3.1 must not reimplement the estimator.** The fitted-compliance estimator and matrix rules already exist in `experiments/mast_physical_validation.py`. | The screen imports and calls it with synthetic inputs; a second estimator is a second source of truth. |
| 6 | **W4.1 orchestrator is premature.** `cad/nominal_inventory.py` (this PR) already writes the manifest with hashes and labels. | Use a command block in the package report plus `nominal_inventory.py --check`. Write a script only if the block passes ten commands. |
| 7 | **No owner slot for the RR-CAD-06/07 staging amendment** drafted in PR #24. Without it A6 stays ambiguous. | Add to the final handoff's owner-input list as item zero: approve or edit the amendment. |

Environment facts checked 2026-09-19: CalculiX `ccx` is in the `fea` conda env and gmsh in `base`,
so W1.7 can run if triggered. `f1tenth-gym` env exists locally. Base `python3` has numpy, so the
hand calc regenerates outside the pinned envs.

## Amended schedule

| day | work | stop rule |
|---|---|---|
| 19 | W0.1, W0.2, W1.1 (this PR) | stop if PR #24 is not merged before Day 2 |
| 20 | W1.2 geometry API, W1.6 load-path equations + tests | stop before CAD if any load-path screen returns UNKNOWN for a reason that is not an owner input |
| 21 | W1.3 clamp, W1.4 bracket | stop before drawings if bolt demand exceeds a plausible M4/M5 group without preload data |
| 22 | W1.5 assembly + deck stub, W1.7 trigger check, W1.8 report + figures | FEA rerun only on the documented trigger |
| 23 | W2.1 matrix + `params` hook, W2.2 sweep (local) | freeze config hash before first run |
| 24 | W2.3 report, W3.1 screen, W3.2 top-three inputs | rank inputs from screen sensitivities, not opinion |
| 25 | W4.2 packet, full acceptance suite, final PR(s) | none |

Cut order unchanged: renders, C6 sketch, extra controller cases, ponytail audit.

## Day 1 record (W0.1, W0.2, W1.1)

W0.1 — main `17c69c1` (PR #23). PR #24 head `85c12f4` is open, so this branch starts from it as a
dependency, per W0.1. Worktree clean before edits; ledgers, register and request sheet unchanged.

W0.2 — `cad/nominal_inventory.py` writes `runs/nominal_package_inventory/inventory.json`: 14 artifact
hashes, 24 headline numbers each with source file, unit and label, the 6 owner-pending register rows,
and the three stale-record checks. `--check` fails on drift or a headline that no longer appears in
its source; a negative control (banner removed from the hand-calc summary) fails as intended.

W1.1 — three stale records corrected, none deleted:

- `docs/design/16_mechanical_design_analysis.md`: selected-table moment 15.45 → 12.88 N·m with the
  arithmetic shown; the baseline table keeps 15.45.
- `docs/design/FEA_SETUP.md`: workflow text no longer hard-codes 0.20 kg / 147.2 N; a "Current result
  (0.175 kg)" section points at `fea_summary.txt`; the 2026-06-25 table is retitled SUPERSEDED.
- `experiments/mast_hand_calc.py`: summary now opens with a REJECTED BASELINE banner naming the
  selected design; regenerated `summary.txt` (2 lines added) and `design_sweep.txt` (byte-identical).
- `experiments/test_final_report.py`: one new test pins all three plus `F=128.8 N` in the FEA summary.

No physical claim changed. No ledger row changed. RR-CAD-02/04/05/06/07, RR-S02/09/12/13 blocked.

## Checks run (Day 1)

```
python3 cad/ledger_validator.py live            PASS live: 10 tasks; 9 invalid mutations rejected; links OK
python3 cad/input_requests.py --check           consistent
python3 cad/fixture_contract.py --check         derived_from_register current
python3 cad/fixture_contract.py --check-draft   DRAFT_BLOCKED (exit 0)
python3 cad/modal_freeze.py --check-draft       DRAFT_BLOCKED (exit 0)
python3 cad/fixture_contract.py --release       exit 2, expected
python3 cad/modal_freeze.py                     exit 2, expected
PYTHONPATH=gym python3 experiments/test_final_report.py   7 tests OK
python3 cad/nominal_inventory.py --check        OK 14 artifacts, 24 headlines, 6 owner-pending
git diff --check                                clean
```

Not run: pinned CadQuery tests (no geometry changed), FEA (no trigger), legacy Gym (no sim change).
