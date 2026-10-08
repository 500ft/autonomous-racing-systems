# Sim-to-Real Controller Ranking

Can dispersion in the predicted performance difference between controllers,
across physically justified models consistent with development data, identify
rankings that should be withheld? The current result is
a reproducible qualification of public F110 archives. Policy ranking remains
blocked by unresolved reuse terms, episode meaning and policy executability.

[![CI](https://github.com/500ft/sim-to-real-controller-ranking/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/500ft/sim-to-real-controller-ranking/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-276C6B)](LICENSE)

[Results](#results) · [Roadmap](ROADMAP.md) · [Quick start](#quick-start) ·
[Qualification report](reports/ope_qualification.md) · [History](docs/history/README.md)

![Recording-segment and policy-name counts from the five pinned F110 archives](runs/ope_qualification/structure.png)

*Unfiltered structural counts from [result.json](runs/ope_qualification/result.json).
Segments are not verified independent experiments. No return or ranking is plotted.*

## Results

- Real v1 contains 311 recording segments and 29 distinct policy-name strings.
  Its 10,813 `done | truncated` rows cannot be treated as separate recordings.
- Real stochastic v2 contains 1,375 segments and 57 policy-name strings. All
  those names match configuration filenames in the pinned benchmark source;
  actual policy execution remains unqualified.
- Both real-stochastic environment registrations load the simulation-v1
  archive. The qualification script binds each archive by explicit filename,
  hash and internal array root.

The [executed table](runs/ope_qualification/structure.md) and
[qualification report](reports/ope_qualification.md) give the source pins,
method, policy-name discrepancies and separate gates for FQE and probability-ratio
estimators. [result.json](runs/ope_qualification/result.json) is the source for
structural numbers; the table and plot are generated views.

## Quick start

The structural reader uses Python 3.11 in its own environment. Unit checks need
no archive download, upstream policy package or vehicle:

```bash
python3.11 -m venv .venv-ope
source .venv-ope/bin/activate
python -m pip install -r requirements-ope-qualification.txt
python experiments/test_ope_qualification.py
```

The optional integration test is skipped unless the pinned cache is supplied.
See [reproduction](reports/ope_qualification.md#reproduce) for the executed
archive check and figure commands. Source data and third-party code are kept
outside this repository while reuse terms remain unknown.

## What's next

Obtain explicit reuse terms and authoritative episode/policy mapping. An
[author request](docs/ope_author_request.txt) is drafted and unsent. The owner
has adopted the [dependency roadmap](ROADMAP.md) and repository cleanup;
[open questions](docs/OPEN_QUESTIONS.md) retain external-contact and physical
decisions. Dataset access and owner-approved platform access are parallel
possible routes. A refusal from one source does not close every route. No empirical OPE or
finite-horizon return calculation has been run.

## Retained work

The licensed [public-driving comparison](reports/real_command_response.md)
remains a same-run development result. Its
[split qualification](reports/driving_split_qualification.md) admitted no
separate final group. Unopened bags stay unopened.

The [history index](docs/history/README.md) retains simulator identification,
controller comparisons, mast hand calculations, FEA, useful CAD and calibration
tooling. Same-model simulator consistency does not validate real controller
rankings. Mast mounting and physical scope remain pending; this software pivot
approves no deck design, height, fabrication or physical campaign.

## Documentation

| Document | Purpose |
| --- | --- |
| [Roadmap](ROADMAP.md) | Finish line and current stop condition |
| [Qualification report](reports/ope_qualification.md) | Executed structural result and estimator gates |
| [Open questions](docs/OPEN_QUESTIONS.md) | Current unknowns and superseded questions |
| [Reading and reproduction guide](docs/START_HERE.md) | Environments and retained checks |
| [Data and figures](docs/data-and-figures.md) | Current and historical figure provenance |
| [History](docs/history/README.md) | Preserved driving, simulation and mechanical work |

## Contributing

Read [CONTRIBUTING.md](CONTRIBUTING.md) and [AGENTS.md](AGENTS.md). A pull request
must identify the result it changes and the checks actually run.

## License and attribution

Repository code uses the [MIT License](LICENSE), preserving upstream simulator
attribution. This grants no rights to the separately inspected F110 archives or
policy code. Their reuse terms remain unknown. The earlier public-driving bag
has its own [CC BY 4.0 source record](runs/real_command_response/source.json).
See the [source register](docs/upstream_roboracer_sources.md) and
[identity note](docs/REPOSITORY_IDENTITY.md) for the retained project history.
