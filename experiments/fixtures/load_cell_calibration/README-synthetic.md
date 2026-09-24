# Synthetic calibration fixtures (SOFTWARE CHECK)

Generated for [`test_load_cell_calibration.py`](../../test_load_cell_calibration.py). **No cell was
mounted, loaded or measured.** Every record carries `source_kind: synthetic`, a `SOFTWARE CHECK`
label and `reviewer_state: unreviewed`.

All fixtures are drawn from one known affine mapping, `force_N = -0.40 + 2.0e-5 * counts`, so the
recovery test has a ground truth to check against. Each remaining file injects exactly one fault.

| Fixture | Injected fault | Expected verdict |
|---|---|---|
| `known_affine.json` | none | `CALIBRATION_USABLE` |
| `hysteresis.json` | loading/unloading offset over the declared limit | `CALIBRATION_INCOMPLETE` |
| `zero_drift.json` | large start-to-end zero return | `CALIBRATION_INCOMPLETE` |
| `inadequate_range.json` | points span only 2.45–4.91 N | `CALIBRATION_INCOMPLETE` |
| `coarse_references.json` | reference masses at 2 % uncertainty | `CALIBRATION_INCOMPLETE` |
| `missing_uncertainty.json` | no reference-mass uncertainty | `REFUSED` |
| `clipping.json` | one saturated count value | `REFUSED` |
| `wrong_cell_1kg.json` | 1 kg cell used for the full 4–20 N profile | `REFUSED` |
| `wrong_units.json` | masses entered as newtons | `REFUSED` |
| `promoted_unreviewed.json` | unreviewed record promoted to campaign-ready | `REFUSED` |

Regenerate by editing the fixtures directly; they are committed data, not build output.
