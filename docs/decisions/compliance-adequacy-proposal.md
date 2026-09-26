# Proposal: measurable adequacy criteria for the compliance campaign

**Status: PROPOSAL, not adopted. Unapproved.** The frozen rule remains R² ≥ 0.99 with hysteresis
≤ 5 % of full scale, relative U95 ≤ 10 % and ±15 % agreement against the as-built FEA prediction. This
document proposes a replacement for the R² component only. Nothing here changes a threshold, and no
past or future campaign result may be reinterpreted under it until it is reviewed and approved.

Prepared 2026-09-25 (closeout T2). Reviewer field and effective date are at the end, deliberately empty.

## Why R² is the wrong component to keep

Two independent reasons, and the second is the stronger one.

1. The analytical-chemistry literature discourages the correlation coefficient as *the* calibration
   quality metric: a value near 1 is compatible with visible curvature
   ([§4](../../literature/04-measurement-uncertainty-and-calibration.md)).
2. **It is not reliable even on its own terms.** At 0.3 µm assumed repeatability the median R² is
   0.9925 — passing — while about one simulated single-axis campaign in seven is rejected, and roughly
   one two-axis campaign in four fails on at least one axis
   ([decision screen](../../evidence/week-2026-09-19/decision_screen/reproduction.txt)). A criterion
   whose pass/fail flips this readily on assumed inputs is a weak gate regardless of its statistical
   pedigree.

**But replacing it with a lack-of-fit p-value is not sufficient either**, and that was the flaw in the
earlier suggestion. Non-rejection of lack of fit does not prove adequacy: with low power an
unacceptable departure passes unnoticed. NIST supports residual diagnostics *and* a declared test
model, not certification from any single scalar. A p-value with no practical tolerance behind it just
relocates the problem.

## What the proposal must contain

### 1. Measurand and model

- **Measurand:** static compliance of the specimen along one axis, in mm/N, as the slope of
  (tip reading − fixture reading) against measured force over 4/8/12/16/20 N.
- **Estimator:** the frozen campaign estimator. A change of estimator is a separate amendment.
- **Error assumptions, stated rather than implied:** force carries a shared calibration gain plus a
  per-reading readout term; displacement carries repeatability, quantization and the residual of the
  root-rotation correction. **Correlations are part of the model**: one calibration and one environment
  serve both axes, so the shared terms are campaign-scope, not per-reading. Independence is to be
  checked against the data, never assumed.

### 2. A practical tolerance for consequential departure — the part that makes the test mean something

Proposed for review, **not an owner acceptance value**: declare a maximum tolerable slope error from
nonlinear departure and from bias, expressed as a fraction of the fitted compliance, and size the test
to detect it. A defensible starting point for discussion is to tie it to the existing ±15 % model-
comparison band: a departure that could move the slope by more than roughly a third of that band is
consequential, since it would consume most of the comparison's margin on its own.

That number is **a proposal with a rationale, not a decision.** It needs the owner's judgement about
what error would change an engineering conclusion. Uncertainty, hysteresis and FEA agreement keep their
own separate requirements; this tolerance does not absorb them.

### 3. Diagnostics, not a single scalar

Required alongside any test statistic:

- Residuals against force, against direction, and against time or cycle index.
- Pure-error replication computed **within a (level, direction) cell**, so a systematic
  ascending/descending offset is reported as a direction effect instead of inflating the noise estimate
  that the test divides by.
- An explicit check of the independence assumption rather than an assertion of it.

### 4. Power, declared at the actual sample design

- A synthetic linear null, plus deliberately nonlinear, hysteretic and drifting alternatives.
- **False-rejection rate and detection power** at the real design (five levels, three cycles, two
  directions) against the practical tolerance in §2, with Monte Carlo precision reported.
- A criterion that cannot detect the tolerance in §2 at the planned sample size is rejected as a
  criterion, not accepted with a caveat.

### 5. Adapting the calibration tool's approach, not reusing its result

The calibration tool's parametric bootstrap is the right *shape* for this problem, because it generates
a null under the actual weighted errors-in-variables model instead of borrowing a classical F quantile
that assumes fixed-x homoscedastic ordinary least squares. It is not directly transplantable:

- Its `LOF_NULL_DRAWS = 300` at α = 0.01 gives p-value steps of 1/301 and only about three expected
  tail counts near the cutoff. **A close call at that resolution is seed-dependent**, which is not an
  acceptable basis for an engineering decision.
- Therefore: a declared numerical stopping rule. Increase draws until the decision is stable to a
  stated tolerance, and if a compute cap is reached first, return **indeterminate** rather than a
  verdict. 300 draws is not validated for every dataset.

## Instrument comparison template

To be filled per candidate, not by me and not from a catalogue page:

| Field | Why it is here |
|---|---|
| Installed uncertainty over the 0–30 µm working range | The only figure that matters; a bench spec is not an installed figure |
| Repeatability, **with its definition** and whether it already includes quantization | This screen adds repeatability *before* rounding, so a figure that bakes in quantization would be double counted |
| Resolution | A different quantity from repeatability (JCGM VIM 4.14 vs 2.21). A display can repeat a rounded value while concealing error |
| Bandwidth | This is a **static** task; high bandwidth buys nothing here and should not drive selection |
| Contact force and alignment sensitivity | Contact force perturbs a 26 µm signal |
| Range and overtravel | Must cover the full-scale signal with margin |
| Calibration source and traceability | Without it there is no uncertainty statement, only a number |
| Total acquisition cost | Recorded last and only with a dated vendor source |

**No candidate is selected here and no purchase is implied.** Pricing real candidates needs dated vendor
sources and is secondary to the statistical work. Better metrology and better criteria are
complementary: neither excuses ignoring the other, and the decision screen shows why — finer resolution
and wider root-station spacing both help, and neither alone rescues an adverse baseline.

## What this proposal deliberately does not do

- It does not change the frozen rule, or any threshold.
- It does not reinterpret an existing result. A campaign that failed under R² ≥ 0.99 stays failed.
- It does not certify any instrument or claim any measurement.
- It does not address the systematic-rotation bias, which **no version of this criterion can detect**:
  the adverse scenario passes both numerical gates at a 19.4 % slope error. That is an observability
  requirement on the apparatus, and it belongs in the readiness checklist rather than in a fit statistic.

## Approval

| Field | Value |
|---|---|
| Proposed by | Agent, 2026-09-25 |
| Reviewed by | *(empty — unreviewed)* |
| Owner decision | *(empty)* |
| Prospective effective version / date | *(empty until approved)* |
| Applies retrospectively | **No.** Prospective only, by construction. |
