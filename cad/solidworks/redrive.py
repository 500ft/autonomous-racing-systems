"""Re-drive the authored parts from their global variables. Runs on the host.

The acceptance test for a parametric model is not that equations exist. Equations
can be present, accepted by Add2, and still drive nothing. The test is that
changing a declared global variable and rebuilding produces the geometry that
change implies.

Opens each saved part, sets one global variable, rebuilds, and measures against
an oracle built for the new value. Saves nothing: the parts on disk keep their
authored values.

Invoked on the host as: python redrive.py <work_dir>
"""
import json
import os
import subprocess
import sys
import time
import traceback

SW_DOC_PART = 1
SW_SOLID_BODY = 0
VOLUME_TOLERANCE_REL = 1e-6

PARTS_DIR = r"C:\Users\admin\Desktop\Projects\autonomous-racing-systems"

VARIABLE = "ClampEngagement"
NEW_VALUE_MM = 40.0

RESULT = {"status": "error", "message": "", "variable": VARIABLE,
          "new_value_mm": NEW_VALUE_MM, "parts": {}}


def solidworks_running():
    out = subprocess.run(["tasklist", "/FI", "IMAGENAME eq SLDWORKS.exe"],
                         capture_output=True, text=True).stdout
    return "SLDWORKS.EXE" in out.upper()


def main():
    work_dir = sys.argv[1] if len(sys.argv) > 1 else os.path.dirname(os.path.abspath(__file__))
    result_path = os.path.join(work_dir, "redrive_result.json")

    sw = None
    unattended_saved = None   # so teardown is safe if Dispatch fails
    try:
        if solidworks_running():
            RESULT["message"] = "SLDWORKS.exe already running; refusing to attach"
            return

        import pythoncom
        import win32com.client

        import unattended

        long_a = win32com.client.VARIANT(pythoncom.VT_I4 | pythoncom.VT_BYREF, 0)
        long_b = win32com.client.VARIANT(pythoncom.VT_I4 | pythoncom.VT_BYREF, 0)

        g = json.loads(open(os.path.join(work_dir, "geometry.json")).read())
        oracle = json.loads(open(os.path.join(work_dir, "oracle_redrive.json")).read())
        density = g["material"]["density"]["value"]

        sw = win32com.client.Dispatch("SldWorks.Application")
        sw.Visible = False

        # No operator on this host: disable the prompts that would block a run.
        unattended_saved, RESULT["unattended"] = unattended.begin(sw)

        for name in ("mast_tube_stock", "support_sleeve", "root_clamp"):
            parts_dir = PARTS_DIR if os.path.isdir(PARTS_DIR) else work_dir
            path = os.path.join(parts_dir, "%s.sldprt" % name)
            # Open latency on this host is unstable and a failure is not
            # reproducible, so the open is retried rather than trusted once.
            doc, last_error = None, None
            for _ in range(4):
                try:
                    doc = sw.OpenDoc6(path, SW_DOC_PART, 0, "", long_a, long_b)
                    if doc is not None:
                        break
                except Exception as error:
                    last_error = error
                    time.sleep(5)
            if doc is None:
                RESULT["parts"][name] = {"accepted": False,
                                         "message": "could not open %s: %s" % (path, last_error)}
                continue

            eq_mgr = doc.GetEquationMgr
            before = None
            bodies = doc.GetBodies2(SW_SOLID_BODY, True)
            if bodies:
                before = bodies[0].GetMassProperties(density)[3] * 1e9

            changed = []
            for index in range(eq_mgr.GetCount):
                text = eq_mgr.Equation(index) or ""
                if text.strip().startswith('"%s"' % VARIABLE) and "=" in text:
                    # A declaration, not a link: the right side is a literal.
                    if '"' not in text.split("=", 1)[1]:
                        eq_mgr.Equation(index, '"%s"= %gmm' % (VARIABLE, NEW_VALUE_MM))
                        changed.append({"index": index, "readback": eq_mgr.Equation(index)})
            eq_mgr.EvaluateAll
            rebuilt = doc.ForceRebuild3(False)

            bodies = doc.GetBodies2(SW_SOLID_BODY, True)
            count = len(bodies) if bodies else 0
            after = bodies[0].GetMassProperties(density)[3] * 1e9 if bodies else 0.0
            expected = oracle["parts"][name]["volume_mm3"]
            error_rel = abs(after - expected) / expected if expected else None

            RESULT["parts"][name] = {
                "equations_changed": changed,
                "rebuilt": bool(rebuilt),
                "volume_before_mm3": before,
                "volume_after_mm3": after,
                "oracle_after_mm3": expected,
                "error_rel": error_rel,
                "n_solids": count,
                "accepted": bool(changed) and count == 1 and error_rel is not None
                            and error_rel <= VOLUME_TOLERANCE_REL,
            }
            # Close without saving: the authored values stay on disk.
            sw.CloseDoc(doc.GetTitle)

        all_ok = all(p.get("accepted") for p in RESULT["parts"].values())
        RESULT["status"] = "ok" if all_ok else "error"
        RESULT["message"] = ("every part re-drove to its new oracle" if all_ok
                             else "at least one part did not re-drive")

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
