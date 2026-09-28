# 03 — Operator's guide

How to run everything, what each gate protects, and how to decide what is next without asking anyone.

---

## Environments — there are four, and they do not mix

| Environment | For | How |
|---|---|---|
| **Portable** (Python 3.10) | evidence checks, calibration, logger, feasibility screen | system python3; the CI path |
| **Pinned CAD** (Python 3.11.16, CadQuery 2.8.0) | `cad/generate.py`, `cad/tests/test_geometry.py` | `conda create -n racing-cad -c conda-forge --file cad/requirements.lock` |
| **FEA** | `experiments/mast_fea.py`, the modal study | gmsh in conda `base`, CalculiX `ccx` in conda env `fea` |
| **Legacy Gym** (Python 3.9) | closed-loop simulation, controller sweeps | `conda env create -f environment.yml` |

Do not combine them. A test asserts the CAD environment matches its lock file so drift cannot pass silently.

---

## The checks, and what each one actually protects

Run from the repository root.

### Always-safe, no hardware, seconds

```bash
python3 cad/ledger_validator.py live      # task-ledger rules + every relative markdown link
python3 cad/nominal_inventory.py --check   # 30 headline numbers still appear in their sources
python3 cad/input_requests.py --check      # the generated request sheet is not stale
python3 scripts/build_week_manifest.py --verify   # 22 artifacts match their recorded hashes
```

| Check | Protects against |
|---|---|
| `ledger_validator live` | A task marked done without evidence; a dependency cycle; a broken link. It also rejects nine deliberate invalid mutations, so the checker itself is tested |
| `nominal_inventory --check` | A headline number quietly changing, or a document drifting from the source it describes |
| `build_week_manifest --verify` | Evidence being edited after it was frozen. Negative-controlled: appending one line to a listed file makes it fail by name |

### Test suites

```bash
PYTHONPATH=gym python3 experiments/test_mast_physical_validation.py   # the frozen campaign evaluator
PYTHONPATH=gym python3 experiments/test_final_report.py               # report claims trace to artifacts
PYTHONPATH=gym python3 experiments/test_cad_inputs.py
python3 experiments/test_load_cell_calibration.py                     # 25 tests
python3 experiments/test_measurement_logger.py                        # 9 tests
python3 cad/tests/test_fixture_feasibility.py                         # 39 tests
python3 cad/tests/test_modal_attachment.py                            # deck invariants + study guards
python3 cad/tests/test_unattended.py                                  # host dialog suppression, offline
python3 experiments/drivetrain_excitation.py --self-check
```

### Expected refusals — exit code 2, and that is correct

```bash
python3 cad/fixture_feasibility.py     # UNKNOWN: no fixture exists, so its stiffness is undeclared
python3 cad/fixture_contract.py --release   # REFUSED: register rows still pending
python3 cad/modal_freeze.py            # REFUSED: modal inputs unresolved
```

**Never "fix" these by making them pass.** They are the design working. An expected refusal is a third
category, distinct from a pass and from a crash, and the manifest records it that way.

### Heavy, opt-in

```bash
# pinned CAD env
python cad/generate.py --parameters cad/roboracer/parameters.csv --output /tmp/cad-out
python -m pytest cad/tests -q

# FEA env — writes to runs/mast_fea/, which is committed evidence
python experiments/mast_fea.py
python3 experiments/modal_attachment_study.py     # three-case comparison, ~10 min

# host CAD, no monitor needed
cd cad/solidworks && python3 run_host.py author_mast_assembly_doc.py assembly_result.json 900
```

---

## The blocker map — what is actually stopping what

Everything below needs an **owner input or a physical measurement**. No code unblocks them.

```
RR-CAD-02  interface records, drawings, instruments, bench, lead time
   │
   ├──> RR-CAD-04  mast/clamp/bracket model ──> RR-CAD-05  two-axis fixture
   │                                              │
   │                                              └──> RR-CAD-06/07  handoff, release pack
   │
   └──> the six pending register rows ──> fixture_contract --release stops refusing

RR-S12  inspected as-built reference, calibration uncertainty, approved band ──> RR-S13  modal analysis
RR-S02  apparatus, calibration records, zero checks, authorisation
RR-S09  a named independent reviewer, and actual written feedback
```

**Status:** CAD ledger 4 done / 5 blocked / 1 deferred. Sprint ledger 10 done / 4 blocked.

### The three input bundles, in priority order

Ranked from the decision screen's own sensitivity output, not from opinion:

1. **Displacement and root-motion chain** — model, serial, range, resolution, mounting sketch, tip and
   root station coordinates, calibration source. Replaces the assumed repeatability and rotation terms and
   decides observability. **Highest leverage**, because resolution and station spacing outrank
   repeatability, and because root motion is the error no gate catches.
2. **Force-chain calibration records** — cell and ADC identifiers, reference masses with uncertainties,
   mounting, gravity basis, zero/creep/drift and ascending/descending raw readings. Replaces the shared
   gain assumption. The 5 kg cell is a candidate only; the 1 kg cell cannot reach 20 N.
3. **Mechanical interfaces** — the six pending register values with coordinates, units, tolerance, source
   and acquisition route, plus one LiDAR vendor drawing.

---

## Decisions waiting on you

| Decision | Why it is blocking | What each choice costs |
|---|---|---|
| **R² route** | With gates enforced, the assumed 0.5 µm repeatability gives median R² 0.986 against the frozen 0.99 — the nominal configuration reports NOT PLAUSIBLE | Either budget indicators near 0.3 µm, or advance the adequacy proposal to replace the R² component. They are not exclusive |
| **Modal headline** | The corrected attachment gives 320.87 Hz but is not adopted | Adopting it needs its own mesh-refinement study under the declared convergence rule |
| **Modal guard basis** | Its drivetrain half is unjustified | Either re-derive from a real excitation spectrum, or restate it as a control-rate guard with the drivetrain question open. Widening the band to pass is not an option |
| **Dependabot** | numpy 2.5.3 and scipy 1.18.1 both need Python ≥ 3.12; CI pins 3.10 | Close them with a documented disposition, or add ignore rules. A major-only rule will not catch the scipy minor |

---

## Working conventions that will save you

- **Plan then implement.** The pattern in this repo is an owner-written `.txt` handoff, then an
  implementation PR. Plans and critiques live in `docs/`; the implementation answers them.
- **Never edit a generated artifact by hand.** Fix the generator so the change appears on the next
  legitimate run and the artifact keeps its provenance link. A wording fix in `mast_tolerance_stack.py`
  was handled this way rather than editing the committed output.
- **Regenerate dependent evidence when inputs change.** The manifest verifier will tell you; it caught
  three legitimate drifts after two PRs merged.
- **A missing input is UNKNOWN, never zero.** Any unknown makes the whole screen unknown. This is the rule
  that keeps the screen honest.
- **Gate on every check you compute.** Both of the worst bugs in this repo were a number calculated,
  displayed, and then ignored by the verdict.
- **Vary one factor at a time**, and report the confounded comparison separately so nobody mistakes it for
  a single effect.

### Host CAD notes, hard-won

The SOLIDWORKS host has no monitor, so a modal dialog is a hang. `cad/solidworks/unattended.py` disables
the "Input dimension value" prompt (`swUserPreferenceToggle_e` id **10**) and restores it afterwards —
**host-verified**, a real run returned `applied: true` with the prompt previously on.

| Trap | What to do |
|---|---|
| `AddComponent5` returns `None` and raises nothing | Use `AddComponent4`. A silent `None` is not a missing file or an inactive document |
| `AddComponent4` ignores the x/y/z you pass | Insertion coordinates are not placement. Set the transform afterwards and **read it back** |
| `EditRebuild3` is a property, not a method | Same trap as the `GetX` family; handle both forms |
| Preference 70 returns the templates *directory* | Require `os.path.isfile`. The template is `Assembly.ASMDOT` |
| Early binding is unavailable | Enum values must be numeric; look them up, never recall them |

Current assembly status is **PARTIAL**: three components and three mates, but placement does not match
intent and per-component volumes are unread. Open item: set transforms explicitly, then re-read.

---

## If you only do one thing next

Weigh nothing, measure nothing, decide nothing — just **answer the R² question**. It determines whether
the compliance campaign is feasible as specified, and everything downstream of the feasibility screen is
waiting on it. Everything else in the blocker map needs hardware you do not yet have.
