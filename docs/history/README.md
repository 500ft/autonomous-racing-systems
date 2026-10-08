# Preserved studies and physical work

The active question and qualification result are in the [roadmap](../../ROADMAP.md).
The studies below retain their result paths so code, links and provenance
stay reproducible. They supply history and reusable tools; their former next
steps do not authorize work under the ranking-refusal question.

| Retained work | Evidence and limits |
| --- | --- |
| Public command response | [Development report](../../reports/real_command_response.md), [split result](../../reports/driving_split_qualification.md). Same-run fitting; session provenance did not qualify a final group. Unopened bags remain unopened. |
| Vehicle model and controllers | [Historical integrated report](../../reports/final_report.md), [figure sources](../data-and-figures.md#historical-figure-sources). Simulator consistency and comparisons remain useful software studies. |
| Mast calculations and attachment audit | [Mechanical analysis](../design/16_mechanical_design_analysis.md), [modal audit](../design/MODAL_MODEL_AUDIT.md), [FEA setup](../design/FEA_SETUP.md). Retain historical and unconverged alternate results separately. |
| Nominal CAD | [Inventory](../CAD_ITEMS.md), [frozen tube contract](../../cad/contract.json), [native SOLIDWORKS work](../../cad/solidworks). No released physical mount or deck follows from these models. |
| Measurement preparation | [Static protocol](../specs/mast-physical-validation/design.md), [fixture preparation](../../cad/roboracer/fixture-preparation.md), [calibration tooling](../../experiments/load_cell_calibration.py). Physical scope awaits D2. |
| Prior weekly work | [Sprint log](../SPRINT_PROGRESS.md), [review log](../REVIEW_READY.md). Historical records, not the current plan. |

The old scale-transfer, mast/deck and fleet proposals are superseded as active
software questions. [Open questions](../OPEN_QUESTIONS.md) preserves their
unanswered physical, scope and disposition decisions. No historical output or
useful CAD was deleted or regenerated in the qualification task.

## Retired entrypoints and plans

The owner adopted the dependency roadmap and authorized this cleanup. The
[pre-cleanup tree](https://github.com/500ft/autonomous-racing-systems/tree/4ef596ad1e824fd6d0873ac94346a8064ed51205) preserves retired source and context:

- Removed the CAD work-order plan, its dependency configuration and the
  CAD-development scope draft. Their schedule-driven validator and validator
  tests had no geometry or measurement consumers, so they are removed too.
  The geometry workflow keeps its actual geometry tests and no longer fetches
  full history solely for that retired metadata check.
- Removed the nominal-package work order and the mast release/order/fabricate
  execution plan. Their proposed work and old modal/deck criteria cannot
  authorize a campaign or define the current finish line.
- Removed the unused simulation/mast concept SVG and its specific accessibility
  assertion. Local-link, image-alt-text and identity checks remain active.
- Removed the reviewer-packet creation entrypoint and its stale campaign check
  list from `scripts/build_week_manifest.py`. `--verify` remains read-only for
  the committed historical manifest. Historical command lists that mention the
  retired ledger checker must be reproduced from the pre-cleanup tree.

[CAD task records](CAD_TASKS.csv), [sprint task records](SPRINT_TASKS.csv) and the
[executed metadata-check report](CAD_PLAN_CHECKS.md) are retained here. The CSV
bytes are unchanged. Their embedded paths and commands describe their original
tree, including plans already removed in earlier cleanups; they are not live
work queues. Historical evidence links now point to these records or immutable
pre-cleanup sources.

### Retentions after consumer tracing

- Keep `cad/generate.py`, `cad/contract.json`, SOLIDWORKS sources, parameter and
  fixture contracts, geometry tests and input checks. They reproduce retained
  geometry and preserve unresolved inputs; removing their checks would weaken
  that evidence.
- Keep hand/FEA/modal generators, original solver outputs, correction reports,
  simulation baselines and evidence-backed figures. They are required to audit
  the old results, without promoting mast success into the current question.
- Keep calibration, logging and compliance analyzers and their tests. Their
  synthetic rejection controls and measurement formats remain useful. The
  frozen protocols and readiness requirements are provenance, not permission
  to fabricate or acquire measurements.
- Keep completed implementation specifications that contain design and
  execution evidence. The [specification index](../specs/README.md) labels them
  as records instead of offering a competing plan.
- Keep the structural archive result, source/license records and unopened bags
  unchanged. No data qualification or research campaign was rerun for cleanup.
