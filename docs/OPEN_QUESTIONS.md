# Open questions and scope decisions

This record accompanies the [executed qualification](../reports/ope_qualification.md).
The [roadmap](../ROADMAP.md) is the only plan.

## Current software scope

The owner's existing-session instruction on 2026-10-06 adopts model-disagreement
and ranking-refusal qualification and authorizes implementation plus a result PR.
It supersedes the former documentation-only and planning-only roles for this
task. It does not approve a full empirical OPE study.

| Question | Status | Evidence or action needed |
| --- | --- | --- |
| Data and code reuse rights | Unknown | Explicit grant for each archive, policy code and weights; see the [unsent request](ope_author_request.txt) |
| Recording segment versus episode | Unresolved | Meaning of continuing `done` flags, collision/reset handling, truncation, raw-to-filtered mapping and independent acquisition groups |
| Policy correspondence and execution | Partly qualified | Exact filename matches are recorded in [result.json](../runs/ope_qualification/result.json); target implementations, preprocessing, action transforms and history/reset behavior remain unqualified |
| Loader aliases | Reproduced; intended mapping unknown | Author confirmation before any analysis using an environment name |
| FQE and probability-ratio methods | Ineligible for empirical execution now | Separate [estimator gates](../reports/ope_qualification.md#estimator-gates); no missing probabilities supplied |
| External author contact | Not authorized | Draft is unsent; owner may provide answers or authorize sending |
| Publication and campaign | Not approved | This task ends with the qualification PR and receipt |

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
