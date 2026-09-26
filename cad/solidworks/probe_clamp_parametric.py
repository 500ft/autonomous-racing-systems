"""Do ClampWidth and ClampHeight actually drive the clamp? Runs on the host.

`redrive.py` changes one variable, `ClampEngagement`, and it passed at 1e-15. That
variable drives `depth_dim`, an extrude depth -- a *feature* dimension. The clamp's
other two size variables drive `width_dim` and `height_dim`, which are *sketch*
dimensions added after `CreateCornerRectangle`, and that is a different case.

Measured on this same host by `500ft/engineering-audit -> cadloop/scaffold/`:
`CreateCornerRectangle` dimensions its own rectangle. Dimensions added afterwards
are a second pair on the same two edges; they report driving, the tool's already
fix the geometry, and driving ours moves nothing. The part still measures exactly
right, because it was drawn at the intended size. There, the feature dimension
drove correctly while both sketch dimensions were inert -- which is precisely the
split this file tests for on the clamp.

No oracle is needed for the answer. If `ClampWidth` is changed by a third and the
volume does not move at all, the equation drives nothing. That is conclusive on its
own; the exact expected volume only matters once it is known to be driving.

Nothing is saved: root_clamp.sldprt keeps its authored values.

Invoked on the host as: python probe_clamp_parametric.py <work_dir>
"""
import json
import os
import subprocess
import sys
import traceback

SW_DOC_PART = 1
SW_SOLID_BODY = 0
MM = 0.001
PARTS_DIR = r"C:\Users\admin\Desktop\Projects\autonomous-racing-systems"

# Each is changed on its own, from a freshly opened copy of the part.
CASES = (("ClampWidth", 40.0), ("ClampHeight", 40.0), ("ClampEngagement", 40.0))

RESULT = {"status": "error", "message": "", "cases": [], "dimensions": []}


def solidworks_running():
    out = subprocess.run(["tasklist", "/FI", "IMAGENAME eq SLDWORKS.exe"],
                         capture_output=True, text=True).stdout
    return "SLDWORKS.EXE" in out.upper()


def short_name(dimension):
    return "@".join(dimension.FullName.split("@")[:2])


def volume_mm3(part, density):
    bodies = part.GetBodies2(SW_SOLID_BODY, True)
    return bodies[0].GetMassProperties(density)[3] * 1e9 if bodies else 0.0


def body_count(part):
    bodies = part.GetBodies2(SW_SOLID_BODY, True)
    return len(bodies) if bodies else 0


def all_dimensions(part):
    """Every dimension in the part, with its driven state, read after a solve."""
    out = []
    feature = part.FirstFeature
    while feature is not None:
        display = feature.GetFirstDisplayDimension
        while display is not None:
            dimension = display.GetDimension2(0)
            out.append({"feature": feature.Name,
                        "name": short_name(dimension),
                        "value_mm": dimension.SystemValue / MM,
                        "driven_state": dimension.DrivenState})
            display = feature.GetNextDisplayDimension(display)
        feature = feature.GetNextFeature
    return out


def set_global(part, name, value_mm):
    """Rewrite a declaration, never a link: a link's right side is a quoted name."""
    manager = part.GetEquationMgr
    for index in range(manager.GetCount):
        text = (manager.Equation(index) or "").strip()
        if text.startswith('"%s"' % name) and "=" in text:
            if '"' not in text.split("=", 1)[1]:
                manager.Equation(index, '"%s"= %gmm' % (name, value_mm))
                return manager.Equation(index)
    return None


def main():
    work_dir = sys.argv[1] if len(sys.argv) > 1 else os.path.dirname(os.path.abspath(__file__))
    sw = None
    saved = None
    try:
        if solidworks_running():
            RESULT["message"] = "SLDWORKS.exe already running; refusing to attach"
            return

        import pythoncom
        import win32com.client

        import unattended

        warning_flag = win32com.client.VARIANT(pythoncom.VT_I4 | pythoncom.VT_BYREF, 0)
        long_b = win32com.client.VARIANT(pythoncom.VT_I4 | pythoncom.VT_BYREF, 0)

        g = json.loads(open(os.path.join(work_dir, "geometry.json")).read())
        density = g["material"]["density"]["value"]

        sw = win32com.client.Dispatch("SldWorks.Application")
        sw.Visible = False
        saved, RESULT["unattended"] = unattended.begin(sw)

        parts_dir = PARTS_DIR if os.path.isdir(PARTS_DIR) else work_dir
        part_path = os.path.join(parts_dir, "root_clamp.sldprt")
        RESULT["part_path"] = part_path

        # Baseline, and the dimension inventory the answer will be read against.
        part = sw.OpenDoc6(part_path, SW_DOC_PART, 0, "", warning_flag, long_b)
        if part is None:
            RESULT["message"] = "could not open %s" % part_path
            return
        part.ForceRebuild3(False)
        baseline = volume_mm3(part, density)
        RESULT["baseline_volume_mm3"] = baseline
        RESULT["dimensions"] = all_dimensions(part)
        sw.CloseDoc(part.GetTitle)

        for variable, new_value in CASES:
            part = sw.OpenDoc6(part_path, SW_DOC_PART, 0, "", warning_flag, long_b)
            entry = {"variable": variable, "new_value_mm": new_value}
            if part is None:
                entry["error"] = "could not reopen the part"
                RESULT["cases"].append(entry)
                continue

            entry["applied"] = set_global(part, variable, new_value)
            part.ForceRebuild3(False)
            measured = volume_mm3(part, density)
            entry.update(
                baseline_volume_mm3=baseline,
                measured_volume_mm3=measured,
                n_solids=body_count(part),
                delta_mm3=measured - baseline,
                # The whole question, in one field: did the geometry move at all?
                drives_geometry=abs(measured - baseline) > 1e-6,
            )
            RESULT["cases"].append(entry)
            sw.CloseDoc(part.GetTitle)      # never saved

        inert = [c["variable"] for c in RESULT["cases"] if c.get("drives_geometry") is False]
        RESULT["inert_variables"] = inert
        RESULT["status"] = "ok"
        RESULT["message"] = ("every variable moved the geometry"
                             if not inert else
                             "these variables changed nothing: %s" % ", ".join(inert))

    except Exception:
        RESULT["message"] = "unhandled exception:\n" + traceback.format_exc()
    finally:
        try:
            if sw is not None and saved is not None:
                import unattended
                RESULT["unattended_restored"] = unattended.end(sw, saved)
            if sw is not None:
                sw.ExitApp()
        except Exception:
            pass
        with open(os.path.join(work_dir, "probe_clamp_result.json"), "w") as handle:
            json.dump(RESULT, handle, indent=2)


if __name__ == "__main__":
    main()
