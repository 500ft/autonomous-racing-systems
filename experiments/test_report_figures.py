#!/usr/bin/env python3
"""Redraw every report figure from committed run outputs into a scratch directory.

Checks that each figure renders, has no overlapping or clipped text, and is
written at the shared resolution. Committed figures and run files are not touched.

Run: PYTHONPATH=gym MPLBACKEND=Agg python experiments/test_report_figures.py
"""
import tempfile
import unittest
from pathlib import Path

from PIL import Image

import figure_style as fs
import plot_integrator_comparison
import report_figures as rf


class ReportFigureTest(unittest.TestCase):
    def test_redraw_from_committed_outputs(self) -> None:
        problems, written = {}, []
        original = fs.save

        def checked(fig, path, formats=("png",)):
            found = fs.layout_problems(fig)
            if found:
                problems[Path(path).name] = found
            paths = original(fig, path, formats)
            written.extend(paths)
            return paths

        fs.save = checked
        try:
            with tempfile.TemporaryDirectory() as tmp:
                out = Path(tmp)
                for name in ("COMBINED_PATH", "TRAJECTORY_PATH", "TRACKING_ERROR_PATH", "SUMMARY_METRICS_PATH"):
                    setattr(plot_integrator_comparison, name, out / getattr(plot_integrator_comparison, name).name)
                plot_integrator_comparison.main()
                rf.draw_integrator_convergence(figure_dir=out)
                rf.draw_dynamic_replay(figure_dir=out)
                rf.draw_kinematic_replay(figure_dir=out)
                rf.draw_sysid_excitation(figure_dir=out)
                rf.draw_parameter_fit(rf.RUNS / "dynamic_parameter_identification",
                                      out / "dynamic_parameter_fit.png", out / "dynamic_parameter_residuals.png")
                rf.draw_pure_pursuit(figure_dir=out)
                rf.draw_ekf(figure_dir=out)
                rf.draw_fmea(figure_dir=out)
                rf.draw_parameter_id_robustness(figure_dir=out)
                rf.draw_item11(figure_dir=out / "item11")
                committed = {p.name for p in (rf.FIGURES.glob("*.png"))} | {
                    p.name for p in (rf.ITEM11 / "figures").glob("*.png")}
                names = {p.name for p in written}
                self.assertEqual(len(written), 29)
                self.assertLessEqual(names, committed, "redraw wrote a figure name that is not committed")
                for path in written:
                    dpi = Image.open(path).info.get("dpi", (0, 0))[0]
                    self.assertAlmostEqual(dpi, fs.DPI, delta=0.5, msg=path.name)
        finally:
            fs.save = original
        self.assertEqual(problems, {})


if __name__ == "__main__":
    unittest.main()
