#!/usr/bin/env python3
"""Independent expectation for the positioned mast ASSEMBLY, and the STEP round-trip check.

Workstation side (needs cadquery). Builds the three parts with oracle.py's builders, translates
each by its intended placement, and records per-component volume and box, the assembly box, the total
volume and the free length, all read off the positioned CadQuery solids. The host script compares
SOLIDWORKS read-backs against this file; nothing here is copied from the host.

usage:
  python oracle_assembly.py                      # write oracle_assembly.json
  python oracle_assembly.py --check-step X.step --result assembly_result.json
      import the assembly STEP, compare box and volumes to the oracle, write the verdict into the result
"""
from __future__ import annotations
import argparse, json
from pathlib import Path

import cadquery as cq
import oracle

HERE = Path(__file__).resolve().parent
# Intended placement of each part's local origin in the assembly, mm. Parts are sketched on the Front
# Plane and extruded +Z; the clamp bore is authored at local (22, 22) so -22,-22 puts it on the tube axis.
PLACEMENT = {"mast_tube_stock": (0.0, 0.0, 0.0), "support_sleeve": (0.0, 0.0, 0.0),
             "root_clamp": (-22.0, -22.0, 0.0)}
BUILDERS = {"mast_tube_stock": oracle.build_tube, "support_sleeve": oracle.build_sleeve,
            "root_clamp": oracle.build_clamp}
REL_VOL = 1e-6
ABS_BOX_MM = 1e-3


def expected(g):
    comps, boxes = {}, []
    for name, build in BUILDERS.items():
        val = build(g)[0].translate(PLACEMENT[name]).val()
        bb = val.BoundingBox()
        lo, hi = [bb.xmin, bb.ymin, bb.zmin], [bb.xmax, bb.ymax, bb.zmax]
        boxes.append((lo, hi))
        comps[name] = {"translation_mm": list(PLACEMENT[name]), "volume_mm3": float(val.Volume()),
                       "box_min_mm": lo, "box_max_mm": hi}
    lo = [min(b[0][i] for b in boxes) for i in range(3)]
    hi = [max(b[1][i] for b in boxes) for i in range(3)]
    tube, clamp = comps["mast_tube_stock"], comps["root_clamp"]
    return {"components": comps,
            "assembly": {"box_min_mm": lo, "box_max_mm": hi, "bbox_mm": [h - l for l, h in zip(lo, hi)],
                         "total_volume_mm3": sum(c["volume_mm3"] for c in comps.values())},
            "free_length_mm": tube["box_max_mm"][2] - clamp["box_max_mm"][2]}


def check_step(step, exp):
    shape = cq.importers.importStep(str(step)).val()
    bb = shape.BoundingBox()
    got_box = [bb.xlen, bb.ylen, bb.zlen]
    want_box = exp["assembly"]["bbox_mm"]
    vols = sorted(float(s.Volume()) for s in shape.Solids())
    want_vols = sorted(c["volume_mm3"] for c in exp["components"].values())
    total = sum(vols)
    want_total = exp["assembly"]["total_volume_mm3"]
    box_ok = all(abs(a - b) <= ABS_BOX_MM for a, b in zip(got_box, want_box))
    lo_ok = all(abs(a - b) <= ABS_BOX_MM for a, b in zip(
        [bb.xmin, bb.ymin, bb.zmin], exp["assembly"]["box_min_mm"]))
    vols_ok = len(vols) == len(want_vols) and all(abs(a - b) / b <= REL_VOL for a, b in zip(vols, want_vols))
    total_ok = abs(total - want_total) / want_total <= REL_VOL
    return {"bbox_mm": got_box, "bbox_expected_mm": want_box, "bbox_ok": box_ok,
            "box_min_mm": [bb.xmin, bb.ymin, bb.zmin], "box_min_ok": lo_ok,
            "solid_volumes_mm3": vols, "solid_volumes_expected_mm3": want_vols, "n_solids": len(vols),
            "volumes_ok": vols_ok, "total_volume_mm3": total, "total_volume_expected_mm3": want_total,
            "total_ok": total_ok, "ok": box_ok and lo_ok and vols_ok and total_ok}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--geometry", type=Path, default=HERE / "geometry.json")
    ap.add_argument("--out", type=Path, default=HERE / "oracle_assembly.json")
    ap.add_argument("--check-step", type=Path)
    ap.add_argument("--result", type=Path)
    a = ap.parse_args()
    g = json.loads(a.geometry.read_text())
    exp = expected(g)
    if not a.check_step:
        a.out.write_text(json.dumps(exp, indent=2) + "\n")
        print(json.dumps(exp, indent=2))
        return 0
    rt = check_step(a.check_step, exp)
    print(json.dumps(rt, indent=2))
    if a.result:
        res = json.loads(a.result.read_text())
        res["step_roundtrip"] = rt
        host_ok = res.get("host_checks_ok") is True
        res["accepted"] = bool(host_ok and rt["ok"])
        res["status"] = "ok" if res["accepted"] else "partial"
        a.result.write_text(json.dumps(res, indent=2) + "\n")
    return 0 if rt["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
