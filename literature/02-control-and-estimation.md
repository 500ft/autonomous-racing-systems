# 2. Path-tracking control and state estimation

Scope: the pure pursuit / LQR / MPC comparison, the EKF study, the FMEA, and the planned
mismatched-plant sweep. Grading scheme: [README](README.md). Items already listed in
[§1](01-vehicle-dynamics-and-system-id.md) are cross-referenced, not repeated.

> **Read this section's "challenge" entry first.** The repo's headline is that tuned pure pursuit
> achieved the lowest RMS cross-track error, below LQR and MPC. No verified publication reports that
> result in the same direction, and one reports the opposite on real hardware. That does not make the
> result wrong; it makes it a finding that has to be defended, scoped and re-tested.

## Geometric path tracking

| Citation | Link | Why it matters here | Ab | Ev |
|---|---|---|---|---|
| Coulter, R. C. (1992). *Implementation of the Pure Pursuit Path Tracking Algorithm.* CMU-RI-TR-92-01. | <https://publications.ri.cmu.edu/implementation-of-the-pure-pursuit-path-tracking-algorithm/> | Canonical source for the baseline controller and for the point that behaviour is dominated by lookahead. Legitimises the lookahead / velocity-gain sweep as the correct way to tune it. | 3 | D |
| Thrun, S.; Montemerlo, M.; Dahlkamp, H.; et al. (2006). *Stanley: the robot that won the DARPA Grand Challenge.* J. Field Robotics 23(9), 661–692. | [10.1002/rob.20147](https://doi.org/10.1002/rob.20147) | System-level evidence that a low-complexity steering law won a real high-speed competition. Supports the framing that a geometric baseline is not a strawman. | 2 | A |
| **Hoffmann, G. M.; Tomlin, C. J.; Montemerlo, M.; Thrun, S. (2007). *Autonomous automobile trajectory tracking for off-road driving: controller design, experimental validation and racing.* ACC, 2296–2301.** | [10.1109/ACC.2007.4282788](https://doi.org/10.1109/ACC.2007.4282788) | The actual Stanley control law with experimental validation. **The missing third geometric baseline in this repo's comparison** — its front-axle error formulation is a direct competitor to pure pursuit. | 3 | A |
| Snider, J. M. (2009). *Automatic Steering Methods for Autonomous Automobile Path Tracking.* CMU-RI-TR-09-08. | <https://publications.ri.cmu.edu/automatic-steering-methods-for-autonomous-automobile-path-tracking/> | Directly comparable prior work: derives, tunes and compares geometric and model-based laws on one platform and concludes **no method dominates everywhere**. This repo's result is consistent with that literature, not contrary to it. | 3 | C |
| Paden, B.; Čáp, M.; Yong, S. Z.; Yershov, D.; Frazzoli, E. (2016). *A survey of motion planning and control techniques for self-driving urban vehicles.* IEEE T-IV 1(1), 33–55. | [10.1109/TIV.2016.2578706](https://doi.org/10.1109/TIV.2016.2578706) | Taxonomy placing pure pursuit, Stanley, LQR and MPC in one framework. Scaffolding only; not an empirical claim. | 2 | D |
| Artuñedo, A.; Moreno-Gonzalez, M.; Villagra, J. (2024). *Lateral control for autonomous vehicles: a comparative evaluation.* Annual Reviews in Control 57, 100910. | [10.1016/j.arcontrol.2023.100910](https://doi.org/10.1016/j.arcontrol.2023.100910) | Closest methodological model: a systematic tuning protocol plus stability and comfort metrics, compared in simulation **and** on an instrumented vehicle. Template for defending same-track, same-seed fairness. | 3 | A |

## The challenge to this repo's headline

| Citation | Link | Why it matters here | Ab | Ev |
|---|---|---|---|---|
| **Becker, J.; Imholz, N.; Schwarzenbach, L.; Ghignone, E.; Baumann, N.; Magno, M. (2023). *Model- and acceleration-based pursuit controller for high-performance autonomous racing.* IEEE ICRA, 5276–5283.** | [10.1109/ICRA48891.2023.10161472](https://doi.org/10.1109/ICRA48891.2023.10161472) | On a **real F1TENTH car up to 11 m/s**, a model-aware pursuit controller beat plain geometric pure pursuit by about 4× on lateral error (0.055 m). Implies this repo's result may be specific to its speed regime and nominal plant. Scope the claim explicitly. | 3 | A |
| Liniger, A.; Domahidi, A.; Morari, M. (2015). *Optimization-based autonomous racing of 1:43 scale RC cars.* | [10.1002/oca.2123](https://doi.org/10.1002/oca.2123) · see [§1](01-vehicle-dynamics-and-system-id.md) | Sets expectations for what MPC actually buys at small scale: constraint handling and progress maximisation at the friction limit, **not** raw tracking accuracy. Consistent with the finding here. | 3 | B |
| Rosolia, U.; Borrelli, F. (2018). *Learning model predictive control for iterative tasks.* IEEE TAC 63(7), 1883–1896. | [10.1109/TAC.2017.2753460](https://doi.org/10.1109/TAC.2017.2753460) | MPC's advantage emerges when the model or terminal set is learned from data over a repeated task. Explains why a one-shot nominal MPC on a nominal plant has little headroom over pure pursuit. | 2 | C |

## Why nominal optimality loses under model error

This is the theoretical backbone for the planned mismatch sweep.

| Citation | Link | Why it matters here | Ab | Ev |
|---|---|---|---|---|
| **Dean, S.; Mania, H.; Matni, N.; Recht, B.; Tu, S. (2020). *On the sample complexity of the linear quadratic regulator.* Found. Comput. Math. 20(4), 633–679.** | [10.1007/s10208-019-09426-y](https://doi.org/10.1007/s10208-019-09426-y) | Rigorous demonstration that certainty-equivalent LQR degrades, and can destabilise, under identification error while an uncertainty-aware design does not. **Strongest theoretical support for "the optimal controller loses under model error."** | 3 | C |
| Yu, S.; Reble, M.; Chen, H.; Allgöwer, F. (2014). *Inherent robustness properties of quasi-infinite horizon nonlinear MPC.* Automatica 50(9), 2269–2280. | [10.1016/j.automatica.2014.07.014](https://doi.org/10.1016/j.automatica.2014.07.014) | How much model and disturbance error nominal MPC tolerates **without** robust design. Formal basis for predicting which controller degrades first in the sweep. | 3 | D |
| **Tufa, L. D.; Ka, C. Z. (2016). *Effect of model plant mismatch on MPC performance and mismatch threshold determination.* Procedia Engineering 148, 1008–1014.** | [10.1016/j.proeng.2016.06.518](https://doi.org/10.1016/j.proeng.2016.06.518) | Studies **how much** mismatch is needed before MPC degrades measurably, and proposes thresholds. Methodologically the closest analogue to the planned wheelbase/mass/friction/delay sweep: use it to **choose sweep magnitudes instead of guessing**. | 3 | C |
| Kong, J.; Pfeiffer, M.; Schildbach, G.; Borrelli, F. (2015). | [10.1109/IVS.2015.7225830](https://doi.org/10.1109/IVS.2015.7225830) · see [§1](01-vehicle-dynamics-and-system-id.md) | Gets good MPC performance from the cruder kinematic model: the **size** of model error, not model complexity, predicts degradation. | 3 | B |
| Mayne, D. Q. (2014). *Model predictive control: recent developments and future promise.* Automatica 50(12), 2967–2986. | [10.1016/j.automatica.2014.10.128](https://doi.org/10.1016/j.automatica.2014.10.128) | Authoritative statement that MPC's distinctive value is explicit constraint satisfaction, and that robustness requires deliberate design. Exactly this repo's stated justification for MPC over accuracy. | 3 | D |
| Song, Y.; Romero, A.; Müller, M.; Koltun, V.; Scaramuzza, D. (2023). *Reaching the limit in autonomous racing: optimal control versus reinforcement learning.* Science Robotics 8(82), eadg1462. | [10.1126/scirobotics.adg1462](https://doi.org/10.1126/scirobotics.adg1462) | Optimal control loses to a learned policy because of decomposition and unmodelled effects. Independent high-quality instance of the same pattern. | 2 | A |
| Recht, B. (2019). *A tour of reinforcement learning: the view from continuous control.* Annu. Rev. Control Robot. Auton. Syst. 2, 253–279. | [10.1146/annurev-control-053018-023825](https://doi.org/10.1146/annurev-control-053018-023825) | Readable framing of nominal optimality vs robustness on the LQR case, plus a critique of benchmark-driven claims. Useful in both discussion and methodology. | 2 | D |
| Yu, S.; Hirche, M.; Huang, Y.; Chen, H.; Allgöwer, F. (2021). *MPC for autonomous ground vehicles: a review.* Autonomous Intelligent Systems 1(1). | [10.1007/s43684-021-00005-z](https://doi.org/10.1007/s43684-021-00005-z) | Survey of MPC formulations including robust and tube variants. The citation for "here is the MPC design space I did not explore, and why." | 2 | D |

## Real-time MPC and solver timing

| Citation | Link | Why it matters here | Ab | Ev |
|---|---|---|---|---|
| **Verschueren, R.; Frison, G.; Kouzoupis, D.; Frey, J.; et al. (2022). *acados — a modular open-source framework for fast embedded optimal control.* Math. Prog. Comp. 14(1), 147–183.** | [10.1007/s12532-021-00208-8](https://doi.org/10.1007/s12532-021-00208-8) | The reference point for what real-time MPC solve times look like with a purpose-built embedded stack. This repo's 1.33 ms p95 SciPy SLSQP figure should be reported against it, which frames SLSQP as a **prototype, not a deployment claim**. | 3 | B |
| Domahidi, A.; Zgraggen, A. U.; Zeilinger, M. N.; Morari, M.; Jones, C. N. (2012). *Efficient interior point methods for multistage problems arising in receding horizon control.* IEEE CDC, 668–674. | [10.1109/CDC.2012.6426855](https://doi.org/10.1109/CDC.2012.6426855) | The structure-exploiting solver behind the real-time claims in the racing papers above. Cite when arguing a bounded-runtime guarantee is achievable in principle. | 2 | B |

## State estimation

| Citation | Link | Why it matters here | Ab | Ev |
|---|---|---|---|---|
| **Walsh, C. H.; Karaman, S. (2018). *CDDT: fast approximate 2D ray casting for accelerated localization.* IEEE ICRA, 3677–3684.** | [10.1109/ICRA.2018.8460743](https://doi.org/10.1109/ICRA.2018.8460743) | The particle-filter localisation actually used in F1TENTH courses: 2500 particles at 40 Hz on a Jetson TX1. The concrete alternative this repo's EKF study should be positioned against, with a real compute budget. | 3 | B |
| Dellaert, F.; Fox, D.; Burgard, W.; Thrun, S. (1999). *Monte Carlo localization for mobile robots.* IEEE ICRA 2, 1322–1328. | [10.1109/ROBOT.1999.772544](https://doi.org/10.1109/ROBOT.1999.772544) | Origin of the particle-filter family. Cite for the EKF-vs-MCL trade: unimodal Gaussian against multimodal, non-Gaussian posterior. | 2 | B |
| Hrgetić, M.; Deur, J. (2020). *Experimental analysis of Kalman filter-based vehicle sideslip angle estimation accuracy and related error-compensation techniques.* IEEE I2MTC, 1–6. | [10.1109/I2MTC43012.2020.9128588](https://doi.org/10.1109/I2MTC43012.2020.9128588) | Experimental quantification of where a single-track EKF loses accuracy. Evidence that this repo's EKF error budget should be attributed to **model terms**, not filter tuning. | 3 | A |
| Goblirsch, S.; Weinmann, M.; Betz, J. (2024). *Three-dimensional vehicle dynamics state estimation for high-speed race cars under varying signal quality.* IEEE/RSJ IROS, 3371–3378. | [10.1109/IROS58592.2024.10802776](https://doi.org/10.1109/IROS58592.2024.10802776) | Racing-specific estimation with degraded-signal robustness, and a concrete failure-mode list that should feed the FMEA's sensor-degradation branches. | 2 | B |
| Kabzan, J.; Valls, M. I.; Reijgwart, V.; et al. (2020). *AMZ Driverless: the full autonomous racing system.* J. Field Robotics 37(7), 1267–1294. | [10.1002/rob.21977](https://doi.org/10.1002/rob.21977) | Full-stack competition-winning system; a real-world sanity check on where EKF-class estimators sit relative to the controller, and support for the FMEA framing. | 2 | A |

## Fair comparison and empirical practice

| Citation | Link | Why it matters here | Ab | Ev |
|---|---|---|---|---|
| **Henderson, P.; Islam, R.; Bachman, P.; Pineau, J.; Precup, D.; Meger, D. (2018). *Deep reinforcement learning that matters.* AAAI 32(1).** | [10.1609/aaai.v32i1.11694](https://doi.org/10.1609/aaai.v32i1.11694) | The standard citation for weak empirical practice: seed variance, cherry-picked baselines, non-reproducible comparisons. Justifies the same-track/same-seed protocol **and obliges reporting across-seed spread, not only point RMS values** — which this repo does not yet do. | 3 | B |
| Bonsignorio, F.; del Pobil, A. P. (2015). *Toward replicable and measurable robotics research.* IEEE Robotics & Automation Magazine 22(3), 32–35. | [10.1109/MRA.2015.2452073](https://doi.org/10.1109/MRA.2015.2452073) | Short, citable community statement of replicability norms. Justification for the experimental-methodology section. | 2 | D |
| Evans, B. D.; Trumpp, R.; et al. (2024). *Unifying F1TENTH.* | <https://arxiv.org/abs/2402.18558> · see [§1](01-vehicle-dynamics-and-system-id.md) | Benchmarks particle-filter localisation, tracking, MPCC, follow-the-gap and end-to-end RL on one F1TENTH testbed, and studies control frequency as a factor. Nearest thing to a fair-comparison standard for this exact platform. | 3 | C |

## Not verified, deliberately absent

- **No verified publication reports plain pure pursuit beating a properly tuned MPC on RMS cross-track
  error on the same track.** The nearest real-hardware result (Becker et al. 2023) runs the other way.
  The honest framing for this repo is "under our nominal plant, tuning budget and speed regime."
- Two frequently-cited controller-comparison papers ("Stanley vs LQR vs MPC", ICISGT 2019; "PID vs LQR
  vs MPC", ICSTCEE 2020) appeared only in search-engine summaries with no publisher or Crossref record
  reachable. **Excluded. Do not cite without a DOI.**

## Two actions this section implies

1. **Add Stanley as a third geometric baseline.** Three controllers but only one geometric one; Stanley
   is the standard co-baseline and its absence is the first thing a reviewer asks about.
2. **Let Tufa & Ka set the sweep magnitudes.** It turns "wheelbase ±X%, mass ±Y%" from an arbitrary
   choice into a published method for determining mismatch thresholds.
