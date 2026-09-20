# Nominal CAD/FEA design package — work order (2026-09-16)

Selected under [DAY4_PLAN.md](DAY4_PLAN.md) optional work. Scope: one reproducible package that
reconciles what already exists for the LiDAR mast (register, generated tube, hand calc, FEA,
tolerance stack) and adds the nominal clamp and bracket as **labelled design proposals**. It closes
no ledger row (RR-CAD-02/04/05 stay blocked) and claims no as-built, inspected or physical result.

## What exists on `main` (do not redo)

| artifact | state |
|---|---|
| `cad/roboracer/parameters.csv` | 30 rows; tube L 100 / OD 20 / wall 1.5 mm, 6061-T6 handbook E and ρ, tip 0.175 kg (0.130 body + 0.030 bracket + 0.015 cable); six interface rows pending |
| `cad/generate.py` + `cad/contract.json` + `cad/tests/test_geometry.py` | generates **only** `mast_tube` (plain hollow cylinder); volume 8717.92 mm³, mass 23.5 g; STEP round-trip and negative controls in CI |
| `runs/mast_fea/` | static + modal, 0.175 kg tip: f1 285.5 Hz, crash tip deflection 0.176 mm, gauge 17.4 MPa; mesh convergence < 1.5% |
| `runs/mast_hand_calc/design_sweep.txt` | recommended row: f1 330.1 Hz, SF crash 8.05, σ 34.3 MPa |
| `runs/mast_tolerance_stack/summary.txt` | blind 1.284° FAIL, levelled 0.354° PASS vs 0.458° bound, 40 mm bolt pattern ASSUMED |
| `docs/design/16_mechanical_design_analysis.md` | selected design, load cases, §7 tolerance stack, deck-height limit ≤ 0.138 m |
| `evidence/task-2026-09-09/cad-out/mast_tube.step` | the only STEP in the repo; no DXF, no drawings, no renders |

Two stale records found during this survey, fixed first (package step 0):

- `docs/design/FEA_SETUP.md` still quotes the 0.20 kg tip run (F 147.2 N, f1 267.4 Hz, δ 0.201 mm) while `fea_summary.txt` and the design doc carry the 0.175 kg rerun.
- `runs/mast_hand_calc/summary.txt` prints the rejected baseline (L 120 / OD 16, f1 174.7 Hz FAIL); the recommended geometry lives only in `design_sweep.txt`.

## CAD items to model

All parametric from `parameters.csv` via CadQuery in `cad/generate.py`, one STEP each plus an
assembly STEP, each with a `geometry.json` and a contract entry. Hand-modelled Onshape parts are
not used for the nominal package (access unconfirmed).

| # | part | inputs available now | design choices the package must make and label | owner input that would replace the choice |
|---|---|---|---|---|
| C1 | **Mast tube** | L, OD, wall (register) | none; already generated | mill cert / stock provenance for material basis |
| C2 | **Root clamp + mounting base** (machined split clamp, per fixture-preparation) | tube OD; deck plane ≤ 0.138 m above floor; transponder bay ≥ 8 × 12 cm front half clear | clamp engagement length; clamp bore and slit; bolt count, size, pattern and coordinates in a declared datum; base footprint and deck bolt pattern; base-to-tube squareness tolerance (stack uses 0.500°) | `clamp_engagement`, `clamp_bolt_pitch`, deck-side mating datum, fastener spec |
| C3 | **LiDAR bracket / top interface** | UST-10LX 50 × 50 × 70 mm body, 130 g, 12 V + Ethernet cable | bracket geometry and mass (allowance 0.030 kg); bolt pattern (stack assumes 40 mm, unverified); optical-center offset from tube tip; cable exit and strain relief; whether any heat-sink plate is on the moving mass (manufacturer's 200 × 200 × 2 mm plate = 0.216 kg, exceeds the whole tip allowance; **excluded unless owner confirms**) | `lidar_bracket_bolt_pitch` from the vendor drawing of the purchased revision; `optical_center_offset` measured; weighed bracket and cable |
| C4 | **Mast assembly** (C1 + C2 + C3) | above | load height = optical-center height (0.100 m design choice); mass and CG table; datums A (deck plane), B (tube axis), C (bolt pattern origin) | `actual_load_height` |
| C5 | **Deck interface stub** (only the mating patch, not the deck) | selected chassis wheelbase 0.324 m vs model 0.3302 m (documented deviation, not to be absorbed by a bracket) | stub thickness and mounting height consistent with the 0.120 m assumed deck; keep RR-CAD-03 deck deferred | deck drawing |
| C6 | **Fixture concept sketch** (geometry only, no fixture design claim) | k_specimen 775.98 N/mm → fixture ≥ 7 759.8 N/mm per axis; indicator stations ≤ 0.001 mm; root-rotation baseline 100 mm proposed | station spacing proposal; load-line height; this is a placement study feeding RR-CAD-05, not RR-CAD-05 | `root_rotation_station_spacing`, instrument IDs |

C6 is optional inside this package; include only if C2–C4 finish inside the estimate.

## Design considerations to carry through every part

1. **Modal guard.** f1 ≥ 200 Hz with the assembled tip mass. Every gram added at the tip (bracket, cable, any plate) lowers f1; recompute the hand estimate for the modelled bracket mass and rerun FEA if tip mass moves more than 10 g from 0.175 kg.
2. **Strength.** Crash 50 g × SF 1.5 governs (128.76 N at the load height). Clamp and bracket bolts must carry the root moment M = F × h = 128.76 N × 0.100 m = 12.88 N·m (not the 15.45 N·m of the rejected 120 mm baseline) with a stated preload and joint model; the tube's SF 8.05 is not the assembly's SF until the joints are checked.
3. **Clamp engagement vs root compliance.** The FEA fixes the root ideally. A finite split clamp adds root rotation; the measurement contract shows 50 µrad × 100 mm = 5 µm, the entire 4 N signal. Record the assumed joint stiffness and mark it `model_assumption`.
4. **Sightline stack.** Deck flatness, base-to-tube squareness, bolt preload rocking, scan-plane tilt, mounting datum. Drawing tolerances on C2 and C3 must reproduce or beat the values in `mast_tolerance_stack.py`; if the modelled bolt pattern is not 40 mm, update the stack input and rerun.
5. **Deck height.** Mast-root plane ≤ 0.138 m above floor at the 0.30 m wall; mast length is not a lever (locked by the modal guard), so the clamp base height is the only free variable.
6. **Transponder bay.** ≥ 8 × 12 cm, front half, clear above. The clamp base footprint and cable route must not enter it.
7. **Thermal.** No powered-sensor thermal adequacy is claimed. Decide plate-or-no-plate explicitly; if a plate is required it belongs on the deck, not the moving mass, unless the modal and mass budgets are redone.
8. **Material basis.** 6061-T6 handbook E 68.9 GPa, ρ 2700 kg/m³ stay `model_assumption` until a mill cert exists; do not relabel to make a checker pass.
9. **Wheelbase deviation.** 0.324 m chassis vs 0.3302 m model is documented; no part geometry compensates for it.
10. **Inspection-readiness.** Each drawing names the datum, the critical dimensions the fixture contract will compare (`--geometry`), and which are design-choice vs to-be-inspected, so RR-CAD-02 intake can later fill the six pending rows from these drawings instead of from scratch.
11. **Manufacturability.** Split clamp machinable from bar stock with a single bore and slit; bracket from plate; no printed polymer in the primary load path.
12. **Cable and service.** Ethernet + 12 V exit direction, bend radius, strain relief at the bracket, route past the clamp without entering the bay.

## Package outputs and acceptance

| output | check |
|---|---|
| `cad/generate.py` extended to C1–C5 (one `--part` per family, `--part all` for the assembly) | `python -m pytest cad/tests -q` green in the pinned CadQuery env; contract entries with tolerances for each part; negative controls for each new required parameter |
| `cad/contract.json` entries for C2–C5 | volume, mass, bbox per part; assembly mass and CG within 1e-6 of analytic |
| `cad/roboracer/parameters.csv` new rows for every design choice (state `design_choice`, source = this work order or the drawing) | `cad/input_requests.py --check` and `fixture_contract.py --check` current after `--refresh`; the six pending rows **stay pending** |
| `docs/design/figures/` renders and one dimensioned drawing per part (SVG or PDF from CadQuery/ezdxf) | datums A/B/C on every drawing; design-choice dimensions marked |
| Refreshed `runs/mast_hand_calc/summary.txt` and `docs/design/FEA_SETUP.md` (step 0) | numbers match `fea_summary.txt`; rejected baseline appears only as "rejected" |
| FEA rerun only if tip mass or joint model changes | f1 ≥ 200 Hz, ±15% vs hand, convergence < 5%, same gauge band |
| `docs/design/17_nominal_mast_package.md` report | mass/CG table, load path, stack result, every assumption listed with its register row; states what the package does not establish |

Effort: step 0 about 1 h; C1–C4 with tests and drawings about 6–8 h; C5 1 h; C6 2 h if taken. FEA
rerun about 1 h including the gmsh↔ccx node-permutation check.

## What this package does not do

No fabrication, purchase, or measurement. No change to the ±15%, U95 ≤ 10%, 200 Hz or ≥10× gates.
No modal acceptance band. No closure of RR-CAD-02/04/05/06/07 or any sprint row; the mast assembly
here becomes the RR-CAD-04 candidate only after RR-CAD-02 records replace the labelled choices.
