# Modal model definition audit (P1-A, stage 1 — no solver run)

Date 2026-09-24. Scope: what the committed modal model **actually defines**, read from source. No mesh
was built, no solver was run, and no frequency was recomputed. Everything below is verifiable from
`experiments/mast_fea.py` at the current revision; nothing here is a measurement or a new result.

This exists because [claim M2](../../literature/claim-ledger.md) asserted the 330.1 → 285.5 Hz gap was
explained by named physical mechanisms. Two of those mechanisms cannot act between these two particular
numerical models, and a third is not represented the way the claim assumed.

## What the source defines

| Item | Source | Fact |
|---|---|---|
| Tip mass attachment | `build_mesh`: `tip_center_node = min(tip_pool, key=lambda t: math.hypot(t[1], t[2]))[0]` | The **nearest existing material node** to the tube axis on the `z = L` plane. |
| Mass element | `write_modal_inp`: `*ELEMENT, TYPE=MASS` on that one node, `*MASS` carrying the tip mass | A single-node point mass. No tip-ring coupling, no rigid element, no reference node. |
| Root, modal | `NROOT, 1, 3` | All three translations fixed. |
| Root, static | `NROOT, 1, 3` | All three translations fixed. |

## Consequences, stated without a solve

1. **The attachment node is not on the tube axis.** The section is hollow: outer diameter 20 mm, wall
   1.5 mm, so the inner radius is 8.5 mm. There is no material at the axis, and therefore no node
   there. The nearest material node on the tip plane lies on or near the **inner wall, about 8.5 mm
   off-axis**. The variable name `tip_center_node` describes an intent the geometry cannot satisfy.
2. **The 0.175 kg is applied eccentrically at a single node**, not distributed over the tip section and
   not rigidly coupled to it. Local compliance at that one node and the eccentricity are both in the
   model, unquantified.
3. **Root flexibility cannot explain the hand-versus-FEA gap.** Both models have a rigid root: the hand
   calculation assumes a built-in cantilever and the FE deck fixes all three translations at the root
   node set. Whatever the difference is, a compliant clamp is not in either model. Root flexibility
   remains a real hardware-versus-model mechanism; it is not a hand-versus-FEA mechanism here.
4. **Tip-mass rotary inertia and axial extent are not represented.** A one-node `*MASS` card carries
   translational mass only, as written. The sensor body's inertia and extent are absent from the model,
   so they cannot be the cause of a difference between these two models either.

## What remains unresolved

The **cause and magnitude** of the 13.5 % difference are unresolved. The mechanisms that can still act
between these two models are shear deformation and rotary inertia of the tube, the difference between a
1D beam kinematic assumption and a 3D solid, the eccentric single-node mass attachment, and local shell
behaviour near the constrained root. Their relative sizes are unknown and are not assigned here.

The eccentric attachment is a **modelling defect worth fixing**, not merely an explanation: a centred
mass coupled to the tip section is the model the hand calculation is comparable to.

## Stage 2, not done here

A controlled comparison, budgeted as its own task with a recorded environment:

1. Export the selected node's coordinates, its radial offset, the total added mass and the root
   constraint set from a fresh model. Confirm which mode is global bending from its **shape**, not its
   index.
2. Define the intended reference explicitly: a centred tip mass with a stated coupling. A rigid coupling
   is itself an assumption, not automatically the right joint.
3. Compare that against the current single-node attachment with **every other input held fixed**.
4. Then vary shear, distributed payload inertia and root restraint **one at a time**, recording effect
   sizes rather than attributing causes by analogy.
5. Check mode shapes, symmetry and mesh sensitivity for each declared observable.

Constraints on stage 2: the committed 285.5 Hz result keeps its original provenance and is **not**
overwritten as though it were a rerun. The ±15 % band is not widened to absorb a changed result. Any
change to the reference used by another model is a prospective, reviewed decision.

## Status of the affected numbers

`runs/mast_fea/fea_summary.txt` remains the output of the model recorded there. It is a
**SIMULATION OUTPUT of a specific model definition**, not a verified physical target, and this audit
does not change it.
