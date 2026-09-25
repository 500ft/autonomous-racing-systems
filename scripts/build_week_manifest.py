#!/usr/bin/env python3
"""Build and verify the week-2026-09-19 reviewer manifest (closeout T5).

    python3 scripts/build_week_manifest.py --write     # hash the listed artifacts, write the manifest
    python3 scripts/build_week_manifest.py --verify    # re-hash and report any drift

The manifest excludes itself from its own hash set, and says so. Nothing tries to embed a commit's own
SHA in a file that changes that commit.
"""
from __future__ import annotations

import argparse, hashlib, json, subprocess, sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "evidence" / "week-2026-09-19"
MANIFEST = OUT / "manifest.json"

# role: what the artifact is. kind: what sort of evidence it carries. Never "measured" anywhere.
ARTIFACTS = [
    ("cad/fixture_feasibility.py", "analysis source", "software"),
    ("cad/decision_screen.py", "analysis source", "software"),
    ("cad/nominal_inventory.py", "analysis source", "software"),
    ("experiments/load_cell_calibration.py", "analysis source", "software"),
    ("experiments/measurement_logger.py", "analysis source", "software"),
    ("experiments/mast_physical_validation.py", "frozen campaign estimator", "software"),
    ("firmware/measurement_node/code.py", "device firmware", "software (NOT device-tested)"),
    ("docs/hardware/purchased-instruments.json", "equipment inventory", "purchase record"),
    ("docs/hardware/measurement-data-format.md", "acquisition format", "specification"),
    ("docs/hardware/load-cell-calibration-protocol.md", "protocol", "specification (conditional)"),
    ("docs/decisions/compliance-adequacy-proposal.md", "prospective proposal", "unapproved proposal"),
    ("docs/W1_8_NOMINAL_REPORT.md", "scoped report", "nominal"),
    ("docs/design/MODAL_MODEL_AUDIT.md", "model audit", "source inspection + simulation"),
    ("evidence/week-2026-09-19/decision_screen/scenarios.json", "screen configs", "synthetic"),
    ("evidence/week-2026-09-19/decision_screen/results.json", "screen results", "synthetic"),
    ("evidence/week-2026-09-19/decision_screen/reproduction.txt", "screen method", "documentation"),
    ("evidence/week-2026-09-19/decision_screen/input_requests.md", "W3.2 requests", "documentation"),
    ("runs/nominal_package_inventory/inventory.json", "traceability inventory", "software check"),
    ("runs/mast_fixture_feasibility/nominal_screen.json", "authoritative UNKNOWN screen", "synthetic"),
    ("runs/mast_fea/fea_summary.txt", "historical FEA result", "simulation (historical provenance)"),
    ("runs/mast_hand_calc/design_sweep.txt", "hand calculation", "analytical"),
    ("runs/mast_tolerance_stack/summary.txt", "tolerance stack", "analytical"),
]

CHECKS = [
    ("python3 cad/ledger_validator.py live", "pass expected"),
    ("python3 cad/nominal_inventory.py --check", "pass expected"),
    ("python3 cad/tests/test_fixture_feasibility.py", "pass expected"),
    ("python3 experiments/test_load_cell_calibration.py", "pass expected"),
    ("python3 experiments/test_measurement_logger.py", "pass expected"),
    ("python3 cad/tests/test_unattended.py", "pass expected"),
    ("PYTHONPATH=gym python3 experiments/test_final_report.py", "pass expected"),
    ("PYTHONPATH=gym python3 experiments/test_mast_physical_validation.py", "pass expected"),
    ("python3 -m py_compile firmware/measurement_node/code.py", "pass expected (syntax only)"),
    ("python3 cad/fixture_feasibility.py", "EXPECTED REFUSAL, exit 2: terms are UNKNOWN"),
    ("python3 cad/fixture_contract.py --release", "EXPECTED REFUSAL, exit 2"),
    ("python3 cad/modal_freeze.py", "EXPECTED REFUSAL, exit 2"),
]

NOT_EXECUTED = [
    ("physical device operation", "no board was connected; firmware is syntax-checked only"),
    ("real load-cell calibration", "no cell mounted, no reference masses; all fixtures synthetic"),
    ("inspected CAD release", "no drawings, no inspection records, RR-CAD-02 blocked"),
    ("compliance campaign", "no fixture exists; the screen's authoritative verdict is UNKNOWN"),
    ("physical modal campaign", "tap test is a draft; RR-S12 blocked. The modal study is solver-only"),
    ("independent review", "no reviewer named; REVIEW_READY means ready for review, not reviewed"),
    ("unattended host toggle verification",
     "cad/solidworks/unattended.py reads the preference back, but no host run has returned "
     "applied=true. Its status is pending, separately from every item above"),
    ("legacy Gym simulation regeneration", "not rerun this week; controller sweep deliberately cut"),
]


def sha(rel: str):
    p = ROOT / rel
    if not p.is_file():
        return None
    return hashlib.sha256(p.read_bytes()).hexdigest()


def build():
    commit = subprocess.run(["git", "-C", str(ROOT), "rev-parse", "HEAD"],
                            capture_output=True, text=True).stdout.strip()
    files, missing = {}, []
    for rel, role, kind in ARTIFACTS:
        h = sha(rel)
        if h is None:
            missing.append(rel)
            continue
        files[rel] = dict(sha256=h, bytes=(ROOT / rel).stat().st_size, role=role, evidence_kind=kind)
    return dict(
        schema="week-manifest/1", week="2026-09-19..25", generated=time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        analysis_source_commit=commit,
        working_directory="repository root", environment="python3 (stdlib) unless a check states otherwise",
        self_exclusion="evidence/week-2026-09-19/manifest.json is excluded from its own hash set; a file "
                       "cannot contain the hash of a version of itself that includes that hash",
        files=files, missing_artifacts=missing,
        checks=[dict(command=c, expectation=e) for c, e in CHECKS],
        check_semantics="An EXPECTED REFUSAL exiting 2 is neither a crash nor a pass. It is the "
                        "fail-closed design working, and it is recorded as its own category.",
        not_executed=[dict(item=i, reason=r) for i, r in NOT_EXECUTED],
        provenance_note="runs/mast_fea/* carry their original historical provenance and were not "
                        "regenerated this week. Their source SHA is the commit that produced them, not "
                        "analysis_source_commit above.",
        review_status="REVIEW_READY means ready for review. Nothing here has been reviewed.")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--verify", action="store_true")
    a = ap.parse_args(argv)
    if not (a.write or a.verify):
        ap.error("give --write or --verify")
    if a.write:
        OUT.mkdir(parents=True, exist_ok=True)
        m = build()
        MANIFEST.write_text(json.dumps(m, indent=1) + "\n")
        print(f"wrote {MANIFEST.relative_to(ROOT)}: {len(m['files'])} artifacts, "
              f"{len(m['missing_artifacts'])} missing, {len(m['checks'])} checks, "
              f"{len(m['not_executed'])} not-executed items")
        return 1 if m["missing_artifacts"] else 0
    old = json.loads(MANIFEST.read_text())
    drift = [rel for rel, rec in old["files"].items() if sha(rel) != rec["sha256"]]
    gone = [rel for rel in old["files"] if not (ROOT / rel).is_file()]
    if drift or gone:
        print("MANIFEST VERIFICATION FAILED", file=sys.stderr)
        for rel in drift:
            print(f"  hash drift: {rel}", file=sys.stderr)
        for rel in gone:
            print(f"  missing:    {rel}", file=sys.stderr)
        return 1
    print(f"manifest verified: {len(old['files'])} artifacts match their recorded hashes")
    return 0


if __name__ == "__main__":
    sys.exit(main())
