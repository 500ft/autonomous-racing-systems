# Start here — Autonomous Racing Systems

The [README](../README.md) is the overview and the [roadmap](../ROADMAP.md) is
the plan. This guide is for reading the work quickly or rerunning part of it.

## Reading paths

| If you have | Read |
| --- | --- |
| Two minutes | [README results](../README.md#results), then the [integrated report](../reports/final_report.md) |
| Half an hour | The [mechanical design analysis](design/16_mechanical_design_analysis.md), then the [test protocol](specs/mast-physical-validation/design.md) |
| A review to do | The [review index](REVIEW_READY.md), then one figure traced through [data and figures](data-and-figures.md) to its inputs |
| A change to make | [CONTRIBUTING.md](../CONTRIBUTING.md), then the environment below that the change touches |

## The two halves of the project

**Public driving data.** The [development comparison](../reports/real_command_response.md)
fits and scores one licensed public run. The [split qualification](../reports/driving_split_qualification.md)
stopped before additional bag access because session and segment membership
are undocumented. Unopened runs remain unassigned. See the roadmap for K2,
D2 and the unapproved fleet proposal.

**Simulation software.** The identification study fits the same model the
simulator uses, so its held-out error checks simulator/fitter consistency.
See the [identification study](../reports/dynamic_parameter_identification.md),
[controller comparison](../reports/controller_comparison.md) and
[EKF study](../reports/ekf_study.md).

**LiDAR mast.** The original result is a [hand calculation](../runs/mast_hand_calc/summary.txt).
The redesign has a [hand sweep](../runs/mast_hand_calc/design_sweep.txt),
[historical FEA](../runs/mast_fea/fea_summary.txt) and an
[unconverged attachment comparison](../runs/mast_modal_attachment_20260925/study.json).
The [shaft-order crossing assessment](design/16_mechanical_design_analysis.md#61-retrospective-assessment--is-the-200-hz-guard-the-right-criterion-audit-f1)
withdraws the motor-clearance rationale. No measured assembly response exists.
The [static protocol](specs/mast-physical-validation/design.md) is optional and
cannot establish modal performance. Mounting need and scope come first.

[Data and figures](data-and-figures.md) and the
[figure manifest](figure-manifest.json) link every plot to its generator and
inputs.

## Reproduce by environment

Run commands from the repository root. Keep the environments separate;
their dependency versions differ on purpose.

### Portable checks — Python 3.10

Set up as in the [README](../README.md#quick-start), then run the checks
from the [CI workflow](../.github/workflows/ci.yml):

```bash
PYTHONPATH=gym python experiments/test_rosbag_to_telemetry.py
PYTHONPATH=gym python experiments/test_bag_evidence.py
PYTHONPATH=gym python experiments/validate_item11.py
PYTHONPATH=gym python experiments/test_mast_physical_validation.py
PYTHONPATH=gym python experiments/test_cad_inputs.py
PYTHONPATH=gym python experiments/test_final_report.py
```

Each should exit 0. They need no ROS install, vehicle or test rig.

### Public data

Use the isolated environment and reproduction command in the
[development report](../reports/real_command_response.md#reproduce).
The [metadata census](../reports/driving_split_qualification.md#reproduce-the-metadata-census)
uses only its committed metadata snapshot.

### CAD — pinned CadQuery environment

The [CAD workflow](../.github/workflows/cad-geometry.yml) uses the package
pins in [cad/requirements.lock](../cad/requirements.lock). They pin direct
packages only, not the full dependency tree. With Conda:

```bash
conda create -n racing-cad -c conda-forge --strict-channel-priority --file cad/requirements.lock
conda activate racing-cad
python cad/input_requests.py --check
python cad/generate.py --parameters cad/roboracer/parameters.csv --output /tmp/racing-cad-review
python -m pytest cad/tests -q
```

The generator writes `mast_tube.step` and `geometry.json`, and the tests
compare them with the [geometry contract](../cad/contract.json). If pytest
crashes while importing `readline` on your machine, this works around it:

```bash
python -c 'import sys,types; sys.modules["readline"]=types.ModuleType("readline"); import pytest; raise SystemExit(pytest.main(["cad/tests","-q"]))'
```

### Legacy simulation — Python 3.9

The [Gym environment](../environment.yml) keeps the older simulator stack.
Regenerate results in a separate checkout so they aren't mixed with other
edits.

```bash
conda env create -f environment.yml
conda activate f1tenth-gym
python -m pip install -e .
./run_all.sh
```

The long MPC and robustness sweeps are opt-in:

```bash
RUN_FULL_MPC=1 RUN_ROBUSTNESS=1 ./run_all.sh
```

[Data and figures](data-and-figures.md) gives single-study commands. GUI
rendering needs OpenGL.

### ROS 2

Follow the [Ubuntu Humble](ros2_verification_ubuntu_humble.md) or
[RoboStack macOS](ros2_verification_robostack_macos.md) setup first. The
package is [`f1tenth_modeling`](../ros2_ws/src/f1tenth_modeling), and the
[telemetry dictionary](telemetry_data_dictionary.md) defines its data format.

```bash
cd ros2_ws
colcon build --symlink-install
source install/setup.bash
```

Don't launch excitation against a physical vehicle as a first test; choose the
simulator or hardware context on purpose.

## Before reusing or citing

Read the [upstream source register](upstream_roboracer_sources.md), the
[license](../LICENSE) and [CONTRIBUTING.md](../CONTRIBUTING.md). Give the
source commit in any review or citation. Task status is in the
[CAD task ledger](CAD_TASKS.csv); the September 11
[completion correction](COMPLETION_RECONCILIATION.md) explains which early
deliverables were preparation rather than finished work.
