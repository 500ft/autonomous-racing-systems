# Progress log

What changed and when, newest first, one line per change that matters. The
plan is in the [roadmap](../ROADMAP.md). The earlier, longer version of this
log, with full entries up to 2026-09-11, is kept at
[commit 51a3bb3](https://github.com/500ft/autonomous-racing-systems/blob/51a3bb3f89be136e7912ef4f7164f713410cc708/docs/SPRINT_PROGRESS.md).

## Week of 2026-09-28

- **09-30** One roadmap to the finish line (build and load-test the mast);
  README rewritten in plain language
  ([#61](https://github.com/500ft/autonomous-racing-systems/pull/61)).
- **09-29** Mast assembly accepted against the CadQuery oracle: part
  placement, volumes, reopen, a move-and-restore test and a STEP round trip all
  match ([#55](https://github.com/500ft/autonomous-racing-systems/pull/55)).
  The first unattended build had the parts in the wrong place
  ([#47](https://github.com/500ft/autonomous-racing-systems/pull/47)).

## Week of 2026-09-21

- **09-26** Tip-mass attachment study. Most of the 13.5% gap between the hand
  calculation (330.1 Hz) and FEA (285.5 Hz) came from hanging the tip mass on
  one wall node; a coupled, centred mass gives 320.9 Hz
  ([#43](https://github.com/500ft/autonomous-racing-systems/pull/43)).
- **09-26** Decision screen for the static test. At 0.3 µm indicator
  repeatability, a full two-axis test passes the fit check about 72% of the
  time. An uncorrected root rotation would leave the fitted stiffness 19.4%
  wrong, so root motion has to be measured
  ([#44](https://github.com/500ft/autonomous-racing-systems/pull/44)).
- **09-26** Root clamp confirmed parametric in width, height and engagement
  ([#48](https://github.com/500ft/autonomous-racing-systems/pull/48)).
  Engineering audit and traceability index
  ([#45](https://github.com/500ft/autonomous-racing-systems/pull/45)).
- **09-24** Fixture feasibility: the mast is 776 N/mm stiff, so the test
  fixture must be at least 7,760 N/mm per axis. The CAD host now runs without
  dialog prompts ([#39](https://github.com/500ft/autonomous-racing-systems/pull/39)).
- **09-24** Critique fixes. The load-cell calibration verdict had ignored its
  own lack-of-fit result; each defect was reproduced before it was fixed
  ([#40](https://github.com/500ft/autonomous-racing-systems/pull/40),
  [#41](https://github.com/500ft/autonomous-racing-systems/pull/41)).
- **09-24** Load-cell calibration tooling: errors-in-variables fit and force
  uncertainty at 4–20 N, tested on synthetic data
  ([#38](https://github.com/500ft/autonomous-racing-systems/pull/38)).
- **09-22** Tube, support sleeve and root clamp authored in SOLIDWORKS and
  checked against a CadQuery oracle
  ([#26](https://github.com/500ft/autonomous-racing-systems/pull/26)).
- **09-22** Bench electronics: instrument inventory, QT Py and NAU7802
  firmware, and a host logger with replay
  ([#25](https://github.com/500ft/autonomous-racing-systems/pull/25)).
  Literature review across the project's five areas
  ([#27](https://github.com/500ft/autonomous-racing-systems/pull/27)).
  Tap-test question closed ([#24](https://github.com/500ft/autonomous-racing-systems/pull/24)).

## Week of 2026-09-14

- **09-15** Day-4 plan revised ([#23](https://github.com/500ft/autonomous-racing-systems/pull/23)).
- **09-14** CAD ledger report fixed; CI checks out full history
  ([#21](https://github.com/500ft/autonomous-racing-systems/pull/21)).

## Week of 2026-09-07

- **09-13** The two fixture-contract checkers merged into one validator, then
  tightened twice ([#18](https://github.com/500ft/autonomous-racing-systems/pull/18),
  [#19](https://github.com/500ft/autonomous-racing-systems/pull/19),
  [#20](https://github.com/500ft/autonomous-racing-systems/pull/20)).
- **09-12** Fixture contract, and a draft modal test protocol that is not frozen
  ([#17](https://github.com/500ft/autonomous-racing-systems/pull/17)).
- **09-11** README and presentation rewrite
  ([#15](https://github.com/500ft/autonomous-racing-systems/pull/15)).
- **09-10** Mast input request sheet; static and modal validation kept apart
  ([#14](https://github.com/500ft/autonomous-racing-systems/pull/14)).
- **09-09** Parametric mast tube generator with geometry CI and a STEP round
  trip ([#13](https://github.com/500ft/autonomous-racing-systems/pull/13)).
  Mast input register ([#12](https://github.com/500ft/autonomous-racing-systems/pull/12)).
- **09-07** CAD part list and plan
  ([#7](https://github.com/500ft/autonomous-racing-systems/pull/7),
  [#8](https://github.com/500ft/autonomous-racing-systems/pull/8),
  [#9](https://github.com/500ft/autonomous-racing-systems/pull/9)).
  Telemetry regression floors set from solver precision
  ([#11](https://github.com/500ft/autonomous-racing-systems/pull/11)).

## Week of 2026-08-31

- **09-06** The mast test evaluator now refuses incomplete measurement sets;
  six developer spot checks match their expected verdicts
  ([#6](https://github.com/500ft/autonomous-racing-systems/pull/6)).
- **09-03** Replay test checks metrics instead of pixels
  ([#2](https://github.com/500ft/autonomous-racing-systems/pull/2)). Fixed a
  module-loading bug that blocked 11 of 15 figure generators
  ([#1](https://github.com/500ft/autonomous-racing-systems/pull/1)).

## Before September

Repository published 2026-08-06 with the simulation work: bicycle-model
identification, controller comparison, EKF, the ROS 2 telemetry bridge and the
mast hand calculations and FEA.
