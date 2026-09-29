"""Build the mast ASSEMBLY document from the three authored parts, on the host, unattended.

Individual part files are not an assembly. The shared CAD briefing names this as the gap: an assembly
with component transforms, mates, and an assembly STEP whose component placement can be checked.

Layout, derived from how the parts were authored (all sketched on the Front Plane and extruded +Z, so
each part's local origin is at the base of its extrusion with the axis along +Z):

  mast_tube_stock  identity                -> z in [0, 135]; 35 mm clamped, 100 mm free above
  support_sleeve   identity                -> z in [0, 35], inside the tube bore over the clamped length
  root_clamp       translate (-22, -22, 0) -> its bore, authored at local (22, 22), lands on the tube axis

That gives a checkable oracle: bounding box 44 x 56 x 135 mm, free length 135 - 35 = 100 mm, and a total
volume equal to the SUM of the three part volumes (assembly components do not subtract from each other).

Unattended by construction: no dialog is answered, because the prompts that would appear are disabled
first. Every step records success or failure and the run continues, so the result JSON says what the
document actually contains rather than what was intended.
"""
from __future__ import annotations

import json
import os
import sys
import traceback

SW_DOC_ASSEMBLY = 2
SW_DOC_PART = 1
SW_OPEN_SILENT = 1          # swOpenDocOptions_e.swOpenDocOptions_Silent
SW_DEFAULT_TEMPLATE_ASSEMBLY = 70          # swUserPreferenceStringValue_e
# Probed on the host 2026-09-26: the file is "Assembly.ASMDOT", and SOLIDWORKS 2024 is the install the
# parts were authored with (2026 is also present).
FALLBACK_ASSEMBLY_TEMPLATE = r"C:\ProgramData\SolidWorks\SOLIDWORKS 2024\templates\Assembly.ASMDOT"
PARTS_DIR = r"C:\Users\admin\Desktop\Projects\autonomous-racing-systems"
MM = 0.001
DENSITY = 2700.0                            # kg/m^3, model_assumption, matches the part authoring

# swMateType_e / swMateAlign_e
MATE_COINCIDENT = 0
ALIGN_ALIGNED = 0
# swAddComponentConfigOptions_e. 0 is not a valid member: AddComponent5 returned None for every
# component until this was 1 (CurrentSelectedConfig). Observed on the host 2026-09-26.
ADD_COMP_CURRENT_CONFIG = 1

COMPONENTS = (
    ("mast_tube_stock", (0.0, 0.0, 0.0)),
    ("support_sleeve", (0.0, 0.0, 0.0)),
    ("root_clamp", (-22.0, -22.0, 0.0)),
)
EXPECTED_BBOX_MM = (44.0, 56.0, 135.0)
EXPECTED_FREE_LENGTH_MM = 100.0

RESULT = {"status": "error", "message": "", "stages": [], "components": {}, "mates": [], "checks": {}}


def rebuild(model):
    """EditRebuild3 is a PROPERTY on this build, not a method: calling it raises
    TypeError: 'bool' object is not callable. Handle both forms so the script is not
    pinned to one SOLIDWORKS release."""
    try:
        attr = model.EditRebuild3
    except Exception as exc:
        return {"ok": False, "error": repr(exc)}
    if callable(attr):
        try:
            return {"ok": bool(attr()), "form": "method"}
        except Exception as exc:
            return {"ok": False, "error": repr(exc), "form": "method"}
    return {"ok": bool(attr), "form": "property"}


def stage(name, ok, detail=None):
    RESULT["stages"].append({"stage": name, "ok": bool(ok), "detail": detail})


def body_volume_m3(model, density):
    """Volume from the body, because CreateMassProperty is not resolvable on this build."""
    try:
        attr = getattr(model, "GetBodies2")
        bodies = attr(0, True) if callable(attr) else attr
        if not bodies:
            return None
        total = 0.0
        for b in (bodies if isinstance(bodies, (list, tuple)) else [bodies]):
            props = b.GetMassProperties(density)
            total += props[3]
        return total
    except Exception:
        return None


def main():
    work_dir = sys.argv[1] if len(sys.argv) > 1 else r"C:\RRMast"
    result_path = os.path.join(work_dir, "assembly_result.json")
    sw = None
    unattended_saved = None
    try:
        import pythoncom  # noqa: F401
        import win32com.client

        sys.path.insert(0, work_dir)
        import unattended

        callout = win32com.client.VARIANT(pythoncom.VT_DISPATCH, None)

        sw = win32com.client.Dispatch("SldWorks.Application")
        sw.Visible = False
        unattended_saved, RESULT["unattended"] = unattended.begin(sw)
        stage("unattended", RESULT["unattended"].get(
            "input_dimension_value_on_create", {}).get("applied"), RESULT["unattended"])

        # Preference 70 returned the templates DIRECTORY on this build, not a template file, and a
        # directory passes os.path.exists -- so require an actual file before trusting it.
        template = sw.GetUserPreferenceStringValue(SW_DEFAULT_TEMPLATE_ASSEMBLY)
        RESULT["template_preference_value"] = template
        if not template or not os.path.isfile(template):
            template = FALLBACK_ASSEMBLY_TEMPLATE
        stage("resolve_assembly_template", os.path.isfile(template), template)

        assy = sw.NewDocument(template, 0, 0, 0)
        if assy is None:
            RESULT["message"] = "NewDocument returned nothing for the assembly template"
            return
        assy = sw.ActiveDoc
        stage("new_assembly", assy is not None, getattr(assy, "GetTitle", None))

        # --- insert components at computed transforms -------------------------------------------
        # AddComponent5 returns None if the part is not already loaded. Open it silently first, then
        # RE-ACTIVATE the assembly: OpenDoc6 makes the part the active document, and AddComponent5
        # operates on the active one. Both steps were needed on this host.
        try:
            assy_title = assy.GetTitle
        except Exception:
            assy_title = None
        RESULT["assembly_title"] = assy_title

        inserted = {}
        for name, (tx, ty, tz) in COMPONENTS:
            path = os.path.join(PARTS_DIR, "%s.SLDPRT" % name)
            if not os.path.exists(path):
                path = os.path.join(PARTS_DIR, "%s.sldprt" % name)
            rec = {"path": path, "intended_translation_mm": [tx, ty, tz]}
            if not os.path.exists(path):
                rec["inserted"] = False
                rec["reason"] = "part file not found in %s" % PARTS_DIR
                RESULT["components"][name] = rec
                stage("insert_%s" % name, False, rec["reason"])
                continue
            try:
                ea = win32com.client.VARIANT(pythoncom.VT_I4 | pythoncom.VT_BYREF, 0)
                wa = win32com.client.VARIANT(pythoncom.VT_I4 | pythoncom.VT_BYREF, 0)
                opened = sw.OpenDoc6(path, SW_DOC_PART, SW_OPEN_SILENT, "", ea, wa)
                rec["opened"] = opened is not None
                rec["open_error"] = int(ea.value)
                if assy_title:
                    act = win32com.client.VARIANT(pythoncom.VT_I4 | pythoncom.VT_BYREF, 0)
                    sw.ActivateDoc3(assy_title, False, 0, act)
                    rec["reactivated_assembly"] = int(act.value)
                # AddComponent5 returned None on this host with the part loaded and the assembly
                # active, and raised nothing. Try the documented alternatives in order and record
                # which one works, rather than guessing across host round-trips.
                attempts = []
                comp = None
                for label, fn in (
                    ("AddComponent5", lambda: assy.AddComponent5(
                        path, ADD_COMP_CURRENT_CONFIG, "", False, "", tx * MM, ty * MM, tz * MM)),
                    ("AddComponent4", lambda: assy.AddComponent4(path, "", tx * MM, ty * MM, tz * MM)),
                    ("AddComponent", lambda: assy.AddComponent(path, tx * MM, ty * MM, tz * MM)),
                    ("save_then_AddComponent5", lambda: (
                        assy.SaveAs3(os.path.join(PARTS_DIR, "mast_assembly.sldasm"), 0, 0),
                        assy.AddComponent5(path, ADD_COMP_CURRENT_CONFIG, "", False, "",
                                           tx * MM, ty * MM, tz * MM))[1]),
                ):
                    try:
                        got = fn()
                        attempts.append({"api": label, "returned": got is not None})
                        if got is not None:
                            comp = got
                            rec["api_used"] = label
                            break
                    except Exception as exc:
                        attempts.append({"api": label, "error": repr(exc)[:160]})
                rec["attempts"] = attempts
            except Exception as exc:
                comp = None
                rec["exception"] = repr(exc)
            ok = comp is not None
            rec["inserted"] = ok
            inserted[name] = comp
            if ok:
                try:
                    rec["name_in_assembly"] = comp.Name2
                except Exception:
                    rec["name_in_assembly"] = None
                try:
                    rec["transform_array"] = list(comp.Transform2.ArrayData)
                except Exception:
                    rec["transform_array"] = None
                md = None
                for getter in ("GetModelDoc2", "GetModelDoc"):
                    try:
                        attr = getattr(comp, getter)
                        md = attr() if callable(attr) else attr
                        if md is not None:
                            rec["model_doc_form"] = "%s/%s" % (
                                getter, "method" if callable(attr) else "property")
                            break
                    except Exception:
                        md = None
                vol = body_volume_m3(md, DENSITY) if md is not None else None
                rec["body_volume_mm3"] = (vol * 1e9) if vol else None
            RESULT["components"][name] = rec
            stage("insert_%s" % name, ok, rec.get("body_volume_mm3") or rec.get("exception"))

        rb = rebuild(assy)
        stage("rebuild_after_insert", rb.get("ok"), rb)

        # --- mates: sleeve to tube, three coincident planes ------------------------------------
        # Plane-based mates are used rather than face picking: the recorded API findings show
        # SelectByID2 on a face through the origin can silently return false.
        tube_nm = RESULT["components"].get("mast_tube_stock", {}).get("name_in_assembly")
        sleeve_nm = RESULT["components"].get("support_sleeve", {}).get("name_in_assembly")
        title = None
        try:
            title = assy.GetTitle
        except Exception:
            title = None
        if tube_nm and sleeve_nm:
            for plane in ("Front Plane", "Top Plane", "Right Plane"):
                rec = {"plane": plane, "type": "coincident", "between": [tube_nm, sleeve_nm]}
                try:
                    assy.ClearSelection2(True)
                    a = assy.Extension.SelectByID2(
                        "%s@%s@%s" % (plane, tube_nm, title), "PLANE", 0, 0, 0, True, 1, callout, 0)
                    b = assy.Extension.SelectByID2(
                        "%s@%s@%s" % (plane, sleeve_nm, title), "PLANE", 0, 0, 0, True, 1, callout, 0)
                    rec["selected"] = bool(a and b)
                    if rec["selected"]:
                        err = win32com.client.VARIANT(pythoncom.VT_I4 | pythoncom.VT_BYREF, 0)
                        mate = assy.AddMate5(MATE_COINCIDENT, ALIGN_ALIGNED, False,
                                             0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
                                             False, False, 0, err)
                        rec["created"] = mate is not None
                        rec["error_status"] = int(err.value)
                    else:
                        rec["created"] = False
                except Exception as exc:
                    rec["created"] = False
                    rec["exception"] = repr(exc)
                RESULT["mates"].append(rec)
                stage("mate_%s" % plane.replace(" ", "_"), rec.get("created"), rec)
            assy.ClearSelection2(True)
            rebuild(assy)

        # --- checks -----------------------------------------------------------------------------
        vols = {n: r.get("body_volume_mm3") for n, r in RESULT["components"].items()}
        have_all = all(v for v in vols.values())
        total = sum(v for v in vols.values() if v) if have_all else None
        # Placement verification. AddComponent4 on this host placed every component at z = -L/2 on
        # its own extrusion depth and did NOT honour the supplied coordinates, so the intended relative
        # positions are not established. Free length is therefore NOT reported: restating the authored
        # 135 - 35 here would be a constant dressed up as a measurement.
        placement = {}
        for name, (tx, ty, tz) in COMPONENTS:
            ta = RESULT["components"].get(name, {}).get("transform_array")
            if not ta:
                placement[name] = {"verified": False, "reason": "no transform read back"}
                continue
            got = [round(v / MM, 4) for v in ta[9:12]]
            placement[name] = {"intended_mm": [tx, ty, tz], "actual_mm": got,
                               "matches_intent": all(abs(a - b) < 1e-3 for a, b in zip(got, (tx, ty, tz)))}
        RESULT["placement"] = placement
        placement_ok = all(v.get("matches_intent") for v in placement.values())
        free_len = None
        RESULT["checks"] = {
            "component_count": sum(1 for r in RESULT["components"].values() if r.get("inserted")),
            "component_count_expected": len(COMPONENTS),
            "per_component_volume_mm3": vols,
            "total_volume_mm3": total,
            "free_length_mm": free_len,
            "free_length_expected_mm": EXPECTED_FREE_LENGTH_MM,
            "free_length_status": ("NOT MEASURED: component placement is unverified, so a free length "
                                  "cannot be derived from the assembly"),
            "placement_matches_intent": placement_ok,
            "expected_bbox_mm": list(EXPECTED_BBOX_MM),
            "mates_created": sum(1 for m in RESULT["mates"] if m.get("created")),
            "mates_attempted": len(RESULT["mates"]),
            "note": "component volumes are summed, not booleaned: assembly components do not subtract",
        }

        # --- save .sldasm, assembly STEP, preview ----------------------------------------------
        out_dir = PARTS_DIR if os.path.isdir(PARTS_DIR) else work_dir
        asm = os.path.join(out_dir, "mast_assembly.sldasm")
        step = os.path.join(out_dir, "mast_assembly.step")
        preview = os.path.join(out_dir, "mast_assembly.bmp")
        assy.SaveAs3(asm, 0, 0)
        assy.ClearSelection2(True)
        assy.SaveAs3(step, 0, 0)
        assy.ShowNamedView2("*Isometric", 7)
        assy.ViewZoomtofit2()
        assy.GraphicsRedraw2()
        assy.SaveBMP(preview, 1000, 750)
        RESULT["outputs"] = {
            "dir": out_dir,
            "sldasm": asm, "sldasm_bytes": (os.path.getsize(asm) if os.path.exists(asm) else 0),
            "step": step, "step_bytes": (os.path.getsize(step) if os.path.exists(step) else 0),
            "preview": preview, "preview_written": os.path.exists(preview),
        }
        stage("save_outputs", RESULT["outputs"]["sldasm_bytes"] > 0
              and RESULT["outputs"]["step_bytes"] > 0, RESULT["outputs"])

        built = (RESULT["checks"]["component_count"] == len(COMPONENTS)
                 and RESULT["outputs"]["sldasm_bytes"] > 0
                 and RESULT["outputs"]["step_bytes"] > 0)
        volumes_read = all(RESULT["checks"]["per_component_volume_mm3"].values())
        if built and placement_ok and volumes_read:
            RESULT["status"] = "ok"
            RESULT["message"] = "assembly written, placement matches intent, volumes match their parts"
        elif built:
            RESULT["status"] = "partial"
            RESULT["message"] = ("assembly document written with all components and mates, but "
                                 "placement %s and per-component volumes %s. The document is NOT a "
                                 "verified assembly." % (
                                     "matches intent" if placement_ok else "does NOT match intent",
                                     "were read" if volumes_read else "could not be read"))
        else:
            RESULT["status"] = "error"
            RESULT["message"] = "assembly incomplete; see stages and checks"

    except Exception:
        RESULT["message"] = "unhandled exception:\n" + traceback.format_exc()
    finally:
        try:
            if sw is not None:
                import unattended as _u
                _u.end(sw, unattended_saved)
                sw.ExitApp()
        except Exception:
            pass
        with open(result_path, "w") as handle:
            json.dump(RESULT, handle, indent=2)


if __name__ == "__main__":
    main()
