# Week plan 2026-09-19 → 25 — review, amendments and Day-1 record

Source: [WEEK_PLAN_2026-09-19_TO_25.txt](WEEK_PLAN_2026-09-19_TO_25.txt) (owner-authored, committed
verbatim; revised by the owner 2026-09-20 after equipment purchases, see the revision section below).
This file is the agent's critique, the amendments it proposes, and the day-by-day execution record.
Amendments are proposals until the owner merges this PR; the source text is not edited.

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

## Revision 2026-09-20 — equipment purchased, priorities re-ordered

The owner revised the source plan after purchasing a QT Py RP2040, NAU7802 ADC, 5 kg and 1 kg load
cells, LIS3DH, INA260 and an IR break-beam pair. New workstream E (E0–E6) makes force acquisition and
calibration tooling the must-finish track; nominal CAD extension moves to "next", the controller sweep
to stretch. Findings 1–7 above still hold; the schedule below supersedes the earlier one.

Critique of the revision (verified where a fact is claimed):

| # | finding | amendment |
|---|---|---|
| 8 | **Arithmetic checks out.** 5 kg → 49.05 N, ratio 2.45 at 20 N; 1 kg → 9.81 N cannot reach 12 N; FEA 0.176 mm × 20/128.76 = 0.0273 mm at 20 N; NAU7802 320 SPS → 160 Hz Nyquist < 285.5 Hz. The plan's engineering decisions follow from these. | none |
| 9 | **W1.1 is scheduled for Sep 23 but was delivered Sep 19 in this PR.** The revision says "do not backfill"; nothing is backfilled, the work simply exists. | Sep 23 = W3.1 only; the freed time goes to W3.2. |
| 10 | **E2 serial capture needs `pyserial`, which is not a repo dependency.** | Import it lazily inside the capture path only; replay and tests stay dependency-free, as the plan requires. Pin it in the firmware README, not the portable requirements. |
| 11 | **E1 `py_compile` of CircuitPython code under CPython is syntax-only** (the plan says so). `import board` would fail at runtime on the host. | Keep the compile check; add no host-side import test. The device README owns flash and capture steps. |
| 12 | **E3 and W3.1 must share one estimator.** E3 produces force U95; W3.1 propagates it through the fitted-compliance estimator already in `experiments/mast_physical_validation.py`. | E3 emits a small JSON the W3.1 screen reads; neither reimplements the other. |
| 13 | **The largest physical gap is unchanged by the purchase:** calibrated tip/root displacement indicators and a root-rotation observation. The plan says this; W3.2's ranked inputs should say it first. | Input bundle 1 stays "displacement and root motion" unless the W3.1 sensitivities disagree. |
| 14 | **Inventory schema.** The revision asks for stable IDs and a separate schema from the owner register. | Delivered as `docs/hardware/purchased-instruments.json` (E0); E1–E3 reference those IDs. |

## Amended schedule (equipment-first)

| day | work | stop rule |
|---|---|---|
| 19 | W0.1, W0.2, W1.1 delivered (this PR, first commit) | — |
| 20 | E0 inventory + hookup notes (this PR, second commit) | stop if PR #24/#25 still unmerged on Sep 21: rebase, do not fork |
| 21 | E1 device format + firmware script (NOT DEVICE-TESTED), E2 logger + replay + tests | replay must run with no board and no CadQuery |
| 22 | E3 calibration record, fit, U95 at 4–20 N, synthetic failure cases incl. 1 kg cell at 20 N | no real calibration fields filled |
| 23 | W3.1 feasibility screen importing the existing estimator, force U95 from E3 as an assumed case | missing physical terms stay UNKNOWN |
| 24 | W3.2 top-three input bundles from screen sensitivities; scoped W1.8 report (existing tube + measurement chain) | start W1.2/W1.3 only if all of the above pass |
| 25 | W4 packet, acceptance suite, final PR(s) | none |

Cut order per the revision: W2 sweep, E4–E6, renders/full assembly, then the clamp extension.
Preserved: E0–E3, nominal-tube source review, W3.1, evidence packet.

## Revision 2026-09-21 — shared CAD briefing and native branch reconciled

The owner adopted `500ft/engineering-audit → docs/cad_agent_briefing.md` (decision record
[0001](decisions/0001-shared-cad-workflow.md), indexed by the new `AGENTS.md` / `CLAUDE.md`) and
re-scoped W1.2–W1.5 onto the existing native SOLIDWORKS branch. Checked against the repo:

| # | finding | amendment |
|---|---|---|
| 15 | **`cad/solidworks-mast-assembly` (PR #26, base `17c69c1`) is real and disjoint from #24/#25:** 13 files, tube stock 135 mm, support sleeve, root clamp, CadQuery oracle, separate contract, a recorded 35 → 40 mm redrive with ≤ 1e-15 volume error. No file overlaps the two open PRs. | Merge order becomes #24 → #25 → #26 (or #26 first; either is conflict-free). The nominal work order in #24 is marked superseded in part; CadQuery parts C2–C6 are withdrawn. |
| 16 | **The `nominal_package_parameters.csv` idea from the Sep 20 plan is dropped** in favour of `cad/solidworks/geometry.json` with per-value evidence states. That file already exists on #26. | Finding 14's inventory schema stays separate from both registers; nothing to change in E0. |
| 17 | **The 135 mm stock tube must not inherit `cad/contract.json` or the 285.5 Hz result.** `cad/tests/test_solidworks_assembly_contract.py` on #26 asserts the two contracts differ. | `cad/nominal_inventory.py` gains no SOLIDWORKS rows until #26 is on main; then add the three oracle volumes with label NOMINAL DESIGN and the redrive error as SOFTWARE CHECK. |
| 18 | **Load-path equations (finding 2) still precede clamp extension.** The briefing's "no seating-torque or grip/yield acceptance without joint analysis" is the same requirement. | W1.6 stays first in the "next" tier, before W1.3's slot/bolt-position parametrization. |
| 19 | **E1 driver identity.** The Adafruit guide's CircuitPython driver is `cedargrove_nau7802` (2.1.4, 2026-03-30), not an `adafruit_*` package; API is `gain`, `ldo_voltage`, `poll_rate`, `channel`, `available()`, `read()`, `calibrate()`. | Firmware written against it and pinned in `library-versions.txt` as written-against, not device-tested. |

## Day 3 record (Sep 21, E1 + E2)

- **E1** `firmware/measurement_node/code.py` (NOT DEVICE-TESTED): one NAU7802 channel on the STEMMA
  bus, 10 SPS, gain 128, LDO 3V0, internal calibration; NDJSON session/sample/error records; new
  session ID per boot; saturation flagged at full scale; read errors emitted, re-init after five,
  `missing_device` once a second. `README.md` (conditional owner steps), `library-versions.txt`
  (written-against vs observed columns). `py_compile` passes; that is syntax only.
- **E2** `experiments/measurement_logger.py`: one parser for replay and serial capture; pyserial imported
  only inside capture; outputs `stream.jsonl` (bytes unchanged), `samples.csv` with flags, `diagnostics.json`,
  `manifest.json` (source kind, hashes, commit, `calibration_id: null`, `complete`), `host_times.csv` on
  capture. Fourteen flag classes, records retained never repaired. `source_kind` never upgraded by replay;
  measured replay refuses a hash mismatch; truncated capture exits 3 with `complete: false`.
- Fixtures `experiments/fixtures/measurement_logger/{valid,faults}.jsonl` (synthetic, labelled);
  `experiments/test_measurement_logger.py` 9 tests: clean session, every fault class, determinism, hash
  refusal, missing/corrupt values never interpolated, split serial lines, disconnect, no-data.
- Format: `docs/hardware/measurement-data-format.md`. CI: the two portable commands added to `ci.yml`.
- Context files committed from the owner's clone: `AGENTS.md`, `CLAUDE.md`, `docs/decisions/0001-shared-cad-workflow.md`,
  the Sep 21 plan revision.
- No device connected, no calibration, no register or ledger change.

## Day 4 record (Sep 22, E3)

`experiments/load_cell_calibration.py` (stdlib only), `test_load_cell_calibration.py` (23 tests),
`docs/hardware/load-cell-calibration-protocol.md` (CONDITIONAL, nothing performed), and ten synthetic
fixtures with a README. CI runs the tests.

Three method choices come straight from [literature §4](../literature/04-measurement-uncertainty-and-calibration.md),
merged the same day:

- **Errors-in-variables fit (York), not OLS**, because both axes carry uncertainty. A Monte Carlo test
  over 200 draws shows the OLS attenuation bias and that the York fit removes it. **Scope, measured not
  assumed:** at the NAU7802's expected noise the two agree to within 0.1 %; the fit is the default
  because nothing guarantees that holds.
- **No R² anywhere.** Fit quality is a lack-of-fit versus pure-error decomposition, which the three
  ascending/descending cycles supply replicates for. A test asserts the string never appears in output.
- **Coverage factor from Student's t at the fit's degrees of freedom**, not an automatic k=2.

Fail-closed verdicts: `REFUSED` (missing reference uncertainty, saturation, over capacity, wrong cell for
the range, unreviewed record promoted, mounting changed), `CALIBRATION_INCOMPLETE` (extrapolated level,
hysteresis or zero drift over a predeclared limit, coarse references, missing identity),
`CALIBRATION_USABLE` (the force channel only, explicitly not campaign readiness). Conversion outside the
calibrated count range is refused rather than extrapolated.

Recovery check: the known mapping is recovered to 0.003 % on slope and 0.5 mN on intercept. No cell was
mounted, loaded or measured; every fixture is labelled synthetic and unreviewed.

## Day 2 record (Sep 20, E0)

- `docs/hardware/purchased-instruments.json`: ten line items, stable IDs (MCU-QTPY-01, ADC-NAU7802-01,
  LC-5KG-01, LC-1KG-01, ACC-LIS3DH-01, PWR-INA260-01, GATE-IR-01, cables and wires), all at
  `purchase_identified`; revision, operation, calibration, mounting and wire-colour fields `null` with a
  stated reason; capacity and range arithmetic embedded; five unconfirmed prerequisites listed. No
  invoice, address, order or payment data.
- `docs/hardware/measurement-electronics.md`: evidence ladder, what the purchase changes and does not,
  hookup 1 (QT Py + NAU7802 + 5 kg cell, one board at a time, 3.3 V logic, STEMMA bus distinction),
  the conditional owner check, sources.
- `cad/roboracer/parameters.csv` untouched; the six pending rows stay pending.

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
