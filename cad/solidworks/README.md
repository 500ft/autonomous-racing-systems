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
| `mast_tube_stock` | 11 769.1915 | 20 × 20 × 135 | matched oracle to 6.2e-16 |
| `support_sleeve` | 5 148.7464 | 16.95 × 16.95 × 35 | matched oracle to 1.8e-16 |
| `root_clamp` | 70 582.7292 | 44 × 56 × 35 | matched oracle exactly (0.0) |

`mast_tube_stock` is 135 mm = 100 mm free length + 35 mm clamp engagement. It is a
**distinct part from `mast_tube`**, which stays at the 100 mm exposed length the
285.5 Hz modal result was computed against. It must not inherit that contract, and
`cad/tests/test_solidworks_assembly_contract.py` asserts the two contracts differ.

`support_sleeve` exists because spec §6.1 requires an internal support over the
clamped length: a 1.5 mm wall under a 16 N·m seating torque is unvalidated, and a
crushed root changes I locally, softening exactly the region the hand calculation
and the FEA both assume is rigid. Clamping directly on the tube wall is the failure
mode it prevents.

## Parametric, and verified so

Every part's governing dimensions are driven by declared global variables, and the
tube's bore is an expression (`"TubeOD" - 2 * "TubeWall"`) rather than a number, so
wall thickness drives the bore as design intent says it should.

Equations existing is not evidence. An equation can be accepted by `Add2` and drive
nothing. `redrive.py` is the acceptance test: it changes one global variable in the
saved parts, rebuilds, and measures against an oracle built for the new value.

Recorded run, `ClampEngagement` 35 → 40 mm:

| Part | Before (mm³) | After (mm³) | New oracle (mm³) | Error |
| --- | --- | --- | --- | --- |
| `mast_tube_stock` | 11 769.1915 | 12 205.0875 | 12 205.0875 | 1.0e-15 |
| `support_sleeve` | 5 148.7464 | 5 884.2816 | 5 884.2816 | 0.0 |
| `root_clamp` | 70 582.7292 | 81 076.5195 | 81 076.5195 | 1.8e-16 |

One variable change propagated through all three parts. `redrive.py` saves nothing,
so the parts on disk keep their authored 35 mm values.

Slot and bolt-hole **positions** are still authored coordinates, not driven
dimensions. Changing `ClampEngagement` moves the block depth correctly but leaves
the bolts where they were placed; beyond roughly 45 mm engagement they would need
repositioning. That is the remaining parametric gap.

## Which pipeline owns what

The repository now has two CAD paths, and they do not overlap:

| | `cad/generate.py` | `cad/solidworks/` |
| --- | --- | --- |
| Tool | CadQuery | SOLIDWORKS on the licensed host |
| Owns | the frozen 100 mm analysis specimen | the as-designed assembly |
| Contract | `cad/contract.json` | `cad/solidworks/contract-assembly.v1.json` |
| Runs in CI | yes, fully | oracle and contract only; authoring needs the host |

`cad/contract.json` stays frozen: it is what 285.5 Hz was computed against.
CI cannot run SOLIDWORKS, so what it holds for this directory is the *reference* the
host run is gated against — if `geometry.json` or `oracle.py` drifts, the contract
stops matching and the gate would silently weaken.

## Evidence states

`geometry.json` carries an evidence state per value. Anything marked
`provisional_design` is a designer choice under the register's
`design_then_inspect` acquisition route and **must not be copied into
`cad/roboracer/parameters.csv`** without inspection.

Not modelled, because the register blocks them:

| Parameter | Route | Consequence |
| --- | --- | --- |
| `clamp_bolt_pitch` | measurement | no deck bolt pattern on the clamp |
| `root_rotation_station_spacing` | design_then_inspect | chosen 40 mm, Part 4 not modelled |
| `lidar_bracket_bolt_pitch` | vendor_drawing | Part 3 not modelled |
| `optical_center_offset` | measurement | Part 3 not modelled |
| `actual_load_height` | measurement | Part 4 load feature not modelled |

## Use

```bash
~/ENTER/envs/rr-cad/bin/python oracle.py                       # refresh expected values
python3 run_host.py author_mast_assembly.py authoring_result.json 900
python3 run_host.py redrive.py redrive_result.json 700         # prove it is parametric
```

`run_host.py` needs the same host config as engineering-audit's cadloop
(`CADLOOP_HOST_CONFIG`, default `~/.config/sw_pc_credentials.json`).

## Unattended host (no monitor, no operator)

The host has no display and nobody to click a dialog, so a modal prompt is a hang. `sw.Visible = False`
hides the window but does not stop SOLIDWORKS asking for values.

[`unattended.py`](unattended.py) disables **"Input dimension value"** (`swUserPreferenceToggle_e`
id 10) before authoring and restores the host's own setting afterwards. With that option on, every
`AddDimension2` call raises a modal Modify box waiting for a number, so an unattended run blocks at the
first dimension with no error and no output. Disabling it makes SOLIDWORKS take the value the script
already passes; the dimension is not guessed, only the confirmation click is removed.

The toggle is **read back after writing** and the outcome recorded under `"unattended"` in the result
JSON, because the identifier is cross-checked against three independent sources but has not yet run on
this host. Check that field on the next host run: `applied: true` means it worked. If it is false, the
journal says why, and the fallback is to clear Tools > Options > General > "Input dimension value" once
on the host by hand.

Scope, stated rather than implied: this disables that prompt and nothing else. It is not a general
suppress-all-dialogs switch and no such switch is claimed. A licence, template or graphics failure will
still block, and `run_host.py`'s polling timeout is what catches that. A host with no monitor also needs
its interactive session to stay logged in and unlocked for the COM server to start at all.

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
