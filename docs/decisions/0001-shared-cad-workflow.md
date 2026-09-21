# Use the shared CAD briefing for RoboRacer planning

Status: Adopted planning guidance, 2026-09-21, at the user's request. This record
does not approve a physical design, release fabrication, or assert a new host run.

## Context and sources

The user supplied `500ft/engineering-audit → docs/cad_agent_briefing.md` as the
handoff to consider going forward. The reviewed source is
[the briefing at cf56cdf](https://github.com/500ft/engineering-audit/blob/cf56cdff50b09c9a266292006cbf5b2a0f2e8ac6/docs/cad_agent_briefing.md).
The same revision contains `docs/host_setup.md` and
`docs/solidworks_api_findings.md`. Read the current briefing for future work and
record changes from this baseline; host-specific observations are not universal
API guarantees.

Repository references fetched and inspected on 2026-09-21:

- Racing main: `17c69c1c3571f597be22970ebad33aceb9183e97`.
- Native CAD branch `cad/solidworks-mast-assembly`:
  `6ef5f4469fbb5c2d2366533eb4e56ac37c7c6e53`.
- Weekly implementation branch `week/day1-20260919`:
  `ea901d51d659b95e78061e62885a3b7eca19451a`.

The native branch contains a
[README](https://github.com/500ft/autonomous-racing-systems/blob/6ef5f4469fbb5c2d2366533eb4e56ac37c7c6e53/cad/solidworks/README.md),
`geometry.json`, `oracle.py`, `contract-assembly.v1.json`, and
[a recorded parameter-change result](https://github.com/500ft/autonomous-racing-systems/blob/6ef5f4469fbb5c2d2366533eb4e56ac37c7c6e53/cad/solidworks/redrive_result.json).
Tube stock, the internal support sleeve and root clamp are existing branch work,
not tasks to author again from scratch. The weekly branch contains E0 inventory
and hookup notes. These observations do not assert either branch is merged, all
checks pass now, or a host is currently reachable.

## Decision

Keep reusable CAD/FEA orchestration in `engineering-audit`. Keep the RoboRacer
deliverable, nominal geometry inputs, contracts and evidence here. Reuse the
existing native-authoring path before proposing another pipeline.

Keep two model scopes distinct:

- `cad/generate.py` and `cad/contract.json`: the frozen 100 mm analysis specimen.
- `cad/solidworks/geometry.json` and `contract-assembly.v1.json`: native assembly
  parts. Recorded stock is 135 mm total: 100 mm free length and provisional 35 mm
  engagement. It is a different part from the specimen.

The prior 285.5 Hz result belongs to its original tube/mass/boundary-condition
model. It is not an assembly modal result merely because the parts share an OD
and exposed length. The sleeve and clamp need explicit joint/load-path and
mass-distribution treatment before an assembly analysis is meaningful.

Use one geometry input with per-value evidence states for native authoring and
an independently implemented oracle. Hand-check the oracle. Require measured
geometry, a variable-change/rebuild check and STEP round-trip evidence. Add
location/clearance/topology checks: correct volume alone cannot establish correct
hole placement. Missing oracle results and host evidence remain unverified.

Use contract tolerances with stated units and purpose. Near-machine-precision
agreement in a numerical run is not a fabrication tolerance or physical accuracy
claim. Preserve the frozen specimen contract.

Respect acquisition routes: `design_then_inspect` permits a provisional design
choice but still needs subsequent inspection; `vendor_drawing` needs its source
drawing; `measurement` needs measurement. Route amendments are prospective and
documented. Do not promote geometry-file choices into the owner register silently.

## Consequences for the next tasks

1. Reconcile existing branches and evidence before building. Preserve work
   already done and report dependencies in Claude's implementation PR.
2. Extend clamp parametrization: slot/bolt-hole positions remain authored
   coordinates. Test actual position changes, clearances and invalid ranges;
   the recorded 35→40 mm engagement run proves only its scope.
3. Develop assembly documents/mates when interfaces are resolved. Individual
   part files are not a mated assembly or an assembly STEP export.
4. Keep blocked bracket/deck/load interfaces absent from the accepted model.
   Isolate any conceptual study so it cannot enter a release contract.
5. Before trusting reusable FEA outputs, plan an independent benchmark/check of
   boundary conditions, load/resultant, reactions, displacement, reportable stress
   and convergence. A finite plate with a hole cannot be validated by blindly
   requiring an infinite-plate stress-concentration value. Reusable verification
   belongs with that FEA machinery; mast-specific applicability stays here.
6. Treat dimensioned drawings and tolerance review as unfinished work. Previews
   and numerical CAD equality do not constitute manufacturing approval.

Equipment-driven E1–E3 acquisition/calibration software remains the weekly
priority. This guidance changes subsequent CAD scope and verification; it does
not add a second mandatory host/FEA project to the week.

## Alternatives considered

Rebuilding the clamp in another CadQuery assembly generator would duplicate
native branch work and create another geometry source. Extending the frozen
specimen contract to assembly stock would obscure the original analysis identity.
Screenshots and solver completion would leave recorded silent failures undetected.
The existing separated paths with independent checks avoid those problems.

## Validation of this planning update

Read source files and recorded result JSON; inspected fetched branch references.
No CAD authoring, host connection, solver execution, calibration or physical test
was performed. Ledger states and source code were not changed.
