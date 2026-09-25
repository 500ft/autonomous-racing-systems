"""Author the RoboRacer mast assembly parts in SOLIDWORKS. Runs on the host.

Builds mast_tube_stock, support_sleeve and root_clamp from geometry.json, drives
each part's governing dimensions from named global variables so the register can
own them, and measures every part against oracle.json (built independently in
CadQuery). A part whose measured volume disagrees is not reported as built: a
clean rebuild proves SOLIDWORKS raised no error, not that the requested geometry
was produced.

API behaviour this file depends on is recorded in cad/solidworks/README.md and
engineering-audit's docs/solidworks_api_findings.md.

Invoked on the host as: python author_mast_assembly.py <work_dir>
"""
import json
import os
import subprocess
import sys
import time
import traceback

SW_DOC_PART = 1
SW_SOLID_BODY = 0
SW_DEFAULT_PART_TEMPLATE = 69
SW_THROUGH_ALL = 1
SW_START_SKETCH_PLANE = 0
FALLBACK_PART_TEMPLATE = r"C:\ProgramData\SolidWorks\SOLIDWORKS 2024\templates\Part.prtdot"
# Deliverables land in the owner's per-repo project folder; the work_dir stays
# the pipeline's scratch area so scripts and JSON do not clutter it.
PARTS_DIR = r"C:\Users\admin\Desktop\Projects\autonomous-racing-systems"
VOLUME_TOLERANCE_REL = 1e-6
MM = 0.001  # the SOLIDWORKS API works in metres

RESULT = {"status": "error", "message": "", "parts": {}, "stages": []}


def stage(name, ok, detail=None):
    RESULT["stages"].append({"stage": name, "ok": bool(ok), "detail": detail})
    return bool(ok)


def set_property(com_object, name, value):
    """Assign a COM property that dynamic dispatch exposes as read-only."""
    import pythoncom
    dispatch_id = com_object._oleobj_.GetIDsOfNames(name)
    com_object._oleobj_.Invoke(dispatch_id, 0, pythoncom.DISPATCH_PROPERTYPUT, 0, value)


def short_name(dimension):
    """`D1@Sketch1` from `D1@Sketch1@Part1.Part`; equations inside a part need the
    two-part form and silently discard the document-qualified one."""
    return "@".join(dimension.FullName.split("@")[:2])


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


def volume_now(document):
    try:
        bodies = document.GetBodies2(SW_SOLID_BODY, True)
        return bodies[0].GetMassProperties(1000.0)[3] * 1e9 if bodies else 0.0
    except Exception:
        return None


def cut_through_all(part, dir_opposite=False):
    """Argument 3 reverses the cut direction. A cut sketched on a face runs into
    the body; a cut sketched on a datum plane does not reliably do so."""
    return part.FeatureManager.FeatureCut4(
        True, False, dir_opposite, SW_THROUGH_ALL, 0, 0.01, 0.01,
        False, False, False, False, 1, 1, False, False, False, False, False,
        True, True, True, True, False, SW_START_SKETCH_PLANE, 0, False, False)


def extrude(part, depth_m):
    return part.FeatureManager.FeatureExtrusion3(
        True, False, False, 0, 0, depth_m, 0.0, False, False, False, False,
        0, 0, False, False, False, False, True, True, True, 0, 0, False)


def dimension_segment(part, callout, pick, place, value_m, label):
    """Dimension the sketch segment under `pick` and return its two-part name.

    Must run while the sketch is still open. The segment is drawn at its final
    size first and then dimensioned to that same value, so applying the dimension
    does not move under-defined geometry.
    """
    part.ClearSelection2(True)
    if not part.Extension.SelectByID2("", "SKETCHSEGMENT", pick[0], pick[1], pick[2],
                                      False, 0, callout, 0):
        stage(label, False, "segment not selected")
        return None
    display = part.AddDimension2(place[0], place[1], place[2])
    if display is None:
        stage(label, False, "AddDimension2 returned nothing")
        return None
    dim = display.GetDimension2(0)
    set_property(dim, "SystemValue", value_m)
    name = short_name(dim)
    stage(label, True, name)
    return name


def feature_depth_name(feature, label):
    """The depth dimension of an extrude, reached through IFeature::Parameter."""
    if feature is None:
        stage(label, False, "no feature")
        return None
    dim = feature.Parameter("D1")
    if dim is None:
        stage(label, False, "Parameter('D1') returned nothing")
        return None
    name = short_name(dim)
    stage(label, True, name)
    return name


def write_equations(part, declarations, links, label):
    """Declare global variables, then drive dimensions from them.

    Both sides of a link are quoted: an unquoted dimension name is accepted by
    Add2 and then discarded, leaving a variable that drives nothing. One rejected
    equation invalidates the rest of the batch, so every index is checked.
    """
    eq_mgr = part.GetEquationMgr
    written = []
    for text in declarations:
        written.append({"equation": text, "index": eq_mgr.Add2(-1, text, False)})
    for dim_name, expression in links:
        if not dim_name:
            written.append({"equation": None, "index": -1, "note": "missing dimension name"})
            continue
        text = '"%s"= %s' % (dim_name, expression)
        written.append({"equation": text, "index": eq_mgr.Add2(-1, text, False)})
    eq_mgr.EvaluateAll
    ok = all(w["index"] is not None and w["index"] >= 0 for w in written)
    stage(label, ok, written)
    return ok


def build_tube(part, g, callout):
    """Solid cylinder plus a bore. A single sketch holding two concentric circles
    is rejected by FeatureExtrusion3 on this host: one closed contour per feature."""
    t = g["mast_tube_stock"]
    od = t["outer_diameter"]["value"]
    wall = t["wall_thickness"]["value"]
    free = t["free_length"]["value"]
    engagement = t["clamp_engagement"]["value"]
    length = free + engagement
    bore = od - 2 * wall

    sketch_mgr = part.SketchManager
    stage("tube_select_plane",
          part.Extension.SelectByID2("Front Plane", "PLANE", 0.0, 0.0, 0.0, False, 0, callout, 0))
    sketch_mgr.InsertSketch(True)
    sketch_mgr.CreateCircleByRadius(0.0, 0.0, 0.0, od / 2 * MM)
    od_dim = dimension_segment(part, callout, (od / 2 * MM, 0.0, 0.0),
                               (od * MM, od * MM, 0.0), od * MM, "tube_dim_od")
    sketch_mgr.InsertSketch(True)
    boss = extrude(part, length * MM)
    stage("tube_extrude", boss is not None, {"volume_mm3": volume_now(part)})
    length_dim = feature_depth_name(boss, "tube_dim_length")

    part.ClearSelection2(True)
    stage("tube_select_top_face",
          part.Extension.SelectByID2("", "FACE", 0.0, 0.0, length * MM, False, 0, callout, 0))
    sketch_mgr.InsertSketch(True)
    sketch_mgr.CreateCircleByRadius(0.0, 0.0, 0.0, bore / 2 * MM)
    bore_dim = dimension_segment(part, callout, (bore / 2 * MM, 0.0, length * MM),
                                 (bore * MM, bore * MM, length * MM), bore * MM, "tube_dim_bore")
    sketch_mgr.InsertSketch(True)
    stage("tube_cut_bore", cut_through_all(part) is not None, {"volume_mm3": volume_now(part)})

    write_equations(
        part,
        ['"TubeOD"= %gmm' % od,
         '"TubeWall"= %gmm' % wall,
         '"MastFreeLength"= %gmm' % free,
         '"ClampEngagement"= %gmm' % engagement],
        [(od_dim, '"TubeOD"'),
         (bore_dim, '"TubeOD" - 2 * "TubeWall"'),
         (length_dim, '"MastFreeLength" + "ClampEngagement"')],
        "tube_equations")


def build_sleeve(part, g, callout):
    """Internal support over the clamped length, required by spec 6.1."""
    s = g["support_sleeve"]
    od = s["outer_diameter"]["value"]
    idia = s["inner_diameter"]["value"]
    length = s["length"]["value"]

    sketch_mgr = part.SketchManager
    stage("sleeve_select_plane",
          part.Extension.SelectByID2("Front Plane", "PLANE", 0.0, 0.0, 0.0, False, 0, callout, 0))
    sketch_mgr.InsertSketch(True)
    sketch_mgr.CreateCircleByRadius(0.0, 0.0, 0.0, od / 2 * MM)
    od_dim = dimension_segment(part, callout, (od / 2 * MM, 0.0, 0.0),
                               (od * MM, od * MM, 0.0), od * MM, "sleeve_dim_od")
    sketch_mgr.InsertSketch(True)
    boss = extrude(part, length * MM)
    stage("sleeve_extrude", boss is not None, {"volume_mm3": volume_now(part)})
    length_dim = feature_depth_name(boss, "sleeve_dim_length")

    part.ClearSelection2(True)
    stage("sleeve_select_top_face",
          part.Extension.SelectByID2("", "FACE", 0.0, 0.0, length * MM, False, 0, callout, 0))
    sketch_mgr.InsertSketch(True)
    sketch_mgr.CreateCircleByRadius(0.0, 0.0, 0.0, idia / 2 * MM)
    bore_dim = dimension_segment(part, callout, (idia / 2 * MM, 0.0, length * MM),
                                 (idia * MM, idia * MM, length * MM), idia * MM, "sleeve_dim_bore")
    sketch_mgr.InsertSketch(True)
    stage("sleeve_cut_bore", cut_through_all(part) is not None, {"volume_mm3": volume_now(part)})

    write_equations(
        part,
        ['"SleeveOD"= %gmm' % od,
         '"SleeveID"= %gmm' % idia,
         '"ClampEngagement"= %gmm' % length],
        [(od_dim, '"SleeveOD"'),
         (bore_dim, '"SleeveID"'),
         (length_dim, '"ClampEngagement"')],
        "sleeve_equations")


def build_clamp(part, g, callout):
    """Block, bore, split slot running to the bore centreline, and two cross bolts."""
    c = g["root_clamp"]
    W = c["block_width"]["value"]
    H = c["block_height"]["value"]
    D = c["block_depth"]["value"]
    bore_d = c["bore_diameter"]["value"]
    bx, by = c["bore_center_x"]["value"], c["bore_center_y"]["value"]
    slot_w = c["slot_width"]["value"]
    slot_bottom = c["slot_bottom_y"]["value"]
    bolt_d = c["clamp_bolt_diameter"]["value"]
    bolt_y = c["clamp_bolt_y"]["value"]
    bolt_zs = c["clamp_bolt_z"]["value"]

    sketch_mgr = part.SketchManager

    # 1. block
    stage("clamp_select_plane",
          part.Extension.SelectByID2("Front Plane", "PLANE", 0.0, 0.0, 0.0, False, 0, callout, 0))
    sketch_mgr.InsertSketch(True)
    sketch_mgr.CreateCornerRectangle(0.0, 0.0, 0.0, W * MM, H * MM, 0.0)
    width_dim = dimension_segment(part, callout, (W / 2 * MM, 0.0, 0.0),
                                  (W / 2 * MM, -0.010, 0.0), W * MM, "clamp_dim_width")
    height_dim = dimension_segment(part, callout, (0.0, H / 2 * MM, 0.0),
                                   (-0.010, H / 2 * MM, 0.0), H * MM, "clamp_dim_height")
    sketch_mgr.InsertSketch(True)
    boss = extrude(part, D * MM)
    stage("clamp_extrude_block", boss is not None, {"volume_mm3": volume_now(part)})
    depth_dim = feature_depth_name(boss, "clamp_dim_depth")

    # 2. bore, sketched on the top face so the cut runs into the body
    part.ClearSelection2(True)
    stage("clamp_select_top_face_bore",
          part.Extension.SelectByID2("", "FACE", bx * MM, by * MM, D * MM, False, 0, callout, 0))
    sketch_mgr.InsertSketch(True)
    sketch_mgr.CreateCircleByRadius(bx * MM, by * MM, 0.0, bore_d / 2 * MM)
    bore_dim = dimension_segment(part, callout,
                                 ((bx + bore_d / 2) * MM, by * MM, D * MM),
                                 ((bx + bore_d) * MM, (by + bore_d) * MM, D * MM),
                                 bore_d * MM, "clamp_dim_bore")
    sketch_mgr.InsertSketch(True)
    stage("clamp_cut_bore", cut_through_all(part) is not None, {"volume_mm3": volume_now(part)})

    # 3. split slot. Runs to the bore centreline: a slot merely tangent to the bore
    #    leaves a knife edge and cannot close on the tube, and SOLIDWORKS perturbs
    #    a sketch edge placed exactly tangent to an existing edge.
    part.ClearSelection2(True)
    stage("clamp_select_top_face_slot",
          part.Extension.SelectByID2("", "FACE", 5.0 * MM, 5.0 * MM, D * MM, False, 0, callout, 0))
    sketch_mgr.InsertSketch(True)
    sketch_mgr.CreateCornerRectangle((bx - slot_w / 2) * MM, slot_bottom * MM, 0.0,
                                     (bx + slot_w / 2) * MM, H * MM, 0.0)
    sketch_mgr.InsertSketch(True)
    stage("clamp_cut_slot", cut_through_all(part) is not None, {"volume_mm3": volume_now(part)})

    # 4. clamp bolts, cut along X off the Right Plane. probe_right_plane.py measured
    #    the mapping: local (x, y) lands at global (Y=y, Z=-x). A cut off a datum
    #    plane runs opposite to a boss off the same plane, so both are tried.
    for index, bz in enumerate(bolt_zs):
        before = volume_now(part)
        made = False
        for dir_opposite in (True, False):
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
                      {"dir_opposite": dir_opposite, "removed_mm3": before - after})
                made = True
                break
        if not made:
            stage("clamp_cut_bolt_%d" % index, False, {"volume_mm3": volume_now(part)})

    write_equations(
        part,
        ['"ClampWidth"= %gmm' % W,
         '"ClampHeight"= %gmm' % H,
         '"ClampEngagement"= %gmm' % D,
         '"ClampBoreDia"= %gmm' % bore_d],
        [(width_dim, '"ClampWidth"'),
         (height_dim, '"ClampHeight"'),
         (depth_dim, '"ClampEngagement"'),
         (bore_dim, '"ClampBoreDia"')],
        "clamp_equations")


def finish_part(part, name, work_dir, density, expected, warning_flag):
    rebuilt = part.ForceRebuild3(False)
    failures = failing_features(part, warning_flag)
    stage("%s_rebuild" % name, rebuilt and not failures, failures)

    bodies = part.GetBodies2(SW_SOLID_BODY, True)
    count = len(bodies) if bodies else 0
    volume_mm3 = bodies[0].GetMassProperties(density)[3] * 1e9 if bodies else 0.0
    expected_volume = expected["volume_mm3"]
    error_rel = abs(volume_mm3 - expected_volume) / expected_volume if expected_volume else None
    accepted = count == 1 and error_rel is not None and error_rel <= VOLUME_TOLERANCE_REL

    record = {
        "measured_volume_mm3": volume_mm3,
        "oracle_volume_mm3": expected_volume,
        "error_rel": error_rel,
        "tolerance_rel": VOLUME_TOLERANCE_REL,
        "n_solids": count,
        "measured_mass_kg": volume_mm3 * 1e-9 * density,
        "accepted": accepted,
    }

    parts_dir = PARTS_DIR if os.path.isdir(PARTS_DIR) else work_dir
    sldprt = os.path.join(parts_dir, "%s.sldprt" % name)
    step = os.path.join(parts_dir, "%s.step" % name)
    part.SaveAs3(sldprt, 0, 0)
    part.ClearSelection2(True)
    part.SaveAs3(step, 0, 0)
    record["sldprt_written"] = os.path.exists(sldprt)
    record["step_written"] = os.path.exists(step) and os.path.getsize(step) > 0

    part.ShowNamedView2("*Isometric", 7)
    part.ViewZoomtofit2()
    part.GraphicsRedraw2()
    preview = os.path.join(parts_dir, "%s.bmp" % name)
    part.SaveBMP(preview, 1000, 750)
    record["preview_written"] = os.path.exists(preview)

    RESULT["parts"][name] = record
    stage("%s_accepted" % name, accepted, record)
    return accepted


def main():
    work_dir = sys.argv[1] if len(sys.argv) > 1 else os.path.dirname(os.path.abspath(__file__))
    result_path = os.path.join(work_dir, "authoring_result.json")

    sw = None
    unattended_saved = None   # so teardown is safe if Dispatch fails
    try:
        if solidworks_running():
            RESULT["message"] = "SLDWORKS.exe already running; refusing to attach to a session this script does not own"
            return

        import pythoncom
        import win32com.client

        import unattended

        callout = win32com.client.VARIANT(pythoncom.VT_DISPATCH, None)
        warning_flag = win32com.client.VARIANT(pythoncom.VT_BOOL | pythoncom.VT_BYREF, False)

        g = json.loads(open(os.path.join(work_dir, "geometry.json")).read())
        oracle = json.loads(open(os.path.join(work_dir, "oracle.json")).read())
        density = g["material"]["density"]["value"]

        sw = win32com.client.Dispatch("SldWorks.Application")
        sw.Visible = False
        time.sleep(8)

        # No operator on this host: disable the prompts that would block a run.
        unattended_saved, RESULT["unattended"] = unattended.begin(sw)

        template = sw.GetUserPreferenceStringValue(SW_DEFAULT_PART_TEMPLATE)
        if not template or not os.path.exists(template):
            template = FALLBACK_PART_TEMPLATE
        stage("resolve_template", os.path.exists(template), template)

        for name, builder in (("mast_tube_stock", build_tube),
                              ("support_sleeve", build_sleeve),
                              ("root_clamp", build_clamp)):
            part = sw.NewDocument(template, 0, 0, 0)
            if not stage("%s_new_document" % name, part is not None):
                RESULT["message"] = "NewDocument returned nothing for %s" % name
                return
            builder(part, g, callout)
            finish_part(part, name, work_dir, density, oracle["parts"][name], warning_flag)
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
                unattended.end(sw, unattended_saved)
                sw.ExitApp()
        except Exception:
            pass
        with open(result_path, "w") as handle:
            json.dump(RESULT, handle, indent=2)


if __name__ == "__main__":
    main()
