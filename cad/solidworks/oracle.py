#!/usr/bin/env python3
"""Closed-form-equivalent oracle for the SOLIDWORKS mast assembly.

Builds the same geometry in CadQuery that the SOLIDWORKS authoring scripts build,
and reports volume, bounding box and mass. SOLIDWORKS measured mass properties are
gated against these numbers: a clean rebuild proves SOLIDWORKS raised no error, it
does not prove the requested geometry was produced.

CadQuery is the reference here, not the deliverable. The deliverable is the
SOLIDWORKS model.

usage: python oracle.py [--geometry geometry.json] [--out oracle.json]
"""
from __future__ import annotations
import argparse, json, math
from pathlib import Path

import cadquery as cq

HERE = Path(__file__).resolve().parent


def v(node):
    """Unwrap a {"value": x, ...} entry from geometry.json."""
    return node["value"]


def build_tube(g):
    t = g["mast_tube_stock"]
    od, wall = v(t["outer_diameter"]), v(t["wall_thickness"])
    length = v(t["free_length"]) + v(t["clamp_engagement"])
    solid = cq.Workplane("XY").circle(od / 2).circle(od / 2 - wall).extrude(length)
    return solid, {"stock_length_mm": length}


def build_clamp(g):
    c = g["root_clamp"]
    W, H, D = v(c["block_width"]), v(c["block_height"]), v(c["block_depth"])
    bore_d = v(c["bore_diameter"])
    bx, by = v(c["bore_center_x"]), v(c["bore_center_y"])
    slot_w = v(c["slot_width"])
    bolt_d = v(c["clamp_bolt_diameter"])
    bolt_y = v(c["clamp_bolt_y"])
    bolt_zs = v(c["clamp_bolt_z"])

    block = cq.Workplane("XY").box(W, H, D, centered=False)

    bore = cq.Workplane("XY").center(bx, by).circle(bore_d / 2).extrude(D)

    slot_bottom = v(c["slot_bottom_y"])
    slot = (cq.Workplane("XY")
            .box(slot_w, H - slot_bottom, D, centered=False)
            .translate((bx - slot_w / 2, slot_bottom, 0)))

    solid = block.cut(bore).cut(slot)
    for bz in bolt_zs:
        bolt = cq.Workplane("YZ").center(bolt_y, bz).circle(bolt_d / 2).extrude(W)
        solid = solid.cut(bolt)

    return solid, {"slot_bottom_mm": slot_bottom}


def metrics(solid, density_kg_m3):
    val = solid.val()
    bb = val.BoundingBox()
    vol = float(val.Volume())
    return {
        "volume_mm3": vol,
        "mass_kg": vol * 1e-9 * density_kg_m3,
        "bbox_mm": [float(bb.xlen), float(bb.ylen), float(bb.zlen)],
        "n_solids": len(solid.solids().vals()),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--geometry", type=Path, default=HERE / "geometry.json")
    ap.add_argument("--out", type=Path, default=HERE / "oracle.json")
    a = ap.parse_args()

    g = json.loads(a.geometry.read_text())
    density = v(g["material"]["density"])

    out = {"geometry_source": a.geometry.name, "density_kg_m3": density, "parts": {}}
    for name, builder in (("mast_tube_stock", build_tube), ("root_clamp", build_clamp)):
        solid, extra = builder(g)
        m = metrics(solid, density)
        m.update(extra)
        out["parts"][name] = m

    a.out.write_text(json.dumps(out, indent=2) + "\n")
    print(json.dumps(out, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
