# cad/solidworks

Authors mast-assembly parts natively in SOLIDWORKS on the licensed host, gated on
a CadQuery oracle. This is the SOLIDWORKS half of the CAD work; `cad/generate.py`
remains the CI-gated CadQuery generator for the frozen analysis specimen.

```
geometry.json ──> oracle.py (CadQuery)  ──> oracle.json   expected volume/bbox/mass
      │                                          │
      └────────> author_mast_assembly.py ────────┴──> gate: measured vs oracle
                 (SOLIDWORKS, on the host)            .sldprt + .step + preview
```

CadQuery is the reference, not the deliverable. The deliverable is the SOLIDWORKS
model. A clean rebuild proves SOLIDWORKS raised no error; it does not prove the
requested geometry was produced, so every part is measured against a closed-form
equivalent before it is reported as built.

## Parts

| Part | Volume (mm³) | bbox (mm) | Gate |
| --- | --- | --- | --- |
| `mast_tube_stock` | 11 333.2955 | 20 × 20 × 130 | matched oracle to 8.0e-16 |
| `root_clamp` | 60 180.4172 | 44 × 56 × 30 | matched oracle to 4.8e-16 |

Both STEP exports were re-imported into CadQuery and re-measured independently:
agreement to 4.8e-16 and 8.5e-16 respectively.

`mast_tube_stock` is 130 mm = 100 mm free length + 30 mm clamp engagement. It is a
**distinct part from `mast_tube`**, which stays at the 100 mm exposed length the
285.5 Hz modal result was computed against. It must not inherit that contract.

## Evidence states

`geometry.json` carries an evidence state per value. Anything marked
`provisional_design` is a designer choice under the register's
`design_then_inspect` acquisition route and **must not be copied into
`cad/roboracer/parameters.csv`** without inspection.

Not modelled, because the register blocks them:

| Parameter | Route | Consequence |
| --- | --- | --- |
| `clamp_bolt_pitch` | measurement | no deck bolt pattern on the clamp |
| `lidar_bracket_bolt_pitch` | vendor_drawing | Part 3 not modelled |
| `optical_center_offset` | measurement | Part 3 not modelled |
| `actual_load_height` | measurement | Part 4 load feature not modelled |

## Use

```bash
~/ENTER/envs/rr-cad/bin/python oracle.py            # refresh expected values
python3 run_host.py author_mast_assembly.py authoring_result.json 600
```

`run_host.py` needs the same host config as engineering-audit's cadloop
(`CADLOOP_HOST_CONFIG`, default `~/.config/sw_pc_credentials.json`).

## Host API findings

These are additional to engineering-audit's `docs/solidworks_api_findings.md` and
were each paid for with a build iteration.

| Finding | Consequence |
| --- | --- |
| `FeatureExtrusion3` rejects a sketch holding two concentric circles. | One closed contour per feature. The tube is a solid cylinder plus a bore cut, not a single annular extrude. |
| A Right Plane sketch at local `(x, y)` lands at global `(Y=y, Z=-x)`, and its extrude runs `+X`. | Measured with `probe_right_plane.py` rather than assumed. The `Z` sign is inverted; guessing it produced a sketch outside the body and a cut that found no material. |
| A cut from a **datum plane** needs `FeatureCut4` argument 3 (`dir_opposite`) set `True`, while a boss extrude from the same plane runs the opposite way. | Cut and boss do not default to the same direction off a datum plane. A cut sketched on a **face** does default into the body. The authoring script tries both directions and records which worked. |
| `swEndCondThroughAllBoth = 9` is rejected on this build. | Use `swEndCondThroughAll = 1` and control direction explicitly. |
| A sketch edge placed exactly **tangent** to an existing feature edge is perturbed. | The slot originally met the bore tangentially and lost 2.579 mm³ against the oracle. Geometry that should intersect must be modelled intersecting, not touching. This was a real design error the gate caught: a tangent slot cannot flex a clamp. |
| `SelectByID2` for a `FACE` at exactly `x = 0` returned false, while selecting the coincident named `Right Plane` worked. | Prefer named planes over face-picking on a plane through the origin. |
