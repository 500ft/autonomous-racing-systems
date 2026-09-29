"""Build the mast ASSEMBLY document from the three authored parts, on the host, unattended.

Individual part files are not an assembly. The shared CAD briefing names this as the gap: an assembly
with component transforms, mates, and an assembly STEP whose component placement can be checked.

Layout, derived from how the parts were authored (all sketched on the Front Plane and extruded +Z, so
each part's local origin is at the base of its extrusion with the axis along +Z):

  mast_tube_stock  identity                -> z in [0, 135]; 35 mm clamped, 100 mm free above
  support_sleeve   identity                -> z in [0, 35], inside the tube bore over the clamped length
  root_clamp       translate (-22, -22, 0) -> its bore, authored at local (22, 22), lands on the tube axis

AddComponent4 does not place the part ORIGIN at the supplied point (it centred each part's box there:
transform z = -L/2), so placement is set explicitly through Component2.Transform2 and read back AFTER the
mates and a rebuild, then again on the reopened .sldasm. Expected values come from oracle_assembly.json
(CadQuery, positioned solids); nothing is compared against a constant restated here: box 44 x 56 x 135 mm,
per-component volume, total = SUM of the parts (components do not subtract), and the free length is
derived from the read-back tube and clamp z-extents.

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
TOL_MM = 1e-3
REL_VOL = 1e-6
MOVE_DELTA_MM = (10.0, 5.0, 3.0)            # parameter-change test on root_clamp

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


def _get(obj, name, *args):
    """Members named GetX are properties on some builds and methods on others."""
    attr = getattr(obj, name)
    if not callable(attr):
        return attr
    try:
        return attr(*args)
    except Exception:
        if args:
            raise
        return attr   # a property that returned a dispatch object: "calling" it is Member not found


def _byref_i4():
    import pythoncom
    import win32com.client
    return win32com.client.VARIANT(pythoncom.VT_I4 | pythoncom.VT_BYREF, 0)


def set_transform(sw, comp, t_mm):
    """Set the component's placement explicitly: identity rotation, translation in mm.
    The 16-double array is 9 rotation, 3 translation, scale, 3 unused; IMathTransform.ArrayData and
    IComponent2.Transform2 both have setters."""
    import pythoncom
    import win32com.client
    arr = [1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0,
           t_mm[0] * MM, t_mm[1] * MM, t_mm[2] * MM, 1.0, 0.0, 0.0, 0.0]
    # IMathUtility.CreateTransform raised "Member not found" / a server exception on this build with every
    # argument form tried (probed 2026-09-29); the component's own transform object takes the array.
    mt = comp.Transform2
    mt.ArrayData = win32com.client.VARIANT(pythoncom.VT_ARRAY | pythoncom.VT_R8, arr)
    try:
        comp.Transform2 = mt
        return {"ok": True, "form": "setattr"}
    except Exception as exc:
        first = repr(exc)[:160]
    try:  # DISPATCH_PROPERTYPUTREF: the value is an object
        dispid = comp._oleobj_.GetIDsOfNames("Transform2")[0]
        comp._oleobj_.Invoke(dispid, 0, 8, 0, mt)
        return {"ok": True, "form": "Invoke PROPERTYPUTREF", "setattr_error": first}
    except Exception as exc:
        return {"ok": False, "error": repr(exc)[:160], "setattr_error": first}


def read_transform(comp):
    ta = list(comp.Transform2.ArrayData)
    ident = [1, 0, 0, 0, 1, 0, 0, 0, 1]
    return {"translation_mm": [v / MM for v in ta[9:12]],
            "rotation_is_identity": all(abs(a - b) < 1e-9 for a, b in zip(ta[:9], ident)),
            "scale": ta[12]}


def comp_volume_mm3(comp):
    """Volume from the component's solid bodies. IModelDoc2 has no GetBodies2 on this build (it is an
    IPartDoc member), so ask the component: IComponent2.GetBodies3(swSolidBody=0, count byref).
    IBody2.GetMassProperties(density)[3] is volume in m^3. Falls back to the part doc."""
    tried = []
    for how in ("Component2.GetBodies3", "ModelDoc2.GetBodies2"):
        try:
            if how.startswith("Component2"):
                bodies = comp.GetBodies3(0, _byref_i4())
            else:
                md = _get(comp, "GetModelDoc2")
                bodies = _get(md, "GetBodies2", 0, True)
            if not bodies:
                tried.append({how: "no bodies"})
                continue
            bodies = bodies if isinstance(bodies, (list, tuple)) else [bodies]
            return sum(b.GetMassProperties(DENSITY)[3] for b in bodies) * 1e9, how, len(bodies), tried
        except Exception as exc:
            tried.append({how: repr(exc)[:160]})
    return None, None, 0, tried


def measure(assy):
    """Read the assembly back: per-component transform, box, volume, and the assembly box."""
    comps = {}
    for c in _get(assy, "GetComponents", True) or []:
        comps[c.Name2.rsplit("-", 1)[0]] = c
    out = {"components": {}}
    for name, c in comps.items():
        rec = {}
        try:
            rec.update(read_transform(c))
        except Exception as exc:
            rec["transform_error"] = repr(exc)[:160]
        try:
            b = list(c.GetBox(False, False))
            rec["box_min_mm"], rec["box_max_mm"] = [v / MM for v in b[:3]], [v / MM for v in b[3:6]]
        except Exception as exc:
            rec["box_error"] = repr(exc)[:160]
        rec["volume_mm3"], rec["volume_api"], rec["n_bodies"], rec["volume_attempts"] = comp_volume_mm3(c)
        out["components"][name] = rec
    try:
        b = list(_get(assy, "GetBox", 0))
        out["assembly_box_min_mm"], out["assembly_box_max_mm"] = [v / MM for v in b[:3]], [v / MM for v in b[3:6]]
        out["assembly_box_source"] = "IAssemblyDoc.GetBox"
    except Exception as exc:
        out["assembly_box_error"] = repr(exc)[:160]
    return out, comps


def _near(a, b, tol=TOL_MM):
    return a is not None and b is not None and len(a) == len(b) and all(abs(x - y) <= tol for x, y in zip(a, b))


def evaluate(m, exp, shift=None):
    """Compare a read-back to the CadQuery oracle. Unmeasured is a failure, never a pass.
    `shift` = (name, delta_mm) moves that component's expected translation and box."""
    ec = {n: dict(c) for n, c in exp["components"].items()}
    if shift:
        n, d = shift
        for k in ("translation_mm", "box_min_mm", "box_max_mm"):
            ec[n][k] = [a + b for a, b in zip(ec[n][k], d)]
    c, ok = {}, True
    for name, e in ec.items():
        r = m["components"].get(name, {})
        chk = {"translation_mm": r.get("translation_mm"), "translation_expected_mm": e["translation_mm"],
               "translation_ok": _near(r.get("translation_mm"), e["translation_mm"]) and bool(
                   r.get("rotation_is_identity")),
               "box_min_mm": r.get("box_min_mm"), "box_max_mm": r.get("box_max_mm"),
               "box_ok": _near(r.get("box_min_mm"), e["box_min_mm"]) and _near(r.get("box_max_mm"), e["box_max_mm"]),
               "volume_mm3": r.get("volume_mm3"), "volume_expected_mm3": e["volume_mm3"],
               "volume_api": r.get("volume_api")}
        chk["volume_ok"] = (r.get("volume_mm3") is not None
                            and abs(r["volume_mm3"] - e["volume_mm3"]) / e["volume_mm3"] <= REL_VOL)
        ok = ok and chk["translation_ok"] and chk["box_ok"] and chk["volume_ok"]
        c[name] = chk
    lo, hi = m.get("assembly_box_min_mm"), m.get("assembly_box_max_mm")
    elo = [min(e["box_min_mm"][i] for e in ec.values()) for i in range(3)]
    ehi = [max(e["box_max_mm"][i] for e in ec.values()) for i in range(3)]
    asm = {"box_min_mm": lo, "box_max_mm": hi, "bbox_mm": [h - l for l, h in zip(lo, hi)] if lo and hi else None,
           "bbox_expected_mm": [h - l for l, h in zip(elo, ehi)]}
    asm["ok"] = _near(lo, elo) and _near(hi, ehi)
    vols = [x["volume_mm3"] for x in c.values()]
    total = sum(vols) if all(v is not None for v in vols) else None
    tot_exp = exp["assembly"]["total_volume_mm3"]
    tot = {"total_volume_mm3": total, "expected_mm3": tot_exp,
           "ok": total is not None and abs(total - tot_exp) / tot_exp <= REL_VOL}
    # Free length from the READ-BACK tube and clamp z-extents, not from a constant.
    tz = c["mast_tube_stock"]["box_max_mm"]
    cz = c["root_clamp"]["box_max_mm"]
    free = (tz[2] - cz[2]) if tz and cz else None
    fl = {"free_length_mm": free, "expected_mm": exp["free_length_mm"],
          "derived_from": "tube box_max z - clamp box_max z (read back)",
          "ok": (not shift) and free is not None and abs(free - exp["free_length_mm"]) <= TOL_MM}
    if shift:
        fl["ok"] = None   # only meaningful in the nominal placement
    ok = ok and asm["ok"] and tot["ok"] and (fl["ok"] is not False)
    return {"ok": bool(ok), "components": c, "assembly": asm, "total": tot, "free_length": fl}


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

        with open(os.path.join(work_dir, "oracle_assembly.json")) as fh:
            exp = json.load(fh)

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

        # --- insert components -------------------------------------------------------------------
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
                ea, wa = _byref_i4(), _byref_i4()
                opened = sw.OpenDoc6(path, SW_DOC_PART, SW_OPEN_SILENT, "", ea, wa)
                rec["opened"] = opened is not None
                rec["open_error"] = int(ea.value)
                if assy_title:
                    act = _byref_i4()
                    sw.ActivateDoc3(assy_title, False, 0, act)
                    rec["reactivated_assembly"] = int(act.value)
                # Try the documented alternatives in order and record which one works.
                attempts = []
                comp = None
                for label, fn in (
                    ("AddComponent5", lambda: assy.AddComponent5(
                        path, ADD_COMP_CURRENT_CONFIG, "", False, "", tx * MM, ty * MM, tz * MM)),
                    ("AddComponent4", lambda: assy.AddComponent4(path, "", tx * MM, ty * MM, tz * MM)),
                    ("AddComponent", lambda: assy.AddComponent(path, tx * MM, ty * MM, tz * MM)),
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
            rec["inserted"] = comp is not None
            inserted[name] = comp
            if comp is not None:
                try:
                    rec["name_in_assembly"] = comp.Name2
                    # Recorded as the "before" of the placement fix; it is stale by design.
                    rec["transform_at_insert_mm"] = read_transform(comp)["translation_mm"]
                except Exception as exc:
                    rec["transform_error"] = repr(exc)[:160]
            RESULT["components"][name] = rec
            stage("insert_%s" % name, rec["inserted"], rec.get("exception"))

        rb = rebuild(assy)
        stage("rebuild_after_insert", rb.get("ok"), rb)

        # --- placement: set explicitly, fix the tube ---------------------------------------------
        def place(only=None):
            for name, (tx, ty, tz) in COMPONENTS:
                if inserted.get(name) is None or (only and name not in only):
                    continue
                res = set_transform(sw, inserted[name], (tx, ty, tz))
                RESULT["components"][name].setdefault("set_transform", []).append(res)
                stage("set_transform_%s" % name, res.get("ok"), res)

        place()
        tube_nm = RESULT["components"].get("mast_tube_stock", {}).get("name_in_assembly")
        sleeve_nm = RESULT["components"].get("support_sleeve", {}).get("name_in_assembly")
        title = assy_title
        if tube_nm:
            try:
                assy.ClearSelection2(True)
                sel = assy.Extension.SelectByID2("%s@%s" % (tube_nm, title), "COMPONENT",
                                                 0, 0, 0, False, 0, callout, 0)
                if sel:
                    _get(assy, "FixComponent")
                assy.ClearSelection2(True)
                stage("fix_tube", sel, {"selected": bool(sel)})
            except Exception as exc:
                stage("fix_tube", False, repr(exc)[:160])
        rebuild(assy)

        # --- mates: sleeve to tube, three coincident planes ------------------------------------
        # Plane-based mates are used rather than face picking: the recorded API findings show
        # SelectByID2 on a face through the origin can silently return false.
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
                        err = _byref_i4()
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

        # --- in-memory read-back AFTER mates + rebuild; re-set anything off and read again ------
        m1, _ = measure(assy)
        RESULT["placement_after_mates"] = {n: r.get("translation_mm") for n, r in m1["components"].items()}
        off = [n for n, e in exp["components"].items()
               if not _near(m1["components"].get(n, {}).get("translation_mm"), e["translation_mm"])]
        RESULT["placement_reset_needed"] = off
        if off:
            place(only=off)
            rebuild(assy)
        m2, _ = measure(assy)
        RESULT["in_memory"] = evaluate(m2, exp)

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

        # --- reopen the saved file from disk; that, not the session above, is what is accepted ----
        try:
            _get(sw, "CloseAllDocuments", True)
        except Exception as exc:
            stage("close_all", False, repr(exc)[:160])
        ea, wa = _byref_i4(), _byref_i4()
        re_assy = sw.OpenDoc6(asm, SW_DOC_ASSEMBLY, SW_OPEN_SILENT, "", ea, wa)
        stage("reopen_sldasm", re_assy is not None, {"error": int(ea.value), "warning": int(wa.value)})
        if re_assy is None:
            RESULT["message"] = "saved .sldasm did not reopen"
            RESULT["reopened"] = None
        else:
            m3, comps3 = measure(re_assy)
            RESULT["reopened"] = evaluate(m3, exp)

            # --- parameter-change test: move root_clamp by a known delta, re-read, restore ---------
            clamp = comps3.get("root_clamp")
            pc = {"delta_mm": list(MOVE_DELTA_MM)}
            if clamp is None:
                pc["ok"] = False
                pc["reason"] = "root_clamp not found in reopened assembly"
            else:
                t0 = read_transform(clamp)["translation_mm"]
                pc["set_moved"] = set_transform(sw, clamp, [a + b for a, b in zip(t0, MOVE_DELTA_MM)])
                rebuild(re_assy)
                m4, _ = measure(re_assy)
                t1 = m4["components"]["root_clamp"].get("translation_mm")
                pc["measured_delta_mm"] = [a - b for a, b in zip(t1, t0)] if t1 else None
                pc["delta_ok"] = _near(pc["measured_delta_mm"], MOVE_DELTA_MM)
                pc["moved_state"] = evaluate(m4, exp, shift=("root_clamp", MOVE_DELTA_MM))
                pc["set_restored"] = set_transform(sw, clamp, t0)
                rebuild(re_assy)
                m5, _ = measure(re_assy)
                pc["restored_state"] = evaluate(m5, exp)
                pc["ok"] = bool(pc["delta_ok"] and pc["moved_state"]["ok"] and pc["restored_state"]["ok"])
            RESULT["parameter_change"] = pc
            stage("parameter_change", pc.get("ok"), {k: pc.get(k) for k in ("delta_ok", "ok")})
            try:  # never save the moved-and-restored doc: the file on disk stays what was verified
                _get(sw, "CloseAllDocuments", True)
            except Exception:
                pass

        # --- verdict ------------------------------------------------------------------------------
        comps_ok = sum(1 for r in RESULT["components"].values() if r.get("inserted")) == len(COMPONENTS)
        checks = {
            "components_inserted": comps_ok,
            "mates_created": sum(1 for x in RESULT["mates"] if x.get("created")),
            "mates_attempted": len(RESULT["mates"]),
            "in_memory_ok": RESULT["in_memory"]["ok"],
            "reopened_ok": bool(RESULT.get("reopened") and RESULT["reopened"]["ok"]),
            "parameter_change_ok": bool(RESULT.get("parameter_change", {}).get("ok")),
            "files_written": RESULT["outputs"]["sldasm_bytes"] > 0 and RESULT["outputs"]["step_bytes"] > 0,
        }
        RESULT["checks"] = checks
        RESULT["host_checks_ok"] = all(v is True for k, v in checks.items() if k not in
                                       ("mates_created", "mates_attempted")) and (
            checks["mates_created"] == checks["mates_attempted"])
        RESULT["accepted"] = None
        RESULT["pending"] = ["step_roundtrip: run oracle_assembly.py --check-step on the retrieved STEP"]
        # Never "ok" from the host: acceptance also needs the independent STEP round trip.
        RESULT["status"] = "partial" if comps_ok else "error"
        RESULT["message"] = ("host read-back checks %s; STEP round trip not yet run, so the assembly is "
                             "NOT accepted" % ("passed" if RESULT["host_checks_ok"] else "FAILED (see checks)"))

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
