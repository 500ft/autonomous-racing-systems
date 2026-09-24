# Load-cell force calibration protocol (E3)

**Status: CONDITIONAL. Not scheduled, not performed, no cell mounted.** This is the procedure that
*would* calibrate one load cell in one mount on one ADC channel, written so the software
([`experiments/load_cell_calibration.py`](../../experiments/load_cell_calibration.py)) can be finished
and tested without hardware. Everything below is prerequisites and steps; nothing here is a result.

Calibrating this force channel establishes **nothing** about the mast, the fixture, displacement, or
campaign readiness. It is one term in the compliance error budget.

## Prerequisites the purchase did not establish

None of these follow from owning the parts
([`purchased-instruments.json`](purchased-instruments.json)). Each is required before step 1.

| Prerequisite | Why |
|---|---|
| Cell rigidly fixed at one end, load applied at the other along the marked axis | A bending-beam cell reads its rated output only when mounted as intended |
| Verified load direction and a load path free of side load and off-axis moment | Parasitic loading is a first-order error, not a rounding term |
| Known reference masses **with stated uncertainty**, not nominal labels | An unlabelled "500 g" mass is not a reference |
| A means of applying load without shock | Overload can damage the element permanently |
| Recorded supported tare (mount hardware the cell already carries) | Capacity applies to the **gross** load, not the applied force |
| Ambient temperature record | Temperature affects both zero and sensitivity |

## Load points

Campaign range is 4/8/12/16/20 N. Proposed masses for the 5 kg cell, subject to actual mounting and
total load:

| Nominal mass | Applied force at g = 9.81 m/s² | Purpose |
|---|---|---|
| 0 (unloaded) | 0 | zero, start and end of every cycle |
| 0.25 kg | 2.45 N | **below the 4 N campaign floor** so that level is interpolated, not extrapolated |
| 0.50 kg | 4.91 N | |
| 1.00 kg | 9.81 N | |
| 1.50 kg | 14.72 N | |
| 2.00 kg | 19.62 N | |
| 2.10 kg | 20.60 N | **above the 20 N campaign ceiling** for the same reason |

Enter **actual** reference values and uncertainties, never the nominal label. Check total cell load
including tare against the 49.05 N capacity at every point; the tool refuses points that exceed it.

**Check the cell's usable floor before trusting the 2.45 N point.** ASTM E74 defines a lower limit
factor that sets the smallest force a force-measuring instrument may be used at. That check has not
been done; see [literature §4](../../literature/04-measurement-uncertainty-and-calibration.md).

## Procedure

1. **Record identity first**: cell, mount, ADC, channel, configuration id, operator, date, ambient
   temperature. Configuration must match the session that will later use the coefficients; the tool
   refuses a mismatch via `--expect-config`.
2. **Zero**: log unloaded for at least one settling period. This is the start zero.
3. **Three ascending/descending cycles.** At each point: apply the mass, wait the declared settling
   time, then average over the declared window. Predeclare both, and **keep the full time series** —
   the averaged value alone is not the evidence.
4. **Zero again** at the end of every cycle and at the end of the session. Start-to-end difference is
   the zero return.
5. **Reserve an independent check.** Either a fourth cycle or additional masses, scored **after** the
   fit is frozen. Scoring only the data used to fit measures nothing.
6. **Record raw file and its hash**, then run the analysis.

Log with the E2 recorder so the raw stream is preserved:

```bash
python experiments/measurement_logger.py --port <device> --seconds <n> \
    --output runs/load_cell_cal/<point> --source-kind measured
python experiments/load_cell_calibration.py --input <record>.json --output runs/load_cell_cal/analysis
```

## How the analysis works, and why

| Choice | Reason |
|---|---|
| **Errors-in-variables fit, not ordinary least squares** | Reference force carries mass and g uncertainty; counts carry noise. OLS attenuates the slope toward zero when x is uncertain (York 1966; York et al. 2004). |
| **No R² anywhere** | The correlation coefficient is discouraged as a calibration metric: a value near 1 is compatible with visible curvature (Analytical Methods Committee 1994/2005). Reported instead: residuals and a lack-of-fit versus pure-error decomposition, which needs the replicates the three cycles provide. |
| **Coverage factor from Student's t** | k = 2 is not automatic for a small fit. EA-4/02 §5 requires effective degrees of freedom; the tool reports k and the degrees of freedom it came from. |
| **Hysteresis and zero return reported in OIML R 60-1 vocabulary** | So the error-budget terms have their standard names. |

**Scope note, measured not assumed:** at the NAU7802's expected count noise, the errors-in-variables
fit and ordinary least squares agree to within 0.1 % — the count uncertainty is a negligible fraction
of the count spread. The tests demonstrate both that agreement and the attenuation that appears once
count noise grows. The errors-in-variables fit remains the default because nothing guarantees the
noise stays small.

## Verdicts

| Verdict | Meaning |
|---|---|
| `REFUSED` | A fatal blocker: missing reference uncertainty, saturated counts, load over capacity, wrong cell for the range, unreviewed record promoted to campaign-ready, mounting changed since calibration. No fit is produced. |
| `CALIBRATION_INCOMPLETE` | Fit computed, but something is unresolved or over a declared limit: extrapolated campaign level, hysteresis or zero drift over the predeclared limit, coarse reference masses, or missing identity fields. |
| `CALIBRATION_USABLE` | The force channel is characterised over the calibrated range. **This is not campaign readiness**, which needs the full physical-readiness checklist and a reviewer. |

Conversion outside the calibrated count range is refused rather than extrapolated. Coefficients are
per cell, per mount, per configuration: the 5 kg cell's coefficients must never be reused for the 1 kg
cell, and changed mounting requires a documented recheck.

## What is deliberately not here

No measured calibration. Every fixture under
[`experiments/fixtures/load_cell_calibration/`](../../experiments/fixtures/load_cell_calibration/) is
synthetic and labelled `SOFTWARE CHECK`, with `reviewer_state: unreviewed`. The tool writes nothing
into the campaign evaluator's inputs; importing a real calibration there would need reviewed
synchronisation and every field the campaign protocol requires.
