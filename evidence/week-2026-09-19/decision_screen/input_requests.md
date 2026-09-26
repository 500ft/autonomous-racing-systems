# W3.2 — the three evidence bundles worth requesting

Ranked **after** the intervention results in [results.json](results.json), not from opinion and not by
copying the screen's `dominant_terms[0]`. Method and caveats: [reproduction.txt](reproduction.txt).

Every physical term in that screen is assumed. These requests ask for the evidence that would replace
an assumption with a record. **None of them requires a purchase to answer**, and a complete request is
not a filled register: missing values stay UNKNOWN until a record arrives.

## What the screen actually says

From a common adverse baseline (0.5 µm repeatability, 1 µm resolution, 40 mm root spacing), one
intervention at a time, 5000 campaigns each:

| Intervention | per-axis R² pass | both-axes pass | relative U95 |
|---|---|---|---|
| baseline | 0.0004 | 0.0000 | 0.0648 |
| finer indicator resolution, 1 → 0.5 µm | 0.1400 | 0.0200 | 0.0445 |
| better repeatability, 0.5 → 0.3 µm | 0.0054 | 0.0000 | 0.0563 |
| wider root station spacing, 40 → 100 mm | 0.1270 | 0.0162 | 0.0451 |

Three things follow, and they reorder the earlier advice:

1. **Resolution and root-station spacing outrank repeatability** from this baseline. The previous
   ranking put repeatability first; it sorted scatter with one term active at a time while quantization
   stayed active underneath, which answers a narrower question than this one.
2. **No single intervention rescues the baseline.** The best single change takes the two-axis pass
   fraction from about 0.00% to only about 2.00%. They have to be combined, and the combination is not
   the sum of the separate effects.
3. **Neither numerical gate detects a systematic root rotation.** The adverse rotation scenario biases
   the slope by 19.4% while median R² is 0.9947 and relative U95 is 0.0332 — both gates pass. Observability of
   root motion is therefore a correctness requirement, not a refinement.

## Bundle A — installed displacement and root-motion chain

**Highest priority**, because it decides both the top two interventions and the undetectable bias above.

Request: model and serial, range, resolution, mounting sketch, tip and root station coordinates with
units, acquisition method, and the calibration source. For a later bench study also repeated
**unrounded raw** readings if the device exposes them, timestamps, dwell, load direction, zero-return
data and environmental notes.

Format: CSV readings plus JSON or YAML metadata, plus a path to the vendor or calibration source.

Unlocks: replaces the assumed repeatability and rotation terms, and answers whether a candidate can
observe the intended displacement at all. The nominal hand-model signal is about **25.77 µm at 20 N and
5.15 µm at 4 N**; the FEA compliance is a separate quantity and is kept distinct.

**State it carefully.** Resolution and repeatability are different quantities. A display can repeat a
rounded value while concealing substantial error, and fine resolution does not prove low drift or
hysteresis. Say whether a quoted repeatability already includes quantization: in this screen
repeatability is added *before* rounding, so counting it twice is a real risk. A 1 µm step contributes
0.289 µm standard uncertainty under a uniform quantization model — that is a model term, not a
manufacturer's repeatability figure. LVDT and capacitive probes are candidates, not automatically
adequate and not the only viable technologies.

## Bundle B — force-chain reference and calibration evidence

Request: installed cell and ADC identifiers, reference masses with their uncertainties, mounting and
orientation, the gravity value and its basis, and zero, creep, drift and ascending/descending raw
readings per the existing calibration protocol.

Format: the existing calibration record schema, plus source certificates and raw CSV.

Unlocks: replaces the assumed shared-gain and readout terms and lets E3 be evaluated against something
real. The 5 kg cell is a candidate only; the 1 kg cell cannot cover the 20 N campaign. Note that the
shared gain is the term repetition cannot reduce, which is why it is requested as a calibration record
rather than estimated from repeats.

## Bundle C — mechanical interfaces and fixture geometry

Request: the six pending register values with coordinates, units, tolerance, source and acquisition
route — clamp engagement, both bolt pitches, optical offset, load height and root station spacing —
plus bolt coordinates, indicator positions, reviewed targets and the stiffness evidence the current
contract requires.

Format: a drawing revision or part number **with** the actual drawing, a dimensioned sketch, and the
mapping to register fields; inspection or test records later where the route requires them.

Unlocks: specific contract fields and the blocked geometry and fixture tasks. One part number starts
intake; it does not resolve every interface or certify fit. Respect the `design_then_inspect`,
`vendor_drawing` and `measurement` routes: a proposed nominal dimension can advance a design without
masquerading as inspected data.

## Status

These three requests are **complete as requests**. The values they ask for are absent, the register's
six pending rows stay pending, and the authoritative screen result stays UNKNOWN until a fixture
stiffness is declared with evidence.
