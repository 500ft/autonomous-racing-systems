# Roadmap

This is the plan for finishing the project. Task-level status lives in
[docs/CAD_TASKS.csv](docs/CAD_TASKS.csv); older sprint history is in
[docs/SPRINT_PROGRESS.md](docs/SPRINT_PROGRESS.md) and
[docs/REVIEW_READY.md](docs/REVIEW_READY.md).

## Finish line

The project is finished when the redesigned LiDAR mast has been built, loaded
on a bench in both axes, and its measured stiffness compared with the as-built
FEA prediction using the [frozen test protocol](docs/specs/mast-physical-validation/design.md).
Any of the analyzer's three outcomes (VALIDATED, DISCREPANCY, INCONCLUSIVE)
counts as finishing, provided the run follows the protocol.

The vehicle software (identification, controllers, EKF, ROS 2 bridge) is
already complete as a simulation study. It only has to stay reproducible.

## Where it stands (2026-09-30)

- Vehicle software: done in simulation. See the [integrated report](reports/final_report.md).
- Mast design: the original 120 mm × 16 mm tube failed the 200 Hz modal limit
  (174.7 Hz). The redesign (100 mm, 20 mm OD, 1.5 mm wall) gives 330.1 Hz by
  hand and 285.5 Hz in FEA.
- The gap between those two numbers is mostly a modelling choice: a coupled,
  centred tip mass gives 320.9 Hz ([attachment study](runs/mast_modal_attachment_20260925/study.json)).
  That model has not been re-converged, so 285.5 Hz is still the reported value.
- CAD: tube, support sleeve and root clamp are parametric SOLIDWORKS parts. The
  three-part assembly was accepted on 2026-09-29 against an independent
  CadQuery model ([#55](https://github.com/500ft/autonomous-racing-systems/pull/55)).
- Test tooling: the compliance analyzer, load-cell calibration code and bench
  logger exist and are tested on synthetic data. Nothing has been measured.

## What's left

| # | Step | Who | Done when |
|---|---|---|---|
| 1 | Confirm the test hardware (RR-CAD-02): load cell and calibration masses, two 0.001 mm dial indicators (tip and root), a bench to clamp to, and the clamp's mating face | Owner | Each item is recorded as available, with model numbers. **Current step.** |
| 2 | Finish the root clamp and sleeve for manufacture: bolt and slot positions driven by parameters, fits from real stock tolerances, drawings | Agent | Drawings and parameter-change tests pass |
| 3 | Design the two-axis test fixture, the load-cell calibration mount and the indicator mounts, sized to the hardware from step 1 | Agent | Fixture CAD accepted against the oracle; FEA only where fixture stiffness affects the reading |
| 4 | Buy and cut the tube (6061-T6), make the clamp, sleeve and fixture, calibrate the load cell | Owner | Parts inspected; calibration record saved |
| 5 | Run the protocol: five loads, x and y, at least three load/unload cycles, root motion measured | Owner, with agent analysis | Analyzer verdict and raw data committed |
| 6 | Update the report, README and portfolio with the measured result | Agent | Merged |

Optional, and none of these block finishing:

- Re-converge the coupled-mass FEA model. If it holds, it replaces 285.5 Hz.
- A modal tap test. It needs its own frozen protocol (RR-S12) first.

## Not in this version

- Deck adapter, LiDAR bracket and electronics tray. These are vehicle
  integration; the bench test does not need them.
- Telemetry from a physical car.
