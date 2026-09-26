#!/usr/bin/env python3
"""Drivetrain excitation orders versus the mast's first bending mode (audit finding F1).

    python3 experiments/drivetrain_excitation.py

Every input is read from a number already derived in docs/design/14_chassis_drivetrain_actuators.md or
docs/design/16_mechanical_design_analysis.md. Nothing here is a new measurement or a new assumption, and
nothing here establishes that the mast has a vibration problem: it establishes only that the 200 Hz
modal guard's stated basis -- "a plausible low-hundreds-Hz motor band", cleared by 2x -- is not the band
this drivetrain actually produces.

Orders that CANNOT be computed yet are returned as None with the missing input named, rather than
guessed: commutation order needs the pole count, gear mesh needs tooth counts.
"""
from __future__ import annotations

import json, sys

# --- inputs, all with provenance --------------------------------------------------------------------
MOTOR_RPM_AT_10MS = 20600.0   # calculated result, 14_chassis §2 (1744 rpm wheel x 11.82 reduction)
MOTOR_RPM_NO_LOAD = 38850.0   # calculated result, 14_chassis §2 (3500 kV x 11.1 V nominal)
WHEEL_RPM_AT_10MS = 1744.0    # calculated result, 14_chassis §2
TOP_SPEED_MS = 10.0           # requirement, the speed the drivetrain table is derived at
MAST_F1_FEA_HZ = 285.5        # calculated result, runs/mast_fea/fea_summary.txt (historical model)
MAST_F1_HAND_HZ = 330.1       # calculated result, runs/mast_hand_calc/design_sweep.txt
GUARD_HZ = 200.0              # selected value, 16_mechanical §3.1 -- the criterion under audit
CONTROL_RATE_HZ = 100.0       # requirement, controller update rate

MISSING = {
    "motor_pole_pairs": "needed for commutation-order frequency; not recorded in the repository",
    "gear_tooth_counts": "needed for gear-mesh frequency; spur/pinion counts not recorded",
    "rotor_unbalance_class": "needed to know whether first order carries energy; not recorded",
    "motor_to_deck_transmission": "needed to relate motor vibration to mast-base input; measurement only",
}


def orders(speed_ms: float) -> dict:
    """First-order rotational frequencies at a given road speed. Linear in speed."""
    frac = speed_ms / TOP_SPEED_MS
    return {
        "road_speed_m_s": speed_ms,
        "motor_shaft_hz": MOTOR_RPM_AT_10MS * frac / 60.0,
        "wheel_hz": WHEEL_RPM_AT_10MS * frac / 60.0,
        "commutation_hz": None,     # = motor_shaft_hz * pole_pairs, pole count unknown
        "gear_mesh_hz": None,       # = motor_shaft_hz * pinion_teeth, counts unknown
    }


def crossing_speed(target_hz: float) -> float:
    """Road speed at which first-order motor shaft frequency equals target_hz."""
    return TOP_SPEED_MS * target_hz / (MOTOR_RPM_AT_10MS / 60.0)


def report() -> dict:
    at_top = orders(TOP_SPEED_MS)
    return dict(
        label="AUDIT CALCULATION: derived from numbers already in the repository. Not a measurement, "
              "and not a claim that the mast has a vibration problem.",
        inputs=dict(motor_rpm_at_10ms=MOTOR_RPM_AT_10MS, motor_rpm_no_load=MOTOR_RPM_NO_LOAD,
                    wheel_rpm_at_10ms=WHEEL_RPM_AT_10MS, mast_f1_fea_hz=MAST_F1_FEA_HZ,
                    mast_f1_hand_hz=MAST_F1_HAND_HZ, guard_hz=GUARD_HZ,
                    control_rate_hz=CONTROL_RATE_HZ),
        at_top_speed=at_top,
        motor_shaft_no_load_hz=MOTOR_RPM_NO_LOAD / 60.0,
        crossings=dict(
            guard_crossed_at_m_s=crossing_speed(GUARD_HZ),
            fea_mode_crossed_at_m_s=crossing_speed(MAST_F1_FEA_HZ),
            hand_mode_crossed_at_m_s=crossing_speed(MAST_F1_HAND_HZ),
        ),
        ratios=dict(shaft_at_top_over_fea_mode=at_top["motor_shaft_hz"] / MAST_F1_FEA_HZ,
                    fea_mode_over_control_rate=MAST_F1_FEA_HZ / CONTROL_RATE_HZ,
                    fea_mode_over_guard=MAST_F1_FEA_HZ / GUARD_HZ),
        finding=("First-order motor shaft excitation reaches the mast's FEA first mode inside the "
                 "operating speed range, and exceeds it at top speed. The guard was justified as "
                 "clearing a motor band UPWARD by 2x; these numbers put first order ABOVE the mode, so "
                 "the shaft order sweeps up through the resonance during acceleration."),
        not_established=("Whether that sweep matters. It depends on rotor unbalance, the motor-to-deck "
                         "transmission path and damping, none of which is recorded. A swept resonance "
                         "with low unbalance may be harmless."),
        missing_inputs=MISSING,
    )


def main() -> int:
    r = report()
    print(json.dumps(r, indent=1))
    c = r["crossings"]
    print(f"\nshaft at top speed {r['at_top_speed']['motor_shaft_hz']:.1f} Hz "
          f"= {r['ratios']['shaft_at_top_over_fea_mode']:.2f}x the {MAST_F1_FEA_HZ} Hz FEA mode",
          file=sys.stderr)
    print(f"guard crossed at {c['guard_crossed_at_m_s']:.2f} m/s; "
          f"FEA mode crossed at {c['fea_mode_crossed_at_m_s']:.2f} m/s "
          f"(operating envelope is {TOP_SPEED_MS:.0f} m/s)", file=sys.stderr)
    print(f"{len(MISSING)} inputs missing before this can become an excitation assessment", file=sys.stderr)
    return 0


def _self_check() -> None:
    """One runnable check: the arithmetic and the ordering that the finding depends on."""
    r = report()
    assert abs(r["at_top_speed"]["motor_shaft_hz"] - 343.333) < 0.01
    assert abs(r["motor_shaft_no_load_hz"] - 647.5) < 0.01
    assert abs(r["at_top_speed"]["wheel_hz"] - 29.067) < 0.01
    # the finding: first order exceeds the mode at top speed, and crosses it inside the envelope
    assert r["at_top_speed"]["motor_shaft_hz"] > MAST_F1_FEA_HZ
    assert 0.0 < r["crossings"]["fea_mode_crossed_at_m_s"] < TOP_SPEED_MS
    assert abs(r["crossings"]["fea_mode_crossed_at_m_s"] - 8.316) < 0.01
    assert abs(r["crossings"]["guard_crossed_at_m_s"] - 5.825) < 0.01
    # orders that need an unavailable input must stay None, never a guess
    assert r["at_top_speed"]["commutation_hz"] is None
    assert r["at_top_speed"]["gear_mesh_hz"] is None
    # linearity in speed
    assert abs(orders(5.0)["motor_shaft_hz"] * 2 - orders(10.0)["motor_shaft_hz"]) < 1e-9
    print("self-check OK")


if __name__ == "__main__":
    if "--self-check" in sys.argv:
        _self_check()
    else:
        sys.exit(main())
