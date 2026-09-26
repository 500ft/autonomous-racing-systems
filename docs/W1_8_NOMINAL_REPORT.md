# W1.8 — nominal mast report (scoped)

## Scope, stated first

This covers **the frozen nominal tube and the assumed static measurement chain**. Nothing else.

It is a **scoped deliverable, not the whole of W1.8**. The original W1.8 acceptance expected a nominal
package including clamp, bracket, assembly and drawings. Those parts are blocked on RR-CAD-02 inputs
that do not exist, so they are absent here and the parent requirement **remains partial**. This report
does not rename a full package into a nominal report and close the original item.

No assembly, fabricated fixture, inspected register, campaign or hardware-safe frequency claim follows
from anything below.

## Claims, evidence, limitations

| Claim | Evidence | Limitation |
|---|---|---|
| Tube geometry and material: 100 mm free length, 20 mm OD, 1.5 mm wall, 6061-T6 | [`parameters.csv`](../cad/roboracer/parameters.csv) | Geometry is `design_choice`; E and ρ are `model_assumption` handbook values. Not a mill certificate — EN 10204 Type 3.1 is what would document the purchased stock |
| Specimen stiffness 775.9837 N/mm, compliance 1.2887 µm/N | Independent recomputation in [`fixture_feasibility.py`](../cad/fixture_feasibility.py), matching [`CAD_MEASUREMENT_CONTRACT.md`](CAD_MEASUREMENT_CONTRACT.md) | Euler–Bernoulli hand model of an ideal built-in cantilever. Not measured |
| Crash case governs strength: 128.76 N, σ 34.3 MPa, SF 8.05 | [`design_sweep.txt`](../runs/mast_hand_calc/design_sweep.txt) | **Tube only.** No bolted-joint analysis exists, so this is not an assembly safety factor. The 50 g shock level is `model_assumption` |
| Root bending moment 12.88 N·m for the selected geometry | [`16_mechanical_design_analysis.md`](design/16_mechanical_design_analysis.md) | Corrected 2026-09-19; 15.45 N·m belongs to the rejected 120 mm baseline |
| Historical FEA: first mode 285.5 Hz, tip deflection 0.176 mm, gauge stress 17.4 MPa | [`fea_summary.txt`](../runs/mast_fea/fea_summary.txt) | **SIMULATION OUTPUT of one specific model definition.** Retains its original provenance and was not regenerated |
| Mesh convergence under 1.5 % at final refinement | [`mesh_convergence.txt`](../runs/mast_fea/mesh_convergence.txt) | A bare delta: no observed order of convergence and no Grid Convergence Index safety factor |
| Sightline: blind assembly 1.284° fails a 0.458° bound; 0.354° after a levelling step | [`summary.txt`](../runs/mast_tolerance_stack/summary.txt) | No drawings exist, so no datum reference frame anchors the contributors. One contributor, the 40 mm bolt pattern, is `ASSUMED` |
| **The hand/FE gap was mostly an attachment artifact** (lands with PR #43) | [modal audit](design/MODAL_MODEL_AUDIT.md); solver evidence at `runs/mast_modal_attachment_20260925/study.json`, which arrives with PR #43 | Attachment model +10.97 %, position +1.27 %, residual −2.79 % vs the hand calc. **No frequency adopted**: a new coupling invalidates reuse of the existing convergence evidence |
| Feasibility of the compliance campaign | [decision screen](../evidence/week-2026-09-19/decision_screen/) | **UNKNOWN by default** — no fixture exists, so its stiffness is undeclared on both axes. Every sensitivity result is an explicitly assumed operating point |

## Electronics and software: what passed, and what it does not establish

| Passed | Does not establish |
|---|---|
| `test_measurement_logger` — replay determinism, 14 fault classes, split serial lines, disconnect | That any board ran. Replay is not acquisition |
| `py_compile` on the CircuitPython firmware | That CircuitPython executes it, that the driver API matches, or that a sensor responded. **NOT DEVICE-TESTED** |
| `test_load_cell_calibration` — known affine mapping recovered to 0.003 %, every fault class refused | That any cell was mounted or loaded. All fixtures are `source_kind: synthetic`, `reviewer_state: unreviewed` |
| `test_fixture_feasibility`, `test_modal_attachment`, `test_unattended` | Physical stiffness, an installed instrument chain, or a verified host toggle |
| CalculiX solve of three declared modal models | A physical frequency, an as-built reference, or assembly modal validation |

## The result that most changes the next decision

The adverse root-rotation scenario applies a synthetic 0.00025 mm/N uncorrected, load-proportional
rotation. It produces a **19.4 % slope bias while median R² is 0.9947 and relative U95 is 3.3 %** —
**both frozen numerical gates pass and the answer is 19 % wrong.**

Low scatter and good linearity do not establish an accurate compliance estimate, and no number of
repeats detects this. Root-motion observability is therefore a correctness requirement on the
apparatus, not a refinement, and it cannot be recovered by a better fit statistic. See the
[adequacy proposal](decisions/compliance-adequacy-proposal.md), which says so explicitly.

## Remaining inputs

| Need | Blocks | Route |
|---|---|---|
| Installed displacement and root-motion chain | replaces the assumed repeatability and rotation terms; decides observability | [Bundle A](../evidence/week-2026-09-19/decision_screen/input_requests.md) |
| Force-chain calibration records | replaces the shared-gain assumption; lets E3 be evaluated | Bundle B |
| Six pending register values and interface drawings | RR-CAD-02, and the geometry and fixture tasks behind it | Bundle C |
| Host run with `applied: true` | confirms the unattended dimension-prompt toggle | one bench session |
| Device bench session | firmware execution and a real calibration | owner |
| Inspected as-built reference, uncertainty, approved band | RR-S12 | owner |
| Readiness records and a named reviewer | RR-S02, RR-S09 | owner, or a named responsible role |

## Scope decision, recorded

**Complete** as a scoped nominal-tube and measurement-chain report. **W1.8's parent acceptance remains
partial**, because the clamp, bracket, assembly and drawing deliverables are blocked on RR-CAD-02. No
ledger row is promoted by this report.
