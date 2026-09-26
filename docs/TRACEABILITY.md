# Traceability index — mechanical lane

One row per consequential decision: what it is, where its reasoning lives, what supports it, and what
would confirm it. **This index links; it does not duplicate.** Equations and numbers stay beside the
decisions they support.

Audit that produced this: [ENGINEERING_AUDIT.md](ENGINEERING_AUDIT.md). Nothing in this lane is
physically tested.

## Decisions

| Decision | Requirement it serves | Reasoning lives in | Evidence status | Confirmed by |
|---|---|---|---|---|
| Tube 100 mm × 20 mm OD × 1.5 mm wall, 6061-T6 | mast stiff enough to clear the modal guard | [§3.2 design sweep](design/16_mechanical_design_analysis.md) | analytically assessed | inspection of delivered stock; no as-built record |
| Tip mass 0.175 kg | modal and stress inputs | [§3.1](design/16_mechanical_design_analysis.md), [register](../cad/roboracer/parameters.csv) | 0.130 kg datasheet + 0.045 kg **unweighed allowances** | weigh the assembled bracket and cable |
| Crash case 50 g, SF 1.5 → 128.76 N | strength sizing | [§3.1](design/16_mechanical_design_analysis.md) | provisional estimate — the shock level is assumed | no planned test; would need a drop spec |
| `f1 ≥ 200 Hz` modal guard | avoid control-rate and drivetrain excitation | [§3.1](design/16_mechanical_design_analysis.md) + [**§6.1 retrospective**](design/16_mechanical_design_analysis.md) | **control-rate half supported; drivetrain half unresolved (audit F1)** | pole count, tooth counts, unbalance, transmission path |
| FEA first mode 285.5 Hz | modal acceptance | [`fea_summary.txt`](../runs/mast_fea/fea_summary.txt), [modal audit](design/MODAL_MODEL_AUDIT.md) | calculated result of one model definition | tap test — draft only, RR-S12 blocked |
| Machined split clamp, not printed | preserve the fixed-root assumption | [fixture-preparation](../cad/roboracer/fixture-preparation.md) | selected value | **conflicts with the stack's printed-bracket term (audit F2)** |
| Internal support sleeve | prevent wall crush changing local `I` | [`geometry.json`](../cad/solidworks/geometry.json), [§5 literature](../literature/05-verification-validation-and-mechanical-design.md) | argued from mechanics; **no code requires it** | seating-torque and slip test |
| Levelling step mandatory | sightline within 0.458° | [§7](design/16_mechanical_design_analysis.md) | analytically assessed | **depends on the disputed 0.500° term (F2)** |
| Deck plane ≤ 0.138 m | sightline at the 0.30 m wall | [§7](design/16_mechanical_design_analysis.md) | calculated result | deck does not exist; RR-CAD-03 deferred |
| Fixture ≥ 10× specimen stiffness | separate specimen from fixture compliance | [measurement contract](CAD_MEASUREMENT_CONTRACT.md) | requirement | no fixture exists; screen verdict UNKNOWN |
| Campaign gates: R² ≥ 0.99, hysteresis ≤ 5 %, U95 ≤ 10 %, ±15 % | compliance acceptance | [frozen protocol](specs/mast-physical-validation/design.md) | requirement (frozen) | `docs/decisions/compliance-adequacy-proposal.md` (arrives with PR #44) is **unapproved** |

## Provenance vocabularies, reconciled

Three artifacts label evidence differently. Each keeps its own values, because checkers gate on them;
this table is the mapping. Audit finding F5.

| Audit label | `parameters.csv` | `geometry.json` | design-doc prose |
|---|---|---|---|
| requirement | `protocol` | — | requirement, LOCKED |
| measured input | — | — | MEASURED |
| sourced assumption | `reported_vendor_nominal` | — | datasheet |
| calculated result | `committed_simulation` | — | derived |
| selected value | `design_choice` | `design_choice` | LOCKED, FIRMED |
| measured result | — | — | — *(none exist)* |
| provisional estimate | `model_assumption`, `pending` | `provisional_design`, blocked rows | ASSUMED |

Two cautions this mapping exposes:

- **`FIRMED` overstates.** It labels the 0.175 kg tip mass, which is a datasheet body mass plus two
  unweighed allowances — a `provisional estimate` by the left-hand column.
- **`model_assumption` and `pending` are different things** and share one audit label only because
  neither is evidence. `pending` means a route exists and the value is awaited; `model_assumption` means
  a number is in use with no route recorded.

## Open items, by what unblocks them

| Blocked | Needs | Owner |
|---|---|---|
| Drivetrain half of the modal guard (F1) | pole count, tooth counts, unbalance class, transmission estimate | recordable from existing BOM + one bench run |
| Tolerance stack validity (F2) | actual clamp process and achievable perpendicularity | RR-CAD-02 |
| Bracket model and stack datum (F3) | one LiDAR vendor drawing | RR-CAD-02, `vendor_drawing` route |
| Every physical claim | fixture, instruments, calibration, reviewer | RR-CAD-02, RR-S02, RR-S09, RR-S12 |
