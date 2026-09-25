# Reviewer packet — week of 2026-09-19

**Ready for review. Not reviewed.** Nothing here has been seen by an independent reviewer, and no
physical measurement, calibration or campaign took place this week.

Start with [`manifest.json`](manifest.json): every artifact with its SHA-256, role and evidence kind,
every check with its expectation, and a named list of what was **not** executed. Verify it with

```bash
python3 scripts/build_week_manifest.py --verify
```

That re-hashes all 22 listed artifacts and exits non-zero on any drift. It was negative-controlled:
appending one line to a listed file makes it fail, and restoring the file makes it pass.

## What a reviewer can reproduce without hardware

```bash
python3 cad/decision_screen.py --output /tmp/screen      # W3.2 scenarios, seed 20260925
python3 cad/fixture_feasibility.py                       # EXPECTED REFUSAL, exit 2: terms UNKNOWN
python3 cad/tests/test_fixture_feasibility.py            # 39 tests
python3 experiments/test_load_cell_calibration.py        # 25 tests
python3 experiments/test_measurement_logger.py           # 9 tests
python3 cad/nominal_inventory.py --check                 # traceability of 30 headline numbers
```

Everything above is standard library. No device, no solver, no network.

**An expected refusal is not a failure.** The feasibility screen exits 2 because no fixture exists, so
its terms are UNKNOWN. The fixture contract and modal freeze also exit 2 by design. The manifest records
these as their own category, distinct from a pass and from a crash.

## Reading order

| Document | What it is for |
|---|---|
| [W1.8 nominal report](../../docs/W1_8_NOMINAL_REPORT.md) | The scoped claim/evidence/limitation table. **Start here for the engineering picture** |
| [decision screen](decision_screen/) | Why the three input requests are the three that matter, with the scenarios behind them |
| [input requests](decision_screen/input_requests.md) | What to send back, in what format, and what each unlocks |
| [adequacy proposal](../../docs/decisions/compliance-adequacy-proposal.md) | A prospective replacement for the R² component. **Unapproved**; the frozen rule stands |
| [modal audit](../../docs/design/MODAL_MODEL_AUDIT.md) | What the modal model actually contains, and the three-case attachment result |
| [claim ledger](../../literature/claim-ledger.md) | Every claim mapped to support, counter-evidence and confidence |

## The two results most worth a reviewer's attention

**A passing median is not campaign reliability.** At 0.3 µm assumed repeatability the median R² is
0.9925 — passing the frozen rule — while about one simulated single-axis campaign in seven is rejected
and roughly one two-axis campaign in four fails on at least one axis. The screen now gates on the
simulated pass fraction. The two-axis figure shares the force-calibration gain across both axes, because
one calibration serves both; the product of per-axis fractions is deliberately not reported.

**Both frozen numerical gates can pass while the answer is 19 % wrong.** A synthetic 0.00025 mm/N
uncorrected, load-proportional root rotation biases the fitted slope by 19.4 % while median R² is 0.9947
and relative U95 is 3.3 %. No amount of repetition detects it, and no fit statistic can. Root-motion
observability is a correctness requirement on the apparatus.

## Status of each ledger gate

Unchanged by this week's work, and unchanged **by** this packet:

- **RR-CAD-02, 04, 05, 06, 07** — blocked. No interface records, no drawings, no inspected register.
- **RR-S02, RR-S09** — blocked. No readiness records, no named reviewer.
- **RR-S12, RR-S13** — blocked. The tap test is a draft; this week's modal work is solver-only and
  adopts no frequency.

No ledger row was promoted, and none may be promoted on the strength of a planning document, a purchased
item or a software-only check.

## Honest limits

Every physical term in the decision screen is **assumed**. No instrument has been characterised, no
fixture exists, and the firmware has never run on a board. The modal study compares three declared model
definitions against each other; it establishes nothing about hardware and adopts no new headline
frequency, because a new coupling invalidates reuse of the existing mesh-convergence evidence.
