# Open questions and scope decisions

This record accompanies the [executed qualification](../reports/ope_qualification.md).
The [roadmap](../ROADMAP.md) is the only plan.

## Current software scope

The owner adopted the dependency roadmap and authorized removal of obsolete
active implementation, work orders and presentation assets. The active method
question concerns dispersion of paired controller-performance differences and
calibrated abstention, including near ties. This authorization supplies no data
rights or permission to execute the future research milestones. The
confidence-gate baseline, registered prediction and scope limit added on
2026-10-09 are in [roadmap M3](../ROADMAP.md#m3-calibrate-a-controller-difference-abstention-rule).

Dataset qualification and owner-approved platform access are parallel possible
routes. Failure of one source requires a route decision, rather than a claim that
all legitimate routes are closed. The [history index](history/README.md) records
what was removed and why useful historical work remains.

| Question | Status | Evidence or action needed |
| --- | --- | --- |
| Data and code reuse rights | Code answered 2026-10-09; data zips open | MIT added 2026-10-09 on the benchmark, f1tenth_orl_dataset, f110_ope_methods and the agents' ope-benchmark branch; legacy f110_datasets archived under CC-BY-4.0. The v2 data zips on Google Drive carry no licence text of their own, so their licence and redistribution of derived subsets stay open. The author asks that the thesis be cited. See the [contact record](ope_author_request.txt) |
| Recording segment versus episode | Answered 2026-10-09, not yet applied here | `done` is on-car crash detection plus manual intervention; `compute_termination` is `done` plus an offline lidar/pose crash check with rows after the first crash filtered. Horizon 250 steps, `set_terminals=True`, gym.make call from experiments/run_iw.py. One car, one configuration, a few days, no session IDs; sim-stoch-v2 produced from the recorded real start poses with no explicit pairing IDs |
| Policy correspondence and execution | Answered 2026-10-09, execution still unqualified here | 15 evaluation agents, 4 stochastic follow-the-gap and 11 parametrised pure pursuit, no neural policies; loadable by name from agent_configs/ (69 configs) via `Agent().load(name=...)`. Actions are deltas with truncated-normal noise. Batched pure-pursuit lookahead bug fixed at c42146c; it affected OPE estimates only. Ground truth per agent for four rewards in Groundtruth/gt_reward_*.json |
| Loader aliases | Confirmed as a bug; fixed upstream 2026-10-09 | All v2 names resolved to f110-sim-v1.zip at 66d0363; fixed at loader 536d762. Only f110-real-stoch-v2 and f110-sim-stoch-v2 remain; v0 and v1 are legacy |
| FQE and probability-ratio methods | Ineligible for empirical execution now; log_prob semantics answered 2026-10-09 | log_probs are per dimension [speed, steering]; the joint is the sum. Open: whether log_probs in the new sim archive are populated (the old archive had zeros). Separate [estimator gates](../reports/ope_qualification.md#estimator-gates) still apply; no missing probabilities supplied |
| External author contact | Reply received 2026-10-09 | [Summary in the contact record](ope_author_request.txt). Still open: f110_sim_env (in .gitmodules, no tree entry, no public repo), data-zip licence, sim log_probs |
| Structural qualification pins | Stale since 2026-10-09 | See the qualification pins note below |
| Reviewer, physical study, publication and campaign | Not approved | Named reviewer, qualified protocol and separate owner authorization are still required |

## Qualification pins

Note added 2026-10-09. Qualification in reports/ope_qualification.md was run
at loader 66d0363 and agents 44ed59d. It must be re-run at loader 536d762,
agents c42146c, gym 886dde0 before any analysis. Not yet re-run.

## Superseded active questions, with decisions retained

| Earlier question | Disposition |
| --- | --- |
| Held-out command response and transfer to the owner's vehicle | Superseded as the active finish line by this software scope. [Development result](../reports/real_command_response.md) and [split blocker](../reports/driving_split_qualification.md) remain intact. K2 closure-or-wait remains unanswered; no final bags opened. |
| Fleet study | K1 adoption and K3 actual access remain unanswered. This pivot does not approve fleet work or establish vehicles. |
| Mast mounting, deck height and D2 study scope | Separately pending physical decision. Keep the delegated low-mount assessment provisional. No approved height, deck, fabrication, modal requirement or new frequency threshold. |
| Static stiffness as vibration evidence | Superseded as a sufficient modal/racing finish line. The [optional static protocol](specs/mast-physical-validation/design.md) remains historical preparation. |
| Funding, physical inventory, naming | No new decisions supplied. No purchase, successor repository or campaign created. |

Superseded means removed from the active software question, not answered or
approved. The [history index](history/README.md) retains the supporting work.
