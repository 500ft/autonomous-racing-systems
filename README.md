# Autonomous Racing Systems

Vehicle modelling, control and a LiDAR mast design for a 1/10-scale F1TENTH
race car. The vehicle software runs in simulation. The mast has gone from a
failed first design through FEA and CAD; building and load-testing it is the
step that remains.

[![CI](https://github.com/500ft/autonomous-racing-systems/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/500ft/autonomous-racing-systems/actions/workflows/ci.yml)
[![Docker](https://github.com/500ft/autonomous-racing-systems/actions/workflows/docker.yml/badge.svg?branch=main)](https://github.com/500ft/autonomous-racing-systems/actions/workflows/docker.yml)
[![Evidence: simulation and nominal CAD](https://img.shields.io/badge/evidence-simulation%20%2B%20nominal%20CAD-465B70)](#results)
[![License: MIT](https://img.shields.io/badge/license-MIT-276C6B)](LICENSE)

[Results](#results) · [Roadmap](ROADMAP.md) · [Quick start](#quick-start) ·
[Full report](reports/final_report.md) · [Contributing](CONTRIBUTING.md)

![Illustration of a sensor-equipped autonomous race car on a test track](docs/media/hero.jpg)

*Concept illustration (AI-generated). It is not the project car or its CAD.*

## What's in the repository

**Vehicle software.** A dynamic bicycle model is fitted to telemetry from the
F1TENTH Gym simulator and checked on a held-out segment. Pure pursuit, LQR and
MPC controllers and an EKF are compared under the same scenarios, and a ROS 2
bridge converts recorded bags into the same telemetry format the simulator
writes.

**LiDAR mast.** The mast holds the LiDAR above the car, and its first bending
mode has to stay above 200 Hz: twice the 100 Hz control rate, clear of motor
vibration. The first design, a 120 mm tube with a 16 mm outside diameter,
reached 174.7 Hz by hand calculation and failed. The redesign is shorter and
wider: 100 mm long, 20 mm OD, 1.5 mm wall, 6061-T6. It gives 330.1 Hz by hand
and 285.5 Hz in FEA, with less than 1.5% change across three meshes.

A later study looked at why the FEA came out 13.5% below the hand calculation.
Most of the difference was how the model attached the tip mass: the original
FEA input file hung it from a single node on the tube wall. Coupling it to the tip face
at the centre gives 320.9 Hz, 2.8% from the hand value. That model has not been
re-converged yet, so 285.5 Hz is still the reported number.

The tube, support sleeve and root clamp are parametric SOLIDWORKS parts. The
assembly was built unattended on the CAD host and checked against a separate
CadQuery model: part placement, volumes, a move-and-restore test and a STEP
round trip all match.

## Results

| Result | Value | Source |
| --- | --- | --- |
| Mast first mode, original design (hand) | 174.7 Hz, below the 200 Hz limit | [Mechanical analysis](docs/design/16_mechanical_design_analysis.md) |
| Mast first mode, redesign (hand) | 330.1 Hz | same |
| Mast first mode, redesign (FEA) | 285.5 Hz, < 1.5% change over three meshes | [FEA output](runs/mast_fea/fea_summary.txt) |
| Tip-mass attachment study | 285.5 Hz → 320.9 Hz with a coupled, centred mass | [Study record](runs/mast_modal_attachment_20260925/study.json) |
| MPC solve time | 1.33 ms at the 95th percentile, inside the 10 ms control period | [MPC report](reports/mpc_controller.md) |
| Controller comparison | Lap completion, cross-track error and steering effort for each controller | [Comparison](reports/controller_comparison.md) |
| Model identification | Held-out yaw-rate error at numerical precision (see below) | [Identification study](reports/dynamic_parameter_identification.md) |

![Identified bicycle-model yaw-rate and slip-angle predictions against simulator telemetry, with the held-out segment marked](reports/figures/dynamic_parameter_fit.png)

*Identified model against simulator telemetry; the segment right of the dashed
line is held out. The simulator generates its data with the same model being
fitted, so the near-zero error shows the fitting code works. It says nothing
about how well the model matches a real car.
[Figure inputs and generator](docs/data-and-figures.md).*

## Quick start

This path uses the portable report environment and Python 3.10, the same as
CI. It does not launch ROS or rerun the full simulation study.

```bash
git clone https://github.com/500ft/autonomous-racing-systems.git
cd autonomous-racing-systems
python3.10 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-item11-regression.txt
python -m pip install -r requirements-report.txt
PYTHONPATH=gym python experiments/test_cad_inputs.py
PYTHONPATH=gym python experiments/test_final_report.py
```

Both commands should finish with `OK`. They check the design inputs and the
report, including a temporary PDF build.

The [reproduction guide](docs/START_HERE.md#reproduce-by-environment) covers
the full checks, the legacy Gym experiments, ROS 2 and the pinned CadQuery
environment. Keep those environments separate; their dependency versions
differ on purpose.

## What's next

Build the mast and load-test it. The [roadmap](ROADMAP.md) has the steps; the
first is confirming the test hardware (load cell, 0.001 mm dial indicators,
bench). The [test protocol](docs/specs/mast-physical-validation/design.md) is
frozen: five loads on each axis, at least three load/unload cycles, and root
motion measured so it can be subtracted.

## Limits

- Nothing has been built or measured. The mast results are hand calculations,
  FEA and nominal CAD, and the material properties are handbook values for
  6061-T6.
- All vehicle results come from the simulator, not a physical car.
- The ±15% agreement band in the test protocol applies to static stiffness. It
  is not a pass criterion for a tap test.

## Documentation

| Document | What it covers |
| --- | --- |
| [Reading and reproduction guide](docs/START_HERE.md) | Where to start, and how to rerun each part |
| [Integrated report](reports/final_report.md) | Modelling, controls, estimation and mast results in one place |
| [Data and figures](docs/data-and-figures.md) | Inputs and generator for each figure |
| [Vehicle model](docs/vehicle_model.md) | Equations and assumptions |
| [Telemetry dictionary](docs/telemetry_data_dictionary.md) | The shared data format |
| [Parameter inventory](docs/parameter_inventory.md) | Which inputs are configured, identified or measured |
| [Fixture preparation](cad/roboracer/fixture-preparation.md) | Mast interface and metrology decisions |
| [CAD inventory](docs/CAD_ITEMS.md) | Planned parts and what exists |
| [Literature](literature/README.md) | Sources checked against the project's claims, starting from the [claim ledger](literature/claim-ledger.md) |

```text
gym/          F1TENTH simulator package and dynamics
experiments/  replay, identification, control, telemetry and mast checks
reports/      engineering reports and figures
runs/         study inputs, metrics and solver summaries
ros2_ws/      f1tenth_modeling ROS 2 package
cad/          parametric geometry and its tests
evidence/     check records and regression captures
docs/         models, interfaces, test protocols and guides
```

## Contributing

Read [CONTRIBUTING.md](CONTRIBUTING.md) before changing models, evidence or
generated outputs. A useful pull request says which result it affects, which
environment it ran in, and which checks passed. Open an
[issue](https://github.com/500ft/autonomous-racing-systems/issues) for a
reproducible bug or a scoped proposal.

## License and attribution

[MIT License](LICENSE), keeping the original simulator copyright notice. The
[upstream source register](docs/upstream_roboracer_sources.md) lists the
reference repositories, their licenses and pinned revisions. When citing,
give the repository revision and the report or dataset used. The project was
previously named RoboRacer; package and ROS interface names were not changed
([identity note](docs/REPOSITORY_IDENTITY.md)).
