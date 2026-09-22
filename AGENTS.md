# Autonomous Racing Systems

## Working scope

- In this user's workflow, Codex prepares plans and detailed `.txt` handoffs;
  Claude implements them. Keep Codex work to planning unless the user explicitly
  changes that scope.
- The current handoff is [the September 19–25 plan](docs/WEEK_PLAN_2026-09-19_TO_25.txt).
  Inspect current branches and evidence before planning work that may already exist.

## CAD and FEA context

- Read `500ft/engineering-audit → docs/cad_agent_briefing.md` before CAD/FEA
  planning. Read that repo's `docs/host_setup.md` for host work and
  `docs/solidworks_api_findings.md` before proposing COM changes.
- [Shared CAD workflow decision](docs/decisions/0001-shared-cad-workflow.md)
  records the reviewed source revision, repo ownership, branch context and
  project consequences. Refresh the references when they change.
- Reusable host/CAD/FEA machinery belongs in `engineering-audit`; RoboRacer
  geometry, contracts and project evidence belong here.
- Preserve `cad/generate.py` and `cad/contract.json` for the frozen 100 mm
  analysis specimen. Native assembly-part work uses `cad/solidworks/` and its
  separate contract. A directory name does not establish an assembly document.
- Acceptance needs independent geometry checks, a parameter-change test and
  export round-trip evidence. A clean rebuild or solver exit alone does not
  establish correctness. CI oracle checks do not establish host runs.
- Respect parameter acquisition routes. Keep provisional design choices separate
  from measured inputs. Instrument purchases do not establish calibration or
  physical campaign readiness.

## Planning context recorded 2026-09-21

- Equipment-specific force logging/calibration preparation remains the weekly
  priority; displacement/root-motion and fixture evidence remain gaps.
- Native tube-stock, support-sleeve and clamp work was found on
  `cad/solidworks-mast-assembly`; equipment intake on `week/day1-20260919`.
  Inspect these branches before duplicating work or assuming it is on main.
- Assembly mates, fully driven feature positions, drawings and independent FEA
  checks are the next CAD/FEA questions. They do not displace the core acquisition
  work or automatically close existing physical gates.
