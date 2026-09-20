"""Author the RoboRacer mast assembly parts in SOLIDWORKS. Runs on the host.

Builds mast_tube_stock and root_clamp from geometry.json, measures each against
oracle.json (built independently in CadQuery), and refuses to report success on a
part whose measured volume disagrees. A clean rebuild proves SOLIDWORKS raised no
error; it does not prove the requested geometry was produced.

API behaviour this file depends on is recorded in engineering-audit's
docs/solidworks_api_findings.md. In particular: Dispatch not EnsureDispatch,
GetEquationMgr/FirstFeature/GetTitle are properties, SelectByID2 needs a
VT_DISPATCH VARIANT for Callout, GetErrorCode2 needs a VT_BOOL|VT_BYREF VARIANT,
and SaveAs3 returns an inconsistent status so file existence is the check.

Invoked on the host as: python author_mast_assembly.py <work_dir>
"""
import json
import math
import os
import subprocess
import sys
import time
import traceback

SW_DOC_PART = 1
SW_SOLID_BODY = 0
SW_DEFAULT_PART_TEMPLATE = 69
SW_THROUGH_ALL = 1  # verified working on this host; ThroughAllBoth=9 was rejected
SW_START_SKETCH_PLANE = 0
FALLBACK_PART_TEMPLATE = r"C:\ProgramData\SolidWorks\SOLIDWORKS 2024\templates\Part.prtdot"
VOLUME_TOLERANCE_REL = 1e-6

MM = 0.001  # SOLIDWORKS API works in metres

RESULT = {"status": "error", "message": "", "parts": {}, "stages": []}


def stage(name, ok, detail=None):
    RESULT["stages"].append({"stage": name, "ok": bool(ok), "detail": detail})
    return bool(ok)


def set_property(com_object, name, value):
    """Assign a COM property that dynamic dispatch exposes as read-only."""
    import pythoncom
    dispatch_id = com_object._oleobj_.GetIDsOfNames(name)
    com_object._oleobj_.Invoke(dispatch_id, 0, pythoncom.DISPATCH_PROPERTYPUT, 0, value)


def solidworks_running():
    out = subprocess.run(["tasklist", "/FI", "IMAGENAME eq SLDWORKS.exe"],
                         capture_output=True, text=True).stdout
    return "SLDWORKS.EXE" in out.upper()


def failing_features(document, warning_flag):
    failures = []
    feature = document.FirstFeature
    while feature is not None:
        code = feature.GetErrorCode2(warning_flag)
        code = code[0] if isinstance(code, tuple) else code
        if code:
            failures.append({"feature": feature.Name, "error_code": code})
        feature = feature.GetNextFeature
    return failures


def measure(document, density):
    bodies = document.GetBodies2(SW_SOLID_BODY, True)
    count = len(bodies) if bodies else 0
    volume_mm3 = bodies[0].GetMassProperties(density)[3] * 1e9 if bodies else 0.0
    return count, volume_mm3


def volume_now(document):
    """Current solid volume in mm^3, for tracing what each feature actually removed."""
    try:
        bodies = document.GetBodies2(SW_SOLID_BODY, True)
        return bodies[0].GetMassProperties(1000.0)[3] * 1e9 if bodies else 0.0
    except Exception:
        return None


def cut_through_all(part, dir_opposite=False):
    """Cut the active sketch through all material.

    Argument 3 of FeatureCut4 reverses the cut direction. A sketch on a face cuts
    into the body by default, but a sketch on a datum plane does not reliably do
    so, so callers that sketch on a plane try both.
    """
    return part.FeatureManager.FeatureCut4(
        True, False, dir_opposite, SW_THROUGH_ALL, 0, 0.01, 0.01,
        False, False, False, False, 1, 1, False, False, False, False, False,
        True, True, True, True, False, SW_START_SKETCH_PLANE, 0, False, False)


def new_part(sw, template):
    return sw.NewDocument(template, 0, 0, 0)


def build_tube(sw, part, g, callout):
    """Two concentric circles on the Front Plane, extruded along Z."""
    t = g["mast_tube_stock"]
    od = t["outer_diameter"]["value"]
    wall = t["wall_thickness"]["value"]
    length = t["free_length"]["value"] + t["clamp_engagement"]["value"]

    # Solid cylinder first. A single sketch holding two concentric circles was
    # rejected by FeatureExtrusion3 on this host; one contour per feature works.
    stage("tube_select_plane",
          part.Extension.SelectByID2("Front Plane", "PLANE", 0.0, 0.0, 0.0, False, 0, callout, 0))
    sketch_mgr = part.SketchManager
    sketch_mgr.InsertSketch(True)
    outer = sketch_mgr.CreateCircleByRadius(0.0, 0.0, 0.0, od / 2 * MM)
    stage("tube_sketch_outer", outer is not None)
    sketch_mgr.InsertSketch(True)
    feature = part.FeatureManager.FeatureExtrusion3(
        True, False, False, 0, 0, length * MM, 0.0, False, False, False, False,
        0, 0, False, False, False, False, True, True, True, 0, 0, False)
    stage("tube_extrude", feature is not None, {"volume_mm3": volume_now(part)})

    # Bore, cut down from the top face so the cut direction is into material.
    part.ClearSelection2(True)
    stage("tube_select_top_face",
          part.Extension.SelectByID2("", "FACE", 0.0, 0.0, length * MM, False, 0, callout, 0))
    sketch_mgr.InsertSketch(True)
    inner = sketch_mgr.CreateCircleByRadius(0.0, 0.0, 0.0, (od / 2 - wall) * MM)
    stage("tube_sketch_bore", inner is not None)
    sketch_mgr.InsertSketch(True)
    stage("tube_cut_bore", cut_through_all(part) is not None, {"volume_mm3": volume_now(part)})
    return length


def build_clamp(sw, part, g, callout):
    """Block, bore along Z, split slot to the bore, and two cross bolt holes along X."""
    c = g["root_clamp"]
    W = c["block_width"]["value"]
    H = c["block_height"]["value"]
    D = c["block_depth"]["value"]
    bore_d = c["bore_diameter"]["value"]
    bx = c["bore_center_x"]["value"]
    by = c["bore_center_y"]["value"]
    slot_w = c["slot_width"]["value"]
    bolt_d = c["clamp_bolt_diameter"]["value"]
    bolt_y = c["clamp_bolt_y"]["value"]
    bolt_zs = c["clamp_bolt_z"]["value"]
    slot_bottom = c["slot_bottom_y"]["value"]

    sketch_mgr = part.SketchManager

    # 1. block
    stage("clamp_select_plane",
          part.Extension.SelectByID2("Front Plane", "PLANE", 0.0, 0.0, 0.0, False, 0, callout, 0))
    sketch_mgr.InsertSketch(True)
    rect = sketch_mgr.CreateCornerRectangle(0.0, 0.0, 0.0, W * MM, H * MM, 0.0)
    stage("clamp_sketch_block", rect is not None)
    sketch_mgr.InsertSketch(True)
    block = part.FeatureManager.FeatureExtrusion3(
        True, False, False, 0, 0, D * MM, 0.0, False, False, False, False,
        0, 0, False, False, False, False, True, True, True, 0, 0, False)
    stage("clamp_extrude_block", block is not None)

    # 2. bore along Z, sketched on the top face so the cut runs into material
    part.ClearSelection2(True)
    stage("clamp_select_top_face_bore",
          part.Extension.SelectByID2("", "FACE", bx * MM, by * MM, D * MM, False, 0, callout, 0))
    sketch_mgr.InsertSketch(True)
    bore_circle = sketch_mgr.CreateCircleByRadius(bx * MM, by * MM, 0.0, bore_d / 2 * MM)
    stage("clamp_sketch_bore", bore_circle is not None)
    sketch_mgr.InsertSketch(True)
    stage("clamp_cut_bore", cut_through_all(part) is not None, {"volume_mm3": volume_now(part)})

    # 3. split slot, from the top of the bore up through the top face. Selected at
    #    a corner of the top face because the bore has removed the face centre.
    part.ClearSelection2(True)
    stage("clamp_select_top_face_slot",
          part.Extension.SelectByID2("", "FACE", 5.0 * MM, 5.0 * MM, D * MM, False, 0, callout, 0))
    sketch_mgr.InsertSketch(True)
    slot_rect = sketch_mgr.CreateCornerRectangle(
        (bx - slot_w / 2) * MM, slot_bottom * MM, 0.0, (bx + slot_w / 2) * MM, H * MM, 0.0)
    stage("clamp_sketch_slot", slot_rect is not None)
    sketch_mgr.InsertSketch(True)
    stage("clamp_cut_slot", cut_through_all(part) is not None, {"volume_mm3": volume_now(part)})

    # 4. two clamp bolt holes crossing the slot, cut along +X from the Right Plane.
    #    probe_right_plane.py measured the mapping on this host: a Right Plane sketch
    #    at local (x, y) lands at global (Y=y, Z=-x), and the extrude runs +X. Hence
    #    the negated z below. Guessing this sign cost one build iteration.
    #    One contour per feature: a sketch holding both circles is rejected, the
    #    same multi-contour refusal that rejected the tube's concentric circles.
    for index, bz in enumerate(bolt_zs):
        before = volume_now(part)
        cut_made = False
        for dir_opposite in (False, True):
            part.ClearSelection2(True)
            part.Extension.SelectByID2("Right Plane", "PLANE", 0.0, 0.0, 0.0,
                                       False, 0, callout, 0)
            sketch_mgr.InsertSketch(True)
            sketch_mgr.CreateCircleByRadius(-bz * MM, bolt_y * MM, 0.0, bolt_d / 2 * MM)
            sketch_mgr.InsertSketch(True)
            feature = cut_through_all(part, dir_opposite)
            after = volume_now(part)
            if feature is not None and after is not None and before is not None and after < before:
                stage("clamp_cut_bolt_%d" % index, True,
                      {"dir_opposite": dir_opposite, "volume_mm3": after,
                       "removed_mm3": before - after})
                cut_made = True
                break
        if not cut_made:
            stage("clamp_cut_bolt_%d" % index, False, {"volume_mm3": volume_now(part)})


def finish_part(part, sw, name, work_dir, density, expected, warning_flag):
    """Rebuild, check features, measure against the oracle, export."""
    rebuilt = part.ForceRebuild3(False)
    failures = failing_features(part, warning_flag)
    stage("%s_rebuild" % name, rebuilt and not failures, failures)

    count, volume_mm3 = measure(part, density)
    expected_volume = expected["volume_mm3"]
    error_rel = abs(volume_mm3 - expected_volume) / expected_volume if expected_volume else None
    accepted = count == 1 and error_rel is not None and error_rel <= VOLUME_TOLERANCE_REL

    record = {
        "measured_volume_mm3": volume_mm3,
        "oracle_volume_mm3": expected_volume,
        "error_rel": error_rel,
        "tolerance_rel": VOLUME_TOLERANCE_REL,
        "n_solids": count,
        "accepted": accepted,
        "measured_mass_kg": volume_mm3 * 1e-9 * density,
    }

    sldprt = os.path.join(work_dir, "%s.sldprt" % name)
    step = os.path.join(work_dir, "%s.step" % name)
    part.SaveAs3(sldprt, 0, 0)
    part.ClearSelection2(True)
    part.SaveAs3(step, 0, 0)
    record["sldprt_written"] = os.path.exists(sldprt)
    record["step_written"] = os.path.exists(step) and os.path.getsize(step) > 0

    part.ShowNamedView2("*Isometric", 7)
    part.ViewZoomtofit2()
    part.GraphicsRedraw2()
    preview = os.path.join(work_dir, "%s.bmp" % name)
    part.SaveBMP(preview, 1000, 750)
    record["preview_written"] = os.path.exists(preview)

    RESULT["parts"][name] = record
    stage("%s_accepted" % name, accepted, record)
    return accepted


def main():
    work_dir = sys.argv[1] if len(sys.argv) > 1 else os.path.dirname(os.path.abspath(__file__))
    result_path = os.path.join(work_dir, "authoring_result.json")

    sw = None
    try:
        if solidworks_running():
            RESULT["message"] = "SLDWORKS.exe already running; refusing to attach to a session this script does not own"
            return

        import pythoncom
        import win32com.client

        callout = win32com.client.VARIANT(pythoncom.VT_DISPATCH, None)
        warning_flag = win32com.client.VARIANT(pythoncom.VT_BOOL | pythoncom.VT_BYREF, False)

        g = json.loads(open(os.path.join(work_dir, "geometry.json")).read())
        oracle = json.loads(open(os.path.join(work_dir, "oracle.json")).read())
        density = g["material"]["density"]["value"]

        sw = win32com.client.Dispatch("SldWorks.Application")
        sw.Visible = False
        time.sleep(8)

        template = sw.GetUserPreferenceStringValue(SW_DEFAULT_PART_TEMPLATE)
        if not template or not os.path.exists(template):
            template = FALLBACK_PART_TEMPLATE
        stage("resolve_template", os.path.exists(template), template)

        # --- mast tube ---
        part = new_part(sw, template)
        if not stage("tube_new_document", part is not None):
            RESULT["message"] = "NewDocument returned nothing"
            return
        build_tube(sw, part, g, callout)
        finish_part(part, sw, "mast_tube_stock", work_dir, density,
                    oracle["parts"]["mast_tube_stock"], warning_flag)
        sw.CloseDoc(part.GetTitle)

        # --- root clamp ---
        part = new_part(sw, template)
        if not stage("clamp_new_document", part is not None):
            RESULT["message"] = "NewDocument returned nothing for the clamp"
            return
        build_clamp(sw, part, g, callout)
        finish_part(part, sw, "root_clamp", work_dir, density,
                    oracle["parts"]["root_clamp"], warning_flag)
        sw.CloseDoc(part.GetTitle)

        all_ok = all(p["accepted"] for p in RESULT["parts"].values())
        RESULT["status"] = "ok" if all_ok else "error"
        RESULT["message"] = ("all parts matched the oracle" if all_ok
                             else "at least one part disagreed with the oracle")

    except Exception:
        RESULT["message"] = "unhandled exception:\n" + traceback.format_exc()
    finally:
        try:
            if sw is not None:
                sw.ExitApp()
        except Exception:
            pass
        with open(result_path, "w") as handle:
            json.dump(RESULT, handle, indent=2)


if __name__ == "__main__":
    main()
