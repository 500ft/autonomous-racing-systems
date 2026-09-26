# Engineering audit — mechanical lane

Prepared 2026-09-25. **Audit only: this document changes no requirement, threshold, CAD geometry or
selected mechanism.** It records what is supported, what is asserted, and what cannot yet be assessed.
Corrective actions are proposals.

Scope: the LiDAR mast and its interfaces — the lane where design decisions are being made. The vehicle
simulation lane is out of scope for this pass.

## How to read the provenance labels

The repository currently uses **three different vocabularies** for the same idea, which is the first
finding below. This audit uses one set, and [TRACEABILITY.md](TRACEABILITY.md) maps the others onto it.

| Label | Meaning |
|---|---|
| `requirement` | Imposed target: a rule, a budget, an interface we must meet |
| `measured input` | Read off a physical thing with a recorded method |
| `sourced assumption` | Taken from a datasheet, handbook or standard, with the source cited |
| `calculated result` | Computed from other entries by a shown model |
| `selected value` | Chosen by a designer, possibly informed by a calculation |
| `measured result` | An outcome observed in a test |
| `provisional estimate` | A working number with no evidence yet, explicitly marked |

**Evidence status is tracked separately from provenance.** A selected value may be `unverified`,
`analytically assessed` or `physically tested`. Nothing in the mechanical lane is `physically tested`.

## Findings

Ordered by consequence. "Retrospective assessment" means the work evaluates an existing number whose
original rationale is not recorded; it does not recover the designer's intent.

### F1 — The 200 Hz modal guard is not satisfied by the drivetrain it cites, and drove a redesign

- **Where:** [`16_mechanical_design_analysis.md`](design/16_mechanical_design_analysis.md) §3.1, §6.
- **Current claim:** `f1` must clear the 100 Hz control rate and "a plausible low-hundreds-Hz
  motor/drivetrain excitation band" by 2×, therefore `f1 ≥ 200 Hz`. The mast is reported as clearing it
  at 1.43× (FEA 285.5 Hz).
- **Evidence and its limitation:** the 100 Hz control rate is a `requirement` and is real. The motor
  band is **`provisional estimate` with no cited frequency** — the word used is "plausible". No motor
  excitation frequency is computed anywhere in the repository.
- **What the repo's own numbers give.** §14 already derives motor speed 20 600 rpm at 10 m/s and 38 850
  rpm no-load on 3S. First-order shaft frequency is therefore **343 Hz at 10 m/s**, and it passes
  through the mast's 285.5 Hz FEA mode at about **8.3 m/s** — inside the intended operating envelope.
  The guard is crossed at about 5.8 m/s. See the calculation block added at §6.1.
- **Consequence if wrong:** the guard's stated basis assumed the excitation band sits *below* the mode
  and must be cleared upward. The drivetrain numbers put first-order shaft excitation *above* the mode,
  sweeping up through it during acceleration. The reported "1.43× margin" is a margin against a number
  that does not describe this drivetrain. This threshold drove the whole mast redesign from 120 mm to
  100 mm, so it is the single most consequential unverified input in the lane.
- **Not claimed:** this does **not** show the design fails. Whether a swept-through resonance matters
  depends on rotor unbalance, the transmission path from motor to deck to mast base, and damping —
  none of which is recorded. It shows the criterion's justification is absent, not that the mast is bad.
- **Priority: highest.** Action: record the missing inputs (pole count, gear ratio and tooth counts,
  unbalance class), then either re-derive the guard from a real excitation spectrum or restate it
  honestly as a control-rate guard with the drivetrain question open.

### F2 — The tolerance stack's dominant term describes a rejected design route

- **Where:** [`runs/mast_tolerance_stack/summary.txt`](../runs/mast_tolerance_stack/summary.txt) line 11,
  and §7 of the design doc.
- **Current value:** base-to-tube squareness **0.500°**, the largest single contributor to a 1.284°
  worst-case total, annotated "ASSUMED FDM/printed-bracket perpendicularity, no post-machining".
- **The inconsistency:** [`fixture-preparation.md`](../cad/roboracer/fixture-preparation.md) selects
  "a machined metal split-clamp route as the proposed fixture, **not a printed polymer primary clamp**",
  and `cad/solidworks/` models a machined split clamp. The stack still carries the printed-bracket value.
- **Consequence if wrong:** the stack concluded that blind assembly fails and a scan-plane levelling step
  is mandatory. If the dominant term belongs to a rejected process, that conclusion may be conservative
  by a wide margin, and a mandated assembly step may be unnecessary — or the stack is simply stale.
- **Cannot be resolved by editing the number.** A machined squareness value would be a new
  `provisional estimate` with no evidence. **Priority: high.** Action: record the actual clamp process
  and its achievable perpendicularity, then re-run the stack. Do not substitute a favourable value.

### F3 — A stack contributor uses a dimension the register says is unknown

- **Where:** §7 table, "LiDAR mounting datum, 0.10 mm / 40 mm → 0.143°".
- **The inconsistency:** the 40 mm bolt pattern is `ASSUMED`, while
  [`geometry.json`](../cad/solidworks/geometry.json) lists `lidar_bracket_bolt_pitch` under
  `blocked_not_modelled` with acquisition route `vendor_drawing`. One artifact assumes a value another
  declares unavailable.
- **Consequence:** small in magnitude (0.143° of 1.284°), but it is a broken evidence chain, and the
  same pattern governs the bracket that is not modelled.
- **Priority: medium.** Action: one vendor drawing resolves both. Until then the stack entry should
  carry the same `pending` marker the register uses.

### F4 — "the validated static FEA"

- **Where:** [`summary.txt`](../runs/mast_tolerance_stack/summary.txt) line 15.
- **Issue:** the FEA is not physically validated. It was compared against a hand calculation, which is
  model-to-model agreement. The phrasing appears inside a committed artifact, where it is most likely to
  be quoted onward.
- **Priority: medium**, because it is a wording defect with no numerical effect. The 0.004°
  contribution it feeds is negligible either way.
- **Deliberately not hand-edited.** `summary.txt` is generated output with its own provenance. Editing
  a committed run artifact to improve its prose would break the link between the artifact and the code
  that produced it. Action: fix the string in `experiments/mast_tolerance_stack.py`, so the correction
  appears the next time the stack is legitimately re-run — which finding F2 will require anyway.

### F5 — Three provenance vocabularies for one concept

| Artifact | Vocabulary | Counts |
|---|---|---|
| `cad/roboracer/parameters.csv` | `model_assumption`, `protocol`, `pending`, `design_choice`, `reported_vendor_nominal`, `committed_simulation` | 9 / 8 / 6 / 3 / 2 / 2 of 30 rows |
| `cad/solidworks/geometry.json` | `provisional_design`, `design_choice`, `model_assumption` | 14 / 4 / 1 of 19 values |
| `docs/design/16_*.md` | prose tags: `ASSUMED`, `LOCKED`, `FIRMED`, `MEASURED`, `derived` | ad hoc |
- **Consequence:** `provisional_design` and `model_assumption` are used for overlapping ideas, and the
  prose tags have no defined meaning. A reader cannot tell whether two artifacts agree about how well a
  number is supported. `FIRMED` in particular reads as stronger than it is: the 0.175 kg tip mass it
  labels is a datasheet body mass plus two unweighed allowances.
- **Priority: medium.** Action: keep each artifact's machine-readable vocabulary, since checkers depend
  on it, and add one mapping table. Done in [TRACEABILITY.md](TRACEABILITY.md). Do not rename register
  values in this pass; `fixture_contract.py` and `ledger_validator.py` gate on them.

### F6 — The register is dominated by assumptions and pending values

- 15 of 30 register rows are `model_assumption` (9) or `pending` (6); 14 of 19 geometry values are
  `provisional_design`.
- This is honestly labelled and is **not** a defect. It is recorded here so the audit's overall verdict
  is visible: the mechanical lane is a coherent design study resting largely on assumed inputs, and no
  part of it is physically tested.
- **Priority: informational.** The three input bundles in the reviewer packet already target the
  highest-value of these.

## What each finding is

| Finding | Missing documentation for a supported decision | Needs engineering justification | Cannot be assessed yet |
|---|---|---|---|
| F1 modal guard | | **yes** — the criterion's basis | partly: unbalance and path unrecorded |
| F2 squareness term | | **yes** — process mismatch | yes, until the process is recorded |
| F3 bolt pattern | | | **yes** — needs a vendor drawing |
| F4 wording | **yes** | | |
| F5 vocabularies | **yes** | | |
| F6 assumption density | **yes** (now recorded) | | |

## Missing inputs, and how to get them

| Input | Blocks | How to obtain |
|---|---|---|
| Motor pole count / pole pairs | commutation-order excitation frequencies | Velineon 3500 datasheet or a count of stator teeth and magnets |
| Gear ratio and tooth counts | gear-mesh excitation frequency | the Slash 4x4 spur and pinion part numbers already in §14's BOM |
| Rotor unbalance class or measured vibration | whether first-order excitation has any energy | vendor spec, or a bench accelerometer run once the LIS3DH is characterised |
| Motor-to-deck transmission path estimate | whether mast-base excitation is comparable to motor vibration | a bench measurement, not a calculation |
| Clamp process and achievable perpendicularity | F2, and the levelling-step requirement | the actual fabrication route once RR-CAD-02 is answered |
| LiDAR bolt pattern | F3, and the bracket model | one vendor drawing |

No value above is guessed anywhere in this audit or in the calculation block it added.

**Where these requests live, and why not in the generated sheet.**
`cad/roboracer/input-requests.csv` is *generated* from the register by `cad/input_requests.py` and
staleness-checked, so hand-appending rows would break `--check`. The four drivetrain inputs are also not
register parameters — they describe the vehicle that excites the mast, not the mast. They are tracked
here and in [TRACEABILITY.md](TRACEABILITY.md) instead. If they later need to gate a ledger row, the
right move is to add them through the generator, not around it.

## What this audit did not do

- It changed **no** requirement, threshold, acceptance criterion, CAD geometry or selected mechanism.
- It did **not** edit `runs/mast_tolerance_stack/summary.txt` to fix F4's wording. That file is
  generated output with its own provenance; the string was corrected in the generator so it appears on
  the next legitimate re-run.
- It did **not** substitute a machined-clamp squareness value for F2. That would replace one
  unsupported number with another.
- It did **not** recover original design intent anywhere. §6.1 is labelled a retrospective assessment.
