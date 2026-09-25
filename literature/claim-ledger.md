# Claim ledger — this project's claims against the literature

Every claim this repo makes that literature can support or challenge. Format follows the
research-analysis doctrine: claim, support, counter-evidence or gaps, confidence and why. **A claim with
no entry here should not appear in the final report.**

Section references are to the files in this folder. Nothing in this ledger changes a ledger row, a
threshold or a protocol; see [README](README.md) for why.

---

## Mechanical lane

### M1. The mast's first bending mode is 285.5 Hz and clears the 200 Hz guard

- **Support:** `runs/mast_fea/fea_summary.txt` (SIMULATION OUTPUT, converged mesh). Method backing from
  Blevins and Rao ([§3](03-structural-dynamics-and-modal-testing.md)).
- **Counter-evidence or gaps:** No measurement exists. The tap test is a **draft**, RR-S12 is blocked, and
  ISO 7626-5:2019 is the standard the frozen procedure would have to be written against.
  **Corrected 2026-09-24:** an earlier version of this claim argued the true frequency was bracketed
  between the Rayleigh upper bound and a Dunkerley lower bound. That argument is withdrawn here for the
  same reason it was withdrawn in [§3](03-structural-dynamics-and-modal-testing.md): a bound brackets the
  FE value only if both describe the same problem, and the [modal audit](../docs/design/MODAL_MODEL_AUDIT.md)
  shows they do not — the FE deck carries a one-node translational mass attached off-axis. The 285.5 Hz
  figure stands on its own model, not on an analytical bound around it.
- **Scope of the number (sharpened 2026-09-25):** 285.5 Hz is the output of the **historical
  off-axis single-node attachment model**, and that model's result exceeds 200 Hz. Withdrawing the
  bracketing argument does not change that output — but it does not establish the margin either, and
  **the corrected attachment model has not produced a result yet**. Until it does, the guard is cleared
  by the historical model only. Do not read the comfortable historical margin as a property of the
  corrected model.
- **Confidence: moderate** for the nominal tube as modelled by the historical deck; **none** as a
  statement about hardware, and **none** about what the corrected attachment model will give.

### M2. The cause of the 13.5 % gap between the 330.1 Hz hand calc and the 285.5 Hz FEA is UNRESOLVED

**Revised 2026-09-24 after a source audit.** The earlier version of this claim said the gap was
"expected physics, not a modelling defect" and attributed it to four mechanisms. That attribution was
wrong in two places and is withdrawn.

- **Support for the mechanisms existing at all:** the entries in
  [§3](03-structural-dynamics-and-modal-testing.md) are real and correctly describe shear deformation,
  rotary inertia, tip-mass extent and root flexibility as things that shift a cantilever's frequency.
- **Counter-evidence, from the model itself** ([audit](../docs/design/MODAL_MODEL_AUDIT.md)):
  **root flexibility cannot act between these two models** — the hand calculation assumes a built-in
  root and the FE deck fixes all three translations at the root node set, so both are rigid.
  **Tip-mass rotary inertia and axial extent are not in the model either**: the deck carries a
  one-node translational `*MASS`. Separately, the mass is attached to the **nearest material node**,
  which on a hollow section is about 8.5 mm off-axis, not at the section centre — an eccentric
  single-node attachment that is a modelling defect in its own right.
- **Confidence: the cause is unresolved.** Mechanisms that can still act are shear and rotary inertia
  of the tube, 1D beam versus 3D solid kinematics, the eccentric attachment, and local behaviour at the
  constrained root. None has been quantified. A controlled one-at-a-time comparison is required before
  any cause is named.
- **Status of the number:** 285.5 Hz stays the output of its recorded model, not a verified physical
  target. It is not re-run or overwritten by this correction.

### M3. Excluding the peak root von Mises stress as a singularity is correct practice

- **Support:** Williams (1952) proves no finite converged peak exists at a re-entrant corner. Sinclair (2004
  I and II) on removal versus interpretation. **Sinclair, Beisheim & Kardak (2019) and Sinclair, Beisheim &
  Roache (2016) map one-to-one onto the scheme already in use**: divergence checks at the singular point,
  convergence checks at the gauge region ([§5](05-verification-validation-and-mechanical-design.md)).
- **Counter-evidence or gaps:** The repo excludes the root by **assertion**; it does not run the published
  divergence check that would demonstrate the exclusion is warranted.
- **Confidence: high** that the practice is right; **moderate** that it is currently *demonstrated*.

### M4. The mesh is converged

- **Support:** `runs/mast_fea/mesh_convergence.txt`, three refinements, changes under 1.5 % on gauge stress,
  tip deflection and f₁ at a fixed gauge band.
- **Counter-evidence or gaps:** **This is a bare delta.** Celik et al. (2008) and Roache (1994) require an
  **observed order of convergence** and a Grid Convergence Index with a factor of safety to state a numerical
  uncertainty. A small change between two grids is necessary, not sufficient.
- **Confidence: moderate.** The study is real and three-level; the *reporting* falls short of the
  ASME-endorsed procedure.

### M5. Crash safety factor is 8.05

- **Support:** `runs/mast_hand_calc/design_sweep.txt`, 50 g × SF 1.5 → 128.76 N, σ 34.3 MPa against 276 MPa
  yield.
- **Counter-evidence or gaps:** This is a **tube-only** number. No bolted-joint analysis exists, so it is not
  an assembly safety factor. VDI 2230 and the ECSS handbook define what the missing calculation must contain
  ([§5](05-verification-validation-and-mechanical-design.md)). The 50 g shock level is `model_assumption`,
  not a measured environment. Yield is a handbook typical, not a mill certificate (EN 10204).
- **Confidence: moderate** for the tube; **none** for the assembly.

### M6. The split clamp needs an internal support sleeve

- **Support:** Campos & Hall (2019) show where thick-wall Lamé breaks down for thin walls, which is this
  regime. DeRuntz & Hodge (1963) give the plastic collapse scale for a tube crushed between platens, the same
  load case as two clamp halves closing. Brazier (1927) is the named mechanism for a crushed root changing
  local bending stiffness. Wierzbicki & Suh (1988) show crush and bending interact.
- **Counter-evidence or gaps:** **No standard or handbook mandates a sleeve.** BS EN 74-1 qualifies tube
  clamps by slip-and-distortion **test**, not calculation — precedent that this case is test-validated. No
  peer-reviewed split-clamp torque-capacity paper was found.
- **Confidence: moderate-to-high** that the sleeve is justified by mechanics. **The claim must be argued from
  mechanics and validated by test, never presented as a code requirement.**

### M7. Blind assembly fails the sightline bound and a levelling step is required

- **Support:** `runs/mast_tolerance_stack/summary.txt`: worst case 1.284° against a 0.458° bound, 0.354° after
  levelling. Method backing from Fischer (2011); Chase & Parkinson (1991) justify worst case as the right gate
  for a blind assembly.
- **Counter-evidence or gaps:** **There are no drawings.** ASME Y14.5 or ISO 1101 govern the datum reference
  frame the budget's contributors must be toleranced against, and ISO 2768 defaults silently enter the stack
  if a drawing block ever cites them. One contributor, the 40 mm bolt pattern, is `ASSUMED`.
- **Confidence: moderate** on the arithmetic; **low** until drawings define the datums.

---

## Measurement lane

### M8. A fitted compliance slope with relative expanded uncertainty U95 ≤ 10 % is achievable

- **Support:** `docs/CAD_MEASUREMENT_CONTRACT.md` arithmetic; framework from JCGM 100 (GUM) and NIST TN 1297
  ([§4](04-measurement-uncertainty-and-calibration.md)).
- **Counter-evidence or gaps:** Three problems. **(a)** EA-4/02 §5 requires effective degrees of freedom and a
  t-based coverage factor for a five-point fit rather than an automatic k=2. **(b)** Both axes carry uncertainty.
  Classical attenuation then biases an ordinary-least-squares slope toward zero **under that specific
  error model**, and York (1966, 2004) supplies both an estimator that avoids it and the slope standard
  error the gate needs. This is a conditional statement, not a universal one: Cantrell (2008) compares
  regimes where bivariate fitting matters against regimes where simpler fitting is satisfactory, and the
  practical size of the effect depends on the error model and magnitude. **Measured in this repo:** at
  the NAU7802's expected count noise the two estimators agree to within 0.1 %; the difference only
  appears once count uncertainty is a real fraction of the count spread. Shared gain errors are a
  different failure mode that neither estimator removes. **(c)** No standard governs cantilever compliance
  testing at this scale and no published sub-30 µm uncertainty budget was found, so the plan must be composed
  rather than cited.
- **Confidence: low** that the current method as written would satisfy a metrologist, **moderate** that the
  target is reachable once the estimator and coverage factor are corrected.

### M9. R² ≥ 0.99 is a meaningful data-quality gate

- **Support:** none found.
- **Counter-evidence:** **Direct.** The Analytical Methods Committee (1994, rev. 2005) states that the
  correlation coefficient "is open to misinterpretation … and is to be discouraged" for calibration, and that
  a value near 1 is compatible with visible curvature. Asuero et al. (2006) concur. The recommended
  replacement is lack-of-fit versus pure-error decomposition, **which requires replicates at each load point**
  and therefore changes the test matrix, not just the arithmetic.
- **Scope of the objection (added 2026-09-24):** the cited sources discourage R² *as the calibration
  quality metric*. They do not make R² meaningless as one diagnostic among several, and the campaign's
  R² gate sits alongside hysteresis and U95 gates rather than alone. The replacement also needs valid
  within-condition replicates; the protocol's repeated load/unload cycles may already supply them, with
  ascending and descending treated separately. Additional repeats are conditional, not automatic.
- **Confidence: high that this gate is weak as specified.** It is frozen in
  [`design.md`](../docs/specs/mast-physical-validation/design.md); changing it is a prospective owner decision.

### M10. The 5 kg cell covers the 4–20 N campaign range

- **Support:** 49.05 N nominal capacity, ratio 2.45 at 20 N before tare
  ([`purchased-instruments.json`](../docs/hardware/purchased-instruments.json)). The 1 kg cell at 9.81 N
  cannot reach 12 N.
- **Counter-evidence or gaps:** **ASTM E74 defines a "lower limit factor" that sets the smallest force an
  instrument may be used at.** The 4 N point may fall below the 5 kg cell's usable floor; this has not been
  checked. OIML R 60-1 supplies the vocabulary for every error term still unquantified: creep, hysteresis,
  non-linearity, zero return, temperature effects.
- **Confidence: moderate** at the top of the range, **unknown at 4 N** until the lower limit is checked.

### M11. The purchased instruments cannot measure the mast's modal response

- **Support:** NAU7802 at 320 samples/s gives a 160 Hz Nyquist limit, below the 285.5 Hz mode. LIS3DH
  bandwidth is mode dependent (roughly 149 Hz in high-resolution mode at 1.344 kHz output rate). Both recorded
  in [`measurement-electronics.md`](../docs/hardware/measurement-electronics.md).
- **Counter-evidence or gaps:** none. The arithmetic is direct.
- **Confidence: high.** This is the strongest claim in the ledger.

### M12. Mast vibration matters for LiDAR data quality, not just structurally

- **Support:** Schlager et al. (2022) measured point loss on an automotive lidar under shaker excitation;
  Periu et al. (2013) treat mount design as the fix for a lidar on a vibrating vehicle
  ([§3](03-structural-dynamics-and-modal-testing.md)).
- **Counter-evidence or gaps:** Both are full-scale vehicles. **No literature was found on sensor-mast
  vibration for 1/10-scale platforms.** The 200 Hz guard is currently justified structurally, not by a
  measured detection-quality requirement.
- **Confidence: low-to-moderate.** Plausible and now cited by analogy, not established for this platform.

---

## Vehicle lane

### V1. Cornering stiffnesses were identified and validated on held-out data

- **Support:** the repo's identification study; method backing from Rajamani (2012) and the CommonRoad vehicle
  models document, which is the literal source of the simulator's equations
  ([§1](01-vehicle-dynamics-and-system-id.md)).
- **Counter-evidence or gaps:** **Ljung (1999) is the direct authority for the repo's own caveat**: fitting a
  model to data generated by that same model structure validates the estimator, not the model. Structural
  identifiability (Bellman & Åström 1970) has not been shown for `C_Sf` and `C_Sr` separately; persistent
  excitation (Green & Moore 1986) has not been stated. Dikici et al. (2025) and Liniger et al. (2015) both
  identify tire parameters from **real** scaled-vehicle data, so the real-data version is demonstrably
  achievable.
- **Confidence: high** that the pipeline is correct; **none** that the parameters transfer to hardware. The
  repo already states this, and the literature backs the statement.

### V2. Tuned pure pursuit achieved the lowest RMS cross-track error, below LQR and MPC

- **Support:** `reports/controller_comparison.md` under fixed track, timestep and 100 Hz update rate. Snider
  (2009) found no steering method dominates everywhere. Liniger et al. (2015) indicate MPC's benefit at small
  scale is constraint handling and progress, not tracking accuracy.
- **Counter-evidence:** **Becker et al. (2023) report the opposite on a real F1TENTH car up to 11 m/s**, where
  a model-aware pursuit controller beat plain pure pursuit by roughly 4× on lateral error. **No verified
  publication reports this result in the same direction.** Henderson et al. (2018) require across-seed spread,
  which this comparison does not report. Stanley, the standard geometric co-baseline, is absent.
- **Confidence: low as a general claim, moderate as scoped.** The defensible form is "under our nominal plant,
  tuning budget and speed regime." This is a finding to defend and re-test, not a settled result.

### V3. MPC is justified by constraint handling and bounded runtime rather than accuracy

- **Support:** Mayne (2014) states exactly this; Liniger et al. (2015) and Rosolia & Borrelli (2018) are
  consistent with it ([§2](02-control-and-estimation.md)).
- **Counter-evidence or gaps:** The runtime claim rests on a 1.33 ms p95 from SciPy SLSQP. Against acados and
  the structure-exploiting solver literature, **that is a prototype timing, not a deployment guarantee.**
- **Confidence: high** on the principle, **moderate** on this implementation's runtime claim.

### V4. A mismatched-plant sweep will reveal which controller conclusions survive

- **Support:** Dean et al. (2020) show certainty-equivalent LQR degrades and can destabilise under
  identification error. Yu et al. (2014) bound nominal MPC's inherent robustness. Kong et al. (2015) find the
  **size** of model error, not model complexity, predicts degradation.
- **Counter-evidence or gaps:** Sweep magnitudes are currently arbitrary. **Tufa & Ka (2016) give a published
  method for determining mismatch thresholds** and should set them instead.
- **Confidence: high** that the experiment is the right next step; **low** on the current magnitude choices.

---

## Claims the literature does *not* let this project make

- That any modal, compliance or tire parameter has been **measured**. Nothing physical has been tested.
- That the mast assembly has a safety factor. No joint analysis exists.
- That the clamp design is code-compliant. No code governs it.
- That pure pursuit is better than MPC in general. See V2.
- That 6061-T6 handbook values describe the purchased stock. EN 10204 Type 3.1 is what would.

## Evidence-strength summary

Updated 2026-09-24 after the source audit and the decision-logic repairs.

The **mechanical lane** rests on grade A–B literature: established handbook formulas, adopted standards
and primary sources with long experimental backing. Two weaknesses are now explicit rather than implied.
Every claim is still simulation or hand calculation, because the experimental half is unbuilt. And the
one place where mechanisms were attributed to a specific numerical result, M2, turned out to be wrong:
the attribution is withdrawn and the cause of the 330.1 → 285.5 Hz gap is unresolved. M1 lost its
bracketing argument for the same reason. Good literature did not prevent either error, because neither
was a literature question — both were questions about what the model actually contains.

The **measurement lane** is the best supported by standards and still the worst aligned to them. The
conflicts recorded in M8 and M9 are conflicts with the **frozen protocol**, which is unchanged: it still
gates on R² ≥ 0.99 and does not specify an errors-in-variables estimator or an effective-degrees-of-freedom
coverage factor. What changed on 2026-09-24 is narrower than "the new tooling no longer repeats those
mistakes", which overstated it. **Repaired:** the tooling no longer returns a passing verdict while its
own checks fail, it uses an errors-in-variables estimator, and it reports a coverage factor drawn from a
Student-t table rather than assuming k = 2. **Still approximate:** `coverage_factor` reads a finite table
through 30 degrees of freedom and then returns 1.960, and its input is the **fit's** degrees of freedom
rather than an effective value derived per uncertainty component. That is closer to the guidance than a
flat k = 2 and is not yet a Welch-Satterthwaite effective-DOF treatment. Amending the protocol itself
remains a prospective, owner-reviewed act.

The **vehicle lane** is the weakest and is unchanged by this round. Its headline comparative result, V2,
still has no supporting citation and one credible contradicting one, and its identification result
validates the estimator rather than the model.

One methodological lesson worth keeping, because it produced three of the errors above: a computed
diagnostic that does not participate in a verdict is not a check, and a mechanism that is absent from a
model cannot explain that model's output.
