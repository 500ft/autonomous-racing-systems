# CAD review disposition — 2026-09-06

## Merge policy: pending owner decision

The reviewer supplied two blocking policy questions. The prior cleanup is verified in Git history for P-V, Drone, RoboRacer and Enclosure. This amendment does not silently reverse it. All five CAD PRs are draft; no merge is authorized until Owner records whether main admits planning ledgers or only reviewer-facing engineering contracts.

Current conservative disposition: keep task ledgers on the unmerged planning branch and remove the newly added README promotion. If Owner selects contracts-only, extract parameter/interface/inspection/verification contracts into a clean main-targeted change and keep task statuses outside main. Reconcile the prerequisite integrity PRs too; their sprint ledgers remain byte-preserved here, so merging those unchanged would reintroduce the same policy problem. No private repository was created and a public branch is not private storage.

## Accepted engineering amendments

Mast/root-clamp and metrology fixture first; deck packaging is deferred. New fixture-readiness design conditions are prospective, not claimed as part of the July freeze. Existing verdict thresholds stay unchanged.

Code-CAD/CI is now an explicit selected workflow and separately estimated task, not an already implemented test. Cross-ledger prerequisites are recorded in [CAD_DEPENDENCIES.json](CAD_DEPENDENCIES.json); the embedded validator checks references and prevents a task entering todo/in_progress/done with unverified prerequisites. Checks establish metadata consistency, not authentic external approval.

## Inputs and limits

The pasted review was available and checked against local files/current PR heads. The two artifact attachment links in the user message were not available as local files; their additional unpasted punch-list items have not been claimed reviewed. No CAD models or scientific measurements were made in this amendment.


## 2026-09-12 — fixture-contract reconciliation (sprint task 4)

Two implementations of the fixture geometry contract were written independently on 2026-09-11
and touched the same four files: **PR #17** (`fix/evidence-gaps-20260911`, merged to `main`) and
**PR #16** (`audit/fixture-contract-tap-prereg-20260911`, open, conflicting).

| | PR #17 (main) | PR #16 |
|---|---|---|
| model | reviewed-target schema + observation comparator (`--check-draft`, `--geometry`) | clauses derived from `parameters.csv` + release gate (`--check`, `--release`) |
| what it catches | CAD observations outside reviewed tolerances | contract disagreeing with the register; pending inputs presented as filled |
| what it lacks | nothing binds the null targets to the register | no observation comparison; no reviewed tolerances |
| tests | 6 (parametrised → 23) | 8 |

**Decision: one file, one checker, both halves kept.** `cad/roboracer/fixture-contract.json` keeps
#17's schema as the authoritative committed contract (it is merged and referenced by RR-CAD-09,
`COMPLETION_RECONCILIATION.md` and `fixture-preparation.md`). #16's register engine is folded into
the same checker as a `derived_from_register` section: `--refresh` regenerates it, `--check` fails
when it is stale, and `--release` refuses (exit 2) unless the review fields and every target are
filled **and** no derived clause is pending. #17's modes are byte-for-byte unchanged. Tests: all of
#17's kept, #16's ported onto the merged schema (33 pass), including a new control showing that
filling only the review fields still refuses on the five pending register rows.

**Disposition of PR #16: closed as superseded, not merged.** Its contract half is now on `main`
through this reconciliation. Its second half — `experiments/tap_test_prereg.py`,
`docs/specs/mast-modal-tap-test/preregistration.md`, `cad/roboracer/modal-inputs.csv` — is **not
carried**: it deletes #17's `docs/specs/mast-physical-validation/modal-preregistration.md` and
`modal-freeze.json`, and the sprint plan keeps the numerical modal freeze as a separate item
(RR-S11). Whether the tap-test generator should regenerate #17's modal document is a separate
decision, recorded as open under RR-S11; nothing about the modal target (285.5 Hz FEA / 330.1 Hz
hand, not the rejected 174.7 Hz baseline) changes here.

Verification: `python cad/fixture_contract.py --check` current; `--release` REFUSED with 16
named blockers; `--check-draft` DRAFT_BLOCKED; `pytest cad/tests/test_fixture_contract.py` 33
passed. `test_geometry.py` needs the pinned CadQuery environment and is unaffected.

### Same-day repair after review (2026-09-12)

The review reproduced `--release` returning RELEASABLE with `evidence_state=not_evidence` rows carrying
empty sources, placeholder review strings (`TBD`, `?`, `x`), all indicator positions missing and no bolt
tolerance. Reproduced here. Cause: `release_blockers` checked presence, not validity, and `--geometry`
ran its own, different field checks.

Fix: one `complete_contract_blockers()` shared by `--release` and `--geometry`. It rejects placeholder
strings in every review field and source, requires every indicator position and a positive bolt
tolerance, checks tolerances are positive and smaller than their targets, checks the tube targets are
numerically consistent (wall < OD/2, volume matches OD/wall/length within tolerance), validates bolt
coordinates as x/y/z, and requires every register row to be at a release-grade evidence state
(`inspection`, `drawing`, `calibration_record`, `owner_decision`, `protocol`). The register loader
refuses evidence states outside an explicit allowed set and any non-pending row without a source.
The passing verdict is renamed `CONTRACT_COMPLETE` and printed with the statement that geometry
comparison and physical validation are separate gates and not claimed. 44 tests pass, including six on
the review's reproductions and five byte-pin-free ledger rules (`test_cad_ledger_rules.py`) that carry
the purpose of the embedded validator without pinning `SPRINT_TASKS.csv` to a snapshot.

### Review 2 repair (2026-09-13)

Review 2 supplied a register mast length of 100 mm with a contract and matching CAD observations at
1000 mm (volume adjusted); the checker reported no blockers and accepted the geometry comparison,
because it checked consistency within each representation, not agreement between them. It also found
`--geometry` ignoring `--parameters`, and revision `A3` rejected merely for being short.

Fix: `SHARED_QUANTITIES` (mast length, OD, wall, clamp engagement, bolt pitches, optical offset, load
height, station spacing) are bound — the contract target must equal the register value within the
contract's own tolerance, in `complete_contract_blockers()` and therefore in both `--release` and
`--geometry`; `--geometry` passes the selected register through; placeholder detection is an explicit
vocabulary only. Tests: the review's 100/1000 mm case fails; a valid custom register passes `--geometry`
from the CLI while the same contract fails against the committed pending register; `A3` is accepted.

The shared CAD-ledger validator is consolidated into `cad/ledger_validator.py` (`live` = every old
semantic rule including cycle detection and the old negative controls, plus the review's cycle between
two done tasks; `historical` = the SPRINT_TASKS.csv byte comparison as a report). The weaker
`test_cad_ledger_rules.py` from the first repair is removed; `test_ledger_validator.py` replaces it.

## 2026-09-16 — RR-S11 follow-up closed: PR #16 tap-test generator not carried (Day-4 A1)

Owner decision (Day-4 plan O1): **`closed`**. `experiments/tap_test_prereg.py`,
`docs/specs/mast-modal-tap-test/preregistration.md` and `cad/roboracer/modal-inputs.csv` from PR #16
stay out of `main`. The reviewed draft procedure `docs/specs/mast-physical-validation/modal-preregistration.md`,
the freeze schema `modal-freeze.json` and `cad/modal_freeze.py` remain the single source; nothing in them,
in the sprint ledger row RR-S11 (done) or in RR-S12/RR-S13 (blocked) changes. Reopen only with a concrete
use for deterministic regeneration, as a new sprint row.

## 2026-09-16 — Proposed staging amendment for RR-CAD-06 / RR-CAD-07 (for review, not applied)

The Day-4 plan flags that RR-CAD-06 mixes two events: preparing the geometry-to-FEA and inspection handoff
(nominal exports, boundary map, inspection sheet) and the later post-inspection as-built reference freeze.
RR-CAD-07 depends on RR-CAD-06, so read literally the fabrication pack cannot be released until a specimen
has been built and inspected from it.

Proposal, to be applied as one reviewed ledger edit before either row activates:

| row | keeps | moves out |
|---|---|---|
| RR-CAD-06 | nominal STEP + boundary map + inspection sheet; datum/material/ideal-vs-detailed record; `reference_commit` and `source_commit` fields defined but unfilled | the "after fabrication/inspection, commit AS-BUILT prediction before any load" clause |
| RR-CAD-07 | fabrication pack release from a reviewed RR-CAD-06 handoff; second-reviewer reproduction | nothing; still blocked on RR-CAD-04/05/06 |
| RR-S02 (existing, Owner) | gains the moved clause as an explicit prerequisite: axis-specific as-built prediction and inspection-linked reference committed and pushed before campaign loads, `test_started_at` after both commits | — |

Freeze-before-loading is preserved word for word, only its home changes. No threshold, tolerance or
evidence criterion changes. Not applied here: the ledger validator would accept the edit, but the plan
requires Owner review of the amendment first.
