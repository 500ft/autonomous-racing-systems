# Literature

Verified references for the two engineering lanes of this project, plus the measurement work started in
September 2026. Assembled 2026-09-22.

**Start with the [claim ledger](claim-ledger.md).** It maps this repo's own claims to what the literature
supports, what it challenges, and what it forbids. The five domain files are the evidence behind it.

| File | Covers | Entries |
|---|---|---|
| [1. Vehicle dynamics and system identification](01-vehicle-dynamics-and-system-id.md) | F1TENTH platform, single-track model, tire models, parameter identification, sim-to-real | 21 |
| [2. Control and estimation](02-control-and-estimation.md) | Pure pursuit, LQR, MPC, EKF, fair comparison, model mismatch | 21 |
| [3. Structural dynamics and modal testing](03-structural-dynamics-and-modal-testing.md) | Cantilever with tip mass, the hand-calc vs FEA gap, impact testing, accelerometer mass loading | 18 |
| [4. Measurement uncertainty and calibration](04-measurement-uncertainty-and-calibration.md) | GUM, force calibration standards, errors-in-variables regression, ADC resolution, displacement metrology | 23 |
| [5. V&V and mechanical design](05-verification-validation-and-mechanical-design.md) | ASME V&V, grid convergence, stress singularities, bolted joints, thin-wall crushing, tolerancing, materials | 43 |

126 rows in total; three rows in §2 are cross-references to §1 rather than new sources.

## How entries are graded

Two separate decisions, never blended into one score. A highly cited paper that is tangential to this
project is still tangential.

**Aboutness** — is it about a question this project actually faces? Judged on subject matter only.

| Grade | Meaning |
|---|---|
| 3 | Core: directly answers or tests a question this project faces |
| 2 | Relevant: addresses the domain directly |
| 1 | Background: cite once for framing, never as primary support |

**Evidence** — what is behind the claim, not how famous the source is.

| Grade | Meaning |
|---|---|
| A | Replicated experiments, adopted international standard, or an established handbook formula with long experimental backing |
| B | Single well-controlled experiment, validated simulation, or a textbook/agency handbook |
| C | Simulation or model without experimental validation; small-n results; grey literature |
| D | Position paper, survey, preprint claim, or qualitative argument |

A survey graded D is not a bad source. It is a bad source *to cite for an empirical claim*.

Grade A deliberately spans an adopted standard, an established analytical formula and a replicated
experiment. Those are **not interchangeable**: a standard fixes definitions and procedure, a formula
holds under its own assumptions, and an experiment establishes behaviour on its own specimen. Keep
source access, method applicability and physical validation separate when citing, and do not let the
single letter imply that a catalogue entry has the same standing as a measurement. A verified catalogue
record establishes a document's identity and scope, not the content of clauses nobody read.

## Verification policy

Every entry was checked against a publisher page, DOI record, Crossref metadata or official standards
listing that was actually retrieved. **No citation here was generated from memory.**

Each domain file ends with a **"Not verified, deliberately absent"** section. Those sections are part of
the deliverable, not an apology: they record well-known items that could not be confirmed, disputed
bibliographic details, and places where **no governing literature exists**. Three such gaps are real and
load-bearing:

- No standard governs cantilever compliance testing at this scale, and no published sub-30 µm static
  deflection uncertainty budget was found.
- No standard or handbook mandates an internal sleeve when clamping thin-walled tube. The sleeve must be
  argued from mechanics and validated by test.
- No literature was found on sensor-mast vibration for 1/10-scale racing platforms.

**Paywalled standards carry no clause numbers anywhere in this folder.** Designation, title, edition and
scope were verified from official listings; clause content was not read and must not be cited without
buying the document.

## What this folder does not do

It changes nothing. No ledger row, threshold, protocol, parameter or acceptance criterion is modified by
anything written here. Several entries identify conflicts between adopted practice and this repo's frozen
[physical protocol](../docs/specs/mast-physical-validation/design.md) — most sharply the `R² ≥ 0.99` gate
and the use of ordinary least squares for a slope whose both axes carry uncertainty. Acting on those is a
**prospective, owner-reviewed amendment**, per the same rule that governs every other change to a frozen
protocol in this repo.

Reading literature is not evidence of anything physical. Nothing here has been measured.

## Adding an entry

Keep the two grades separate, verify the source before adding it, and say why it matters **to this
project** rather than summarising it generically. If a claim in the final report has no entry in the claim
ledger, either add the entry or delete the claim.
