#!/usr/bin/env python3
"""Nominal-package evidence inventory (Week plan W0.2). Stdlib only.

    python cad/nominal_inventory.py           # write runs/nominal_package_inventory/inventory.json
    python cad/nominal_inventory.py --check   # exit 1 if the committed inventory is stale or a headline
                                              # number no longer appears in its source

Every headline number the nominal mast package relies on, with the file it comes from, its SHA-256
at inventory time and its evidence label. Labels follow the week plan: NOMINAL DESIGN, MODEL
ASSUMPTION, SIMULATION OUTPUT, SOFTWARE CHECK, plus REJECTED BASELINE and OWNER PENDING. The
inventory is a SOFTWARE CHECK; it establishes traceability, not correctness of any value.
"""
import csv, hashlib, json, re, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "runs/nominal_package_inventory/inventory.json"

# (quantity, value as printed in the source, unit, source file, label). The value string must appear
# verbatim in the source file; that is the traceability check.
HEADLINES = [
    ("mast_length", "100", "mm", "cad/roboracer/parameters.csv", "NOMINAL DESIGN"),
    ("mast_outer_diameter", "20", "mm", "cad/roboracer/parameters.csv", "NOMINAL DESIGN"),
    ("mast_wall_thickness", "1.5", "mm", "cad/roboracer/parameters.csv", "NOMINAL DESIGN"),
    ("youngs_modulus", "68900", "N/mm^2", "cad/roboracer/parameters.csv", "MODEL ASSUMPTION"),
    ("density", "2700", "kg/m^3", "cad/roboracer/parameters.csv", "MODEL ASSUMPTION"),
    ("tip_total_mass", "0.175", "kg", "cad/roboracer/parameters.csv", "MODEL ASSUMPTION"),
    ("tube_volume_contract", "8717.919613711676", "mm^3", "cad/contract.json", "SOFTWARE CHECK"),
    ("tube_mass_contract", "0.023538382957021525", "kg", "cad/contract.json", "SOFTWARE CHECK"),
    ("crash_force", "128.76", "N", "runs/mast_hand_calc/summary.txt", "MODEL ASSUMPTION"),  # same F for both geometries
    ("selected_f1_hand", "330.1", "Hz", "runs/mast_hand_calc/design_sweep.txt", "NOMINAL DESIGN"),
    ("selected_crash_sf_hand", "8.05", "1", "runs/mast_hand_calc/design_sweep.txt", "NOMINAL DESIGN"),
    ("selected_root_stress_hand", "34.3", "MPa", "runs/mast_hand_calc/design_sweep.txt", "NOMINAL DESIGN"),
    ("selected_root_moment", "12.88", "N.m", "docs/design/16_mechanical_design_analysis.md", "NOMINAL DESIGN"),
    ("rejected_baseline_f1", "174.7", "Hz", "runs/mast_hand_calc/summary.txt", "REJECTED BASELINE"),
    ("rejected_baseline_moment", "15.451", "N.m", "runs/mast_hand_calc/summary.txt", "REJECTED BASELINE"),
    ("fea_f1", "285.5", "Hz", "runs/mast_fea/fea_summary.txt", "SIMULATION OUTPUT"),
    ("fea_tip_deflection", "0.176", "mm", "runs/mast_fea/fea_summary.txt", "SIMULATION OUTPUT"),
    ("fea_gauge_stress", "17.4", "MPa", "runs/mast_fea/fea_summary.txt", "SIMULATION OUTPUT"),
    ("fea_mesh_delta_f1", "-1.42", "%", "runs/mast_fea/mesh_convergence.txt", "SIMULATION OUTPUT"),
    ("tilt_blind_worst", "1.284", "deg", "runs/mast_tolerance_stack/summary.txt", "MODEL ASSUMPTION"),
    ("tilt_levelled", "0.354", "deg", "runs/mast_tolerance_stack/summary.txt", "MODEL ASSUMPTION"),
    ("deck_height_limit", "0.138", "m", "runs/mast_tolerance_stack/summary.txt", "NOMINAL DESIGN"),
    ("specimen_stiffness", "775.98", "N/mm", "docs/CAD_MEASUREMENT_CONTRACT.md", "NOMINAL DESIGN"),
    ("fixture_stiffness_min", "7,759.84", "N/mm", "docs/CAD_MEASUREMENT_CONTRACT.md", "NOMINAL DESIGN"),
]
ARTIFACTS = sorted({h[3] for h in HEADLINES} | {
    "evidence/task-2026-09-09/cad-out/mast_tube.step", "evidence/task-2026-09-09/cad-out/geometry.json",
    "docs/design/FEA_SETUP.md", "cad/roboracer/fixture-contract.json", "cad/roboracer/input-requests.csv",
})

# The two stale-record checks named in W0.2 / W1.1.
STALE_CHECKS = {
    "hand_calc_summary_labels_rejected_baseline": lambda: "REJECTED BASELINE" in _read("runs/mast_hand_calc/summary.txt"),
    "fea_setup_current_before_superseded": lambda: (t := _read("docs/design/FEA_SETUP.md")).index("Current result (0.175 kg") < t.index("SUPERSEDED"),
    "design_doc_selected_moment_is_F_times_h": lambda: "12.88 N·m" in _read("docs/design/16_mechanical_design_analysis.md"),
}


def _read(rel):
    return (ROOT / rel).read_text(encoding="utf-8", errors="ignore")


def _sha(rel):
    return hashlib.sha256((ROOT / rel).read_bytes()).hexdigest()


def pending_rows():
    with (ROOT / "cad/roboracer/parameters.csv").open(newline="") as f:
        return sorted(r["parameter"] for r in csv.DictReader(f) if r["evidence_state"] == "pending")


def build():
    missing = [(q, v, src) for q, v, _, src, _ in HEADLINES if v not in _read(src)]
    stale = [k for k, fn in STALE_CHECKS.items() if not fn()]
    commit = subprocess.run(["git", "-C", str(ROOT), "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
    return dict(
        source_commit=commit,
        label="SOFTWARE CHECK: traceability inventory, not validation",
        artifacts={a: _sha(a) for a in ARTIFACTS},
        headlines=[dict(quantity=q, value=v, unit=u, source=s, label=l) for q, v, u, s, l in HEADLINES],
        owner_pending=[dict(parameter=p, label="OWNER PENDING") for p in pending_rows()],
        stale_record_checks={k: (k not in stale) for k in STALE_CHECKS},
        blockers=[f"{q}={v} not found in {src}" for q, v, src in missing] + [f"stale record: {k}" for k in stale],
    )


def main(argv=None):
    check = "--check" in (argv or sys.argv[1:])
    inv = build()
    if inv["blockers"]:
        print("FAIL inventory:", *inv["blockers"], sep="\n  ", file=sys.stderr)
        return 1
    if check:
        old = json.loads(OUT.read_text()) if OUT.exists() else {}
        drift = [a for a, h in inv["artifacts"].items() if old.get("artifacts", {}).get(a) != h]
        if drift:
            print("STALE inventory; rerun without --check. Changed:", *drift, sep="\n  ", file=sys.stderr)
            return 1
        print(f"OK inventory: {len(inv['artifacts'])} artifacts, {len(inv['headlines'])} headlines traced, {len(inv['owner_pending'])} owner-pending rows")
        return 0
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(inv, indent=1) + "\n")
    print(f"wrote {OUT.relative_to(ROOT)}: {len(inv['artifacts'])} artifacts, {len(inv['headlines'])} headlines, {len(inv['owner_pending'])} owner-pending rows")
    return 0


if __name__ == "__main__":
    sys.exit(main())
