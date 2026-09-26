#!/usr/bin/env python3
"""Three-case modal tip-mass attachment comparison (closeout T3).

    python experiments/modal_attachment_study.py [--mesh-size 1.2e-3] [--modes 6]

Answers one bounded question: how much of the hand-vs-FE frequency difference is attributable to HOW
the tip mass is attached, and how much to WHERE it sits? Those are separate changes and the historical
model conflated them.

  A legacy            single-node mass on the off-axis wall node (the historical deck)
  B coupled_eccentric same position, but rigidly coupled to the whole tip plane
  C coupled_centred   on the axis, with the identical coupling definition

B - A isolates the attachment model. C - B isolates position within that model. A - C alone changes two
things and is NOT the eccentricity effect.

Writes to runs/mast_modal_attachment_20260925/. It does NOT touch runs/mast_fea/, and it does not adopt
a new headline frequency: a new coupling invalidates automatic reuse of the old convergence evidence, so
adopting any number from here would need its own refinement study first.
"""
from __future__ import annotations

import argparse, json, math, platform, re, subprocess, sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "experiments"))
import mast_fea as mf  # noqa: E402

OUT = ROOT / "runs" / "mast_modal_attachment_20260925"
NEAR_ZERO_HZ = 1.0          # below this a mode is treated as a spurious mechanism, not a structural mode


def parse_tables(dat: Path) -> dict:
    """Eigenfrequencies plus the participation-factor and effective-modal-mass tables.

    Effective modal mass per direction is what identifies a mode: it is quantitative and does not
    depend on the solver's ordering, which can swap a near-degenerate orthogonal pair."""
    txt = dat.read_text()
    freqs = mf.parse_dat_eigenfreqs(dat)

    def block(title):
        rows = {}
        m = re.search(re.escape(title) + r"(.*?)(?:\n\s*\n\s*[A-Z] [A-Z]|\Z)", txt, re.S)
        if not m:
            return rows
        for line in m.group(1).splitlines():
            parts = line.split()
            if len(parts) == 7 and parts[0].isdigit():
                rows[int(parts[0])] = [float(v) for v in parts[1:]]
            elif len(parts) == 7 and parts[0] == "TOTAL":
                rows["TOTAL"] = [float(v) for v in parts[1:]]
        return rows

    return dict(frequencies_hz=freqs,
                participation=block("P A R T I C I P A T I O N   F A C T O R S"),
                effective_modal_mass=block("E F F E C T I V E   M O D A L   M A S S"))


def identify(tables: dict) -> dict:
    """Label each mode from its effective modal mass, and pick the transverse bending pair."""
    emm = tables["effective_modal_mass"]
    freqs = tables["frequencies_hz"]
    modes = []
    for i, f in enumerate(freqs, start=1):
        row = emm.get(i)
        if not row:
            modes.append(dict(mode=i, hz=f, label="unknown", reason="no effective-mass row"))
            continue
        mx, my, mz = row[0], row[1], row[2]
        transverse, axial = mx + my, mz
        label = ("transverse_bending" if transverse > 5.0 * axial else
                 "axial" if axial > 5.0 * transverse else "mixed")
        modes.append(dict(mode=i, hz=f, label=label, eff_mass_x_kg=mx, eff_mass_y_kg=my,
                          eff_mass_z_kg=mz, transverse_over_axial=(transverse / axial if axial else None)))
    bending = [m for m in modes if m["label"] == "transverse_bending"]
    return dict(modes=modes,
                bending_pair_hz=[m["hz"] for m in bending[:2]],
                first_bending_hz=(bending[0]["hz"] if bending else None),
                first_bending_mode_index=(bending[0]["mode"] if bending else None),
                near_zero_modes=[m["mode"] for m in modes if m["hz"] < NEAR_ZERO_HZ],
                note="the first bending mode is chosen by effective modal mass, not by index; a "
                     "near-degenerate orthogonal pair can swap order between cases")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--mesh-size", type=float, default=mf.MESH_SIZE)
    ap.add_argument("--modes", type=int, default=6)
    a = ap.parse_args(argv)

    ccx = mf.find_ccx()
    if not ccx:
        print("REFUSED: no ccx binary found; set CCX", file=sys.stderr)
        return 2
    OUT.mkdir(parents=True, exist_ok=True)
    rev = subprocess.run(["git", "-C", str(ROOT), "rev-parse", "HEAD"],
                         capture_output=True, text=True).stdout.strip()
    env = dict(python=platform.python_version(), platform=platform.platform(), ccx_path=ccx,
               ccx_version=subprocess.run([ccx, "-v"], capture_output=True, text=True).stdout.strip(),
               gmsh=getattr(__import__("gmsh"), "__version__", "unknown"),
               source_commit=rev, generated=time.strftime("%Y-%m-%dT%H:%M:%S%z"))

    # ONE mesh for all three cases. Mesh, material, root constraint, tube dimensions and tip mass are
    # held fixed inside the comparison; only the attachment definition changes.
    mesh = mf.build_mesh(mesh_size=a.mesh_size)
    mesh_id = dict(mesh_size_m=a.mesh_size, nodes=len(mesh.nodes), c3d10=len(mesh.c3d10),
                   root_nodes=len(mesh.root_nodes), tip_plane_nodes=len(mesh.tip_nodes),
                   legacy_mass_node=mesh.tip_center_node,
                   legacy_mass_node_coords_m=list(mesh.nodes[mesh.tip_center_node]))

    cases = {}
    for att in mf.ATTACHMENTS:
        job = OUT / att
        rec = mf.write_modal_inp(mesh, job.with_suffix(".inp"), attachment=att)
        t0 = time.time()
        mf.run_ccx(ccx, job)
        dat = job.with_suffix(".dat")
        if not dat.exists():
            cases[att] = dict(attachment=rec, status="SOLVER_FAILED",
                              log=str((OUT / (att + ".ccx.log")).relative_to(ROOT)))
            continue
        tables = parse_tables(dat)
        ident = identify(tables)
        emm_total = tables["effective_modal_mass"].get("TOTAL")
        cases[att] = dict(attachment=rec, status="ok", solve_seconds=round(time.time() - t0, 1),
                          tables=tables, identification=ident,
                          checks=dict(
                              added_mass_kg=rec["added_mass_kg"],
                              total_effective_mass_x_kg=(emm_total[0] if emm_total else None),
                              root_nodes_constrained=len(mesh.root_nodes),
                              near_zero_modes=ident["near_zero_modes"],
                              no_spurious_mechanism=not ident["near_zero_modes"]),
                          files={k: str((OUT / (att + k)).relative_to(ROOT))
                                 for k in (".inp", ".dat", ".ccx.log")})

    # Deltas with explicit denominators. Only the two single-change comparisons are named as effects.
    def f(att):
        return cases.get(att, {}).get("identification", {}).get("first_bending_hz")
    a_hz, b_hz, c_hz = f("legacy"), f("coupled_eccentric"), f("coupled_centred")
    def delta(lo, hi, name, what):
        if lo is None or hi is None:
            return dict(comparison=name, status="unavailable")
        return dict(comparison=name, isolates=what, from_hz=lo, to_hz=hi,
                    delta_hz=hi - lo, percent=100.0 * (hi - lo) / lo,
                    denominator=f"percent is relative to {name.split(' -> ')[0]} = {lo:.4f} Hz")
    comparisons = [
        delta(a_hz, b_hz, "legacy -> coupled_eccentric", "the attachment model, position held fixed"),
        delta(b_hz, c_hz, "coupled_eccentric -> coupled_centred", "position, attachment model held fixed"),
    ]
    confounded = delta(a_hz, c_hz, "legacy -> coupled_centred", "TWO changes at once")
    confounded["warning"] = ("This is NOT the eccentricity effect: it changes both the attachment model "
                             "and the position. Reported only so it cannot be mistaken for one of them.")

    result = dict(
        label="MODAL ATTACHMENT COMPARISON: solver output of three declared model definitions. "
              "No physical measurement, no adopted headline frequency, no RR-S12 progress.",
        schema="modal-attachment-study/1", environment=env, mesh=mesh_id, cases=cases,
        comparisons=comparisons, confounded_comparison=confounded,
        historical_reference=dict(
            committed_fea_hz=285.5, hand_calc_hz=330.1, run_dir="runs/mast_fea",
            note="retained with its original provenance; this study neither regenerates nor replaces it"),
        adoption=dict(
            adopted=False,
            reason="a new coupling invalidates automatic reuse of the existing mesh-convergence "
                   "evidence, so no number here may become a headline without its own refinement study"))
    (OUT / "study.json").write_text(json.dumps(result, indent=1) + "\n")

    print(f"mesh {mesh_id['nodes']} nodes, legacy offset "
          f"{math.hypot(*mesh_id['legacy_mass_node_coords_m'][:2])*1e3:.4f} mm")
    for att in mf.ATTACHMENTS:
        c = cases[att]
        if c["status"] != "ok":
            print(f"  {att:18} {c['status']}")
            continue
        i = c["identification"]
        print(f"  {att:18} f1_bending={i['first_bending_hz']:.4f} Hz (mode {i['first_bending_mode_index']}) "
              f"pair={[round(v,2) for v in i['bending_pair_hz']]} spurious={i['near_zero_modes']}")
    for d in comparisons:
        if d.get("status") != "unavailable":
            print(f"  {d['comparison']}: {d['delta_hz']:+.4f} Hz ({d['percent']:+.3f} %) -- {d['isolates']}")
    print(f"-> {OUT.relative_to(ROOT)}/study.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
