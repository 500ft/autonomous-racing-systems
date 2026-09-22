"""Determine how Right Plane sketch coordinates map to global axes. Runs on the host.

A sketch drawn on a named plane does not advertise which global axes its local x
and y correspond to, and guessing cost a build iteration. This draws a single
known circle on the Right Plane, extrudes it, and reports the resulting bounding
box, from which the mapping is read directly.

Invoked on the host as: python probe_right_plane.py <work_dir>
"""
import json
import os
import sys
import traceback

SW_DEFAULT_PART_TEMPLATE = 69
FALLBACK_PART_TEMPLATE = r"C:\ProgramData\SolidWorks\SOLIDWORKS 2024\templates\Part.prtdot"
MM = 0.001

SKETCH_X_MM = 10.0   # local sketch x
SKETCH_Y_MM = 20.0   # local sketch y
RADIUS_MM = 2.0
EXTRUDE_MM = 5.0

RESULT = {"status": "error", "message": "", "probe": {}}


def main():
    work_dir = sys.argv[1] if len(sys.argv) > 1 else os.path.dirname(os.path.abspath(__file__))
    sw = None
    try:
        import pythoncom
        import win32com.client

        callout = win32com.client.VARIANT(pythoncom.VT_DISPATCH, None)
        sw = win32com.client.Dispatch("SldWorks.Application")
        sw.Visible = False

        template = sw.GetUserPreferenceStringValue(SW_DEFAULT_PART_TEMPLATE)
        if not template or not os.path.exists(template):
            template = FALLBACK_PART_TEMPLATE
        part = sw.NewDocument(template, 0, 0, 0)

        selected = part.Extension.SelectByID2("Right Plane", "PLANE", 0.0, 0.0, 0.0,
                                              False, 0, callout, 0)
        RESULT["probe"]["selected_right_plane"] = bool(selected)

        sketch_mgr = part.SketchManager
        sketch_mgr.InsertSketch(True)
        sketch_mgr.CreateCircleByRadius(SKETCH_X_MM * MM, SKETCH_Y_MM * MM, 0.0, RADIUS_MM * MM)
        sketch_mgr.InsertSketch(True)

        feature = part.FeatureManager.FeatureExtrusion3(
            True, False, False, 0, 0, EXTRUDE_MM * MM, 0.0, False, False, False, False,
            0, 0, False, False, False, False, True, True, True, 0, 0, False)
        RESULT["probe"]["extruded"] = feature is not None

        box = part.GetPartBox(True)
        RESULT["probe"]["part_box_m"] = [float(v) for v in box] if box else None
        if box:
            xmin, ymin, zmin, xmax, ymax, zmax = [float(v) / MM for v in box]
            RESULT["probe"]["part_box_mm"] = {
                "x": [xmin, xmax], "y": [ymin, ymax], "z": [zmin, zmax]}
            centre = {"x": (xmin + xmax) / 2, "y": (ymin + ymax) / 2, "z": (zmin + zmax) / 2}
            RESULT["probe"]["centre_mm"] = centre
            RESULT["probe"]["interpretation"] = (
                "sketch x=%.1f, y=%.1f -> global centre x=%.3f y=%.3f z=%.3f"
                % (SKETCH_X_MM, SKETCH_Y_MM, centre["x"], centre["y"], centre["z"]))

        RESULT["status"] = "ok"
        RESULT["message"] = "probe complete"
        sw.CloseDoc(part.GetTitle)
    except Exception:
        RESULT["message"] = "unhandled exception:\n" + traceback.format_exc()
    finally:
        try:
            if sw is not None:
                sw.ExitApp()
        except Exception:
            pass
        with open(os.path.join(work_dir, "probe_result.json"), "w") as handle:
            json.dump(RESULT, handle, indent=2)


if __name__ == "__main__":
    main()
