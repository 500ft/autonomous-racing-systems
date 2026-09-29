"""The CadQuery oracle must keep reproducing cad/solidworks/contract-assembly.v1.json.

SOLIDWORKS cannot run in CI, so the SOLIDWORKS half of the mast assembly is not
regenerated here. What CI can hold is the reference the authoring run is gated
against: if geometry.json or oracle.py drifts, the contract stops matching and
the gate silently weakens. That is the failure this guards.

It does not assert that any SOLIDWORKS part matches. That check lives in
cad/solidworks/author_mast_assembly.py and runs on the licensed host.
"""
from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
SOLIDWORKS_DIR = REPO / "cad" / "solidworks"
CONTRACT = SOLIDWORKS_DIR / "contract-assembly.v1.json"
GEOMETRY = SOLIDWORKS_DIR / "geometry.json"
ORACLE = SOLIDWORKS_DIR / "oracle.py"


class SolidworksAssemblyContract(unittest.TestCase):
    def setUp(self):
        self.contract = json.loads(CONTRACT.read_text())

    def test_contract_declares_every_modelled_part(self):
        self.assertEqual(
            sorted(self.contract["parts"]),
            ["mast_tube_stock", "root_clamp", "support_sleeve"],
        )

    def test_contract_is_not_the_frozen_specimen_contract(self):
        """mast_tube_stock is stock length; the specimen is the 100 mm free length."""
        specimen = json.loads((REPO / "cad" / "contract.json").read_text())
        stock = self.contract["parts"]["mast_tube_stock"]
        self.assertNotEqual(stock["volume_mm3"], specimen["expected"]["volume_mm3"])
        self.assertNotEqual(stock["bbox_mm"], specimen["expected"]["bbox_mm"])

    def test_every_blocked_parameter_names_its_acquisition_route(self):
        blocked = json.loads(GEOMETRY.read_text())["blocked_not_modelled"]
        self.assertTrue(blocked)
        for parameter, reason in blocked.items():
            self.assertTrue(
                any(route in reason for route in
                    ("measurement", "vendor_drawing", "design_then_inspect")),
                "%s does not name an acquisition route: %r" % (parameter, reason),
            )

    def test_oracle_reproduces_the_contract(self):
        """Regenerate the oracle and compare. Requires cadquery, as cad/generate.py does."""
        try:
            import cadquery  # noqa: F401
        except ImportError:
            self.skipTest("cadquery not installed")

        out = SOLIDWORKS_DIR / "oracle.regenerated.json"
        try:
            subprocess.run(
                [sys.executable, str(ORACLE), "--geometry", str(GEOMETRY), "--out", str(out)],
                check=True, capture_output=True,
            )
            regenerated = json.loads(out.read_text())["parts"]
        finally:
            out.unlink(missing_ok=True)

        tolerance = self.contract["tolerances"]["volume_mm3_rel"]
        for name, expected in self.contract["parts"].items():
            measured = regenerated[name]
            self.assertEqual(measured["n_solids"], expected["n_solids"], name)
            relative = abs(measured["volume_mm3"] - expected["volume_mm3"]) / expected["volume_mm3"]
            self.assertLessEqual(relative, tolerance, "%s volume drifted" % name)
            for axis, (got, want) in enumerate(zip(measured["bbox_mm"], expected["bbox_mm"])):
                self.assertAlmostEqual(got, want, places=6, msg="%s bbox axis %d" % (name, axis))

    def test_assembly_oracle_is_current_and_result_declares_its_status(self):
        """oracle_assembly.json must match a regeneration; the recorded run may not claim `ok`
        without accepted == True, and accepted needs every check plus the STEP round trip."""
        try:
            import cadquery  # noqa: F401
        except ImportError:
            self.skipTest("cadquery not installed")
        sys.path.insert(0, str(SOLIDWORKS_DIR))
        import oracle_assembly
        fresh = oracle_assembly.expected(json.loads(GEOMETRY.read_text()))
        committed = json.loads((SOLIDWORKS_DIR / "oracle_assembly.json").read_text())
        self.assertEqual(fresh["assembly"]["bbox_mm"], committed["assembly"]["bbox_mm"])
        self.assertAlmostEqual(fresh["assembly"]["total_volume_mm3"],
                               committed["assembly"]["total_volume_mm3"], places=6)
        res = json.loads((REPO / "runs" / "mast_assembly_20260929" / "assembly_result.json").read_text())
        self.assertIn(res["status"], ("ok", "partial", "error"))
        if res["status"] == "ok":
            self.assertIs(res["accepted"], True)
            self.assertTrue(res["host_checks_ok"] and res["step_roundtrip"]["ok"])
            # An accepted record may not still carry the pre-check "not yet run / NOT accepted" text.
            self.assertEqual(res["pending"], [])
            self.assertNotIn("NOT accepted", res["message"])


if __name__ == "__main__":
    unittest.main()
