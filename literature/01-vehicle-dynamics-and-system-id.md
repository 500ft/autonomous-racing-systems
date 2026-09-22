# 1. Autonomous racing platforms, vehicle dynamics, and system identification

Scope: what the vehicle lane of this project models, and what the literature says about whether a
parameter identified in simulation means anything on a real car. Grading scheme and verification
policy: [README](README.md).

## Platform and simulator

| Citation | Link | Why it matters here | Ab | Ev |
|---|---|---|---|---|
| O'Kelly, M.; Zheng, H.; Karthik, D.; Mangharam, R. (2020). *F1TENTH: An Open-source Evaluation Environment for Continuous Control and Reinforcement Learning.* NeurIPS 2019 Competition and Demonstration Track, PMLR 123, 77–89. | <https://proceedings.mlr.press/v123/o-kelly20a.html> | Canonical citation for the platform **and** for `f1tenth_gym`; the gym README lists this as its only citation, so it is the required primary reference for every telemetry artifact in this repo. | 3 | B |
| `f1tenth_gym` source repository, F1TENTH Autonomous Racing Community. | <https://github.com/f1tenth/f1tenth_gym> | The exact environment `C_Sf`/`C_Sr` were fit against. Cite repo **plus** commit hash alongside the paper; see [upstream register](../docs/upstream_roboracer_sources.md). | 3 | — |
| O'Kelly, M.; Sukhil, V.; Abbas, H.; Harkins, J.; Kao, C.; Pant, Y. V.; Mangharam, R.; Agarwal, D.; Behl, M.; Burgio, P.; Bertogna, M. (2019). *F1/10: An Open-Source Autonomous Cyber-Physical Platform.* arXiv:1901.08567. | <https://arxiv.org/abs/1901.08567> | Documents the physical 1/10 vehicle (sensors, VESC, compute). The reference for arguing what a real-hardware validation of this pipeline would require. | 3 | D |

## Surveys

| Citation | Link | Why it matters here | Ab | Ev |
|---|---|---|---|---|
| Betz, J.; Zheng, H.; Liniger, A.; Rosolia, U.; Karle, P.; Behl, M.; Krovi, V.; Mangharam, R. (2022). *Autonomous Vehicles on the Edge: A Survey on Autonomous Vehicle Racing.* IEEE OJ-ITS 3, 458–488. | [10.1109/OJITS.2022.3181510](https://doi.org/10.1109/OJITS.2022.3181510) | Standard framing citation. Its modelling section justifies the single-track dynamic model as the accepted fidelity level for scaled racing, and it names the sim-to-real gap as an open problem. | 3 | D |
| Evans, B. D.; Trumpp, R.; Caccamo, M.; Jahncke, F.; Betz, J.; Jordaan, H. W.; Engelbrecht, H. A. (2024). *Unifying F1TENTH Autonomous Racing: Survey, Methods and Benchmarks.* arXiv:2402.18558. | <https://arxiv.org/abs/2402.18558> | F1TENTH-specific survey with an open benchmark; the place to position this pipeline against existing work and borrow evaluation conventions. arXiv-only. | 3 | C |
| Charles, I.; Maghsoumi, H.; Fallah, Y. (2025). *Advancing Autonomous Racing: A Comprehensive Survey of the RoboRacer (F1TENTH) Platform.* arXiv:2506.15899. | <https://arxiv.org/abs/2506.15899> | The only survey using the current **RoboRacer** name, with a dedicated sim-to-real section. arXiv-only. | 2 | D |

## Single-track model

| Citation | Link | Why it matters here | Ab | Ev |
|---|---|---|---|---|
| Althoff, M.; Würsching, G. (2020). *CommonRoad: Vehicle Models (Version 2020a).* TU München. | [PDF](https://gitlab.lrz.de/tum-cps/commonroad-vehicle-models/-/raw/master/vehicleModels_commonRoad.pdf) | The literal source of the single-track state equations, the `C_Sf`/`C_Sr` parameterisation and the steering/acceleration constraints `f1tenth_gym` implements. Without it the "recovering the simulator's own parameters" claim has no defined ground truth. | 3 | C |
| Althoff, M.; Koschi, M.; Manzinger, S. (2017). *CommonRoad: Composable benchmarks for motion planning on roads.* IEEE IV, 719–726. | [10.1109/IVS.2017.7995802](https://doi.org/10.1109/IVS.2017.7995802) | Citable paper for the CommonRoad framework; the vehicle-models document above is a tech report. Cite both. | 2 | C |
| Rajamani, R. (2012). *Vehicle Dynamics and Control*, 2nd ed. Springer. ISBN 978-1-4614-1432-2. | [10.1007/978-1-4614-1433-9](https://doi.org/10.1007/978-1-4614-1433-9) | Standard derivation of the lateral bicycle model and the small-slip linear tire assumption `F_y = C_α·α`, which is exactly what the least-squares fit assumes. | 3 | B |
| Milliken, W. F.; Milliken, D. L. (1995). *Race Car Vehicle Dynamics.* SAE R-146. ISBN 978-1-56091-526-3. | <https://www.sae.org/books/race-car-vehicle-dynamics-r-146> | Defines cornering stiffness operationally as the slope of the lateral-force/slip-angle curve near zero, and load dependent. The reference for stating what a single scalar `C_Sf`/`C_Sr` represents and where it stops being valid. No DOI. | 2 | B |
| Kong, J.; Pfeiffer, M.; Schildbach, G.; Borrelli, F. (2015). *Kinematic and dynamic vehicle models for autonomous driving control design.* IEEE IV, 1094–1099. | [10.1109/IVS.2015.7225830](https://doi.org/10.1109/IVS.2015.7225830) | Quantifies forecast error of kinematic vs dynamic bicycle models against experimental data, and flags the low-speed tire-model singularity. The justification this repo's model pair needs. | 3 | B |
| Polack, P.; Altché, F.; d'Andréa-Novel, B.; de La Fortelle, A. (2017). *The kinematic bicycle model: a consistent model for planning feasible trajectories for autonomous vehicles?* IEEE IV, 812–818. | [10.1109/IVS.2017.7995816](https://doi.org/10.1109/IVS.2017.7995816) | Gives the lateral-acceleration threshold above which the kinematic model becomes inconsistent. A defensible criterion for when the dynamic model must be used. | 3 | C |

## Tire models and cornering stiffness

| Citation | Link | Why it matters here | Ab | Ev |
|---|---|---|---|---|
| Pacejka, H. B.; Bakker, E. (1992). *The Magic Formula Tyre Model.* Vehicle System Dynamics 21(sup1), 1–18. | [10.1080/00423119208969994](https://doi.org/10.1080/00423119208969994) | Origin of the Magic Formula; its stiffness factor **is** cornering stiffness, so this places the single linear `C_α` inside the full nonlinear curve and shows what the linear fit discards. | 3 | A |
| Pacejka, H. B. (2012). *Tire and Vehicle Dynamics*, 3rd ed. Butterworth-Heinemann. ISBN 978-0-08-097016-5. | <https://shop.elsevier.com/books/tire-and-vehicle-dynamics/pacejka/978-0-08-097016-5> | Load dependence and relaxation-length transients, both unmodelled here and both first-order candidates for sim-to-real error. | 2 | A |

## Identification methodology

| Citation | Link | Why it matters here | Ab | Ev |
|---|---|---|---|---|
| **Dikici, O.; Ghignone, E.; Hu, C.; Baumann, N.; Xie, L.; Carron, A.; Magno, M.; Corno, M. (2025). *Learning-Based On-Track System Identification for Scaled Autonomous Racing in Under a Minute.* IEEE RA-L 10(2), 1984–1991.** | [10.1109/LRA.2025.3527336](https://doi.org/10.1109/LRA.2025.3527336) · [arXiv](https://arxiv.org/abs/2411.17508) | **The most important item for this project's known weakness.** Identifies tire parameters on a real scaled racing platform from about 30 s of on-track data, 3.3× lower RMSE than baseline under noise. This is the paper a reviewer asks why you did not do. | 3 | B |
| Sierra, C.; Tseng, E.; Jain, A.; Peng, H. (2006). *Cornering stiffness estimation based on vehicle lateral dynamics.* Vehicle System Dynamics 44(sup1), 24–38. | [10.1080/00423110600867259](https://doi.org/10.1080/00423110600867259) | Closest prior art to the bounded NLS fit here, and it carries the **same** sim-only validation limitation, which can be cited honestly rather than hidden. | 3 | C |
| Wesemeier, D.; Isermann, R. (2009). *Identification of vehicle parameters using stationary driving maneuvers.* Control Engineering Practice 17(12), 1426–1431. | [10.1016/j.conengprac.2008.10.008](https://doi.org/10.1016/j.conengprac.2008.10.008) | Real-vehicle experiment design: which steady-state maneuvers actually excite the lateral parameters. The template for the physical test that would close the sim-vs-sim gap. | 3 | B |
| Boyali, A.; Thompson, S.; Wong, D. R. (2021). *Identification of Vehicle Dynamics Parameters Using Simulation-based Inference.* arXiv:2108.12114. | <https://arxiv.org/abs/2108.12114> | Bayesian alternative returning posteriors over tire parameters. The natural next step for reporting **uncertainty** on `C_Sf`/`C_Sr` instead of a point estimate. | 2 | D |
| **Ljung, L. (1999). *System Identification: Theory for the User*, 2nd ed. Prentice Hall. ISBN 0-13-656695-2.** | <https://www.informit.com/store/system-identification-theory-for-the-user-9780136566953> | The methodological backbone, and the direct authority for this repo's own caveat: fitting a model to data generated by that same model structure validates the **estimator**, not the model. | 3 | B |
| Bellman, R.; Åström, K. J. (1970). *On structural identifiability.* Mathematical Biosciences 7(3–4), 329–339. | [10.1016/0025-5564(70)90132-X](https://doi.org/10.1016/0025-5564(70)90132-X) | Correct vocabulary for asking whether `C_Sf` and `C_Sr` are **separately** identifiable from these telemetry channels or only in a lumped combination. A real risk with understeer-gradient-like data. | 2 | D |
| Green, M.; Moore, J. B. (1986). *Persistence of excitation in linear systems.* Systems & Control Letters 7(5), 351–360. | [10.1016/0167-6911(86)90052-6](https://doi.org/10.1016/0167-6911(86)90052-6) | The persistent-excitation condition this project should state explicitly for its excitation sequences; without it, convergence in held-out validation is not guaranteed by anything but luck. | 2 | D |

## Sim-to-real

| Citation | Link | Why it matters here | Ab | Ev |
|---|---|---|---|---|
| Chisari, E.; Liniger, A.; Rupenyan, A.; Van Gool, L.; Lygeros, J. (2021). *Learning from Simulation, Racing in Reality.* IEEE ICRA, 8046–8052. | [10.1109/icra48506.2021.9562079](https://doi.org/10.1109/icra48506.2021.9562079) | Closest analogue: a policy trained in a simple simulated vehicle model with **model randomization** transfers to a real miniature race car; fine-tuning on 3 h of real data halved track violations. Motivates randomising `C_Sf`/`C_Sr` rather than point-identifying them. | 3 | B |
| Evans, B. D.; Jordaan, H. W.; Engelbrecht, H. A. (2023). *Comparing deep reinforcement learning architectures for autonomous racing.* Machine Learning with Applications 14, 100496. | [10.1016/j.mlwa.2023.100496](https://doi.org/10.1016/j.mlwa.2023.100496) | Runs sim-trained agents on real F1TENTH hardware to about 5 m/s and reports measured degradation. Concrete numbers for how large the F1TENTH reality gap actually is. | 3 | B |
| Liniger, A.; Domahidi, A.; Morari, M. (2015). *Optimization-based autonomous racing of 1:43 scale RC cars.* Optimal Control Applications and Methods 36(5), 628–647. | [10.1002/oca.2123](https://doi.org/10.1002/oca.2123) | Identifies a Pacejka model from **real** 1:43 RC-car data and races at tire saturation. Proof that scaled-vehicle tire identification from real telemetry is achievable, and a benchmark for what this pipeline would have to produce. | 3 | B |
| Tobin, J.; Fong, R.; Ray, A.; Schneider, J.; Zaremba, W.; Abbeel, P. (2017). *Domain randomization for transferring deep neural networks from simulation to the real world.* IEEE/RSJ IROS, 23–30. | [10.1109/IROS.2017.8202133](https://doi.org/10.1109/IROS.2017.8202133) | Origin citation for domain randomization; the standard reference for treating tire parameters as a distribution rather than a single sim-identified value. | 2 | B |
| Zhao, W.; Queralta, J. P.; Westerlund, T. (2020). *Sim-to-Real Transfer in Deep Reinforcement Learning for Robotics: a Survey.* IEEE SSCI, 737–744. | [10.1109/SSCI47803.2020.9308468](https://doi.org/10.1109/SSCI47803.2020.9308468) | Taxonomy of reality-gap mitigations. Cite once when conceding the sim-vs-sim limitation and naming the options. | 2 | D |
| Loquercio, A.; Kaufmann, E.; Ranftl, R.; Dosovitskiy, A.; Koltun, V.; Scaramuzza, D. (2020). *Deep Drone Racing: From Simulation to Reality With Domain Randomization.* IEEE T-RO 36(1), 1–14. | [10.1109/tro.2019.2942989](https://doi.org/10.1109/tro.2019.2942989) | Independent second data point that randomization beats point-identification when the gap is dominated by unmodelled dynamics. Non-car domain. | 1 | B |

## Not verified, deliberately absent

- **A standalone `f1tenth_gym` paper does not exist.** The repository README's only BibTeX entry is O'Kelly et al. 2020. Cite repo plus that paper; do not invent a gym paper.
- **Milliken & Milliken DOI**: SAE books have none. Bibliographic data confirmed via Open Library; DOI omitted rather than guessed.
- **Pacejka 3rd ed. co-author**: the Elsevier page lists Pacejka only. Some catalogues add I. J. M. Besselink. Verify before citing him.
- **Evans et al. "Bypassing the Simulation-to-Reality Gap" (ICAR 2023)**: appeared in search snippets, no publisher/DOI page reached. Omitted as unverified.
- **A single citation for optimal input design specific to cornering-stiffness identification**: none found that could be verified end to end. The identifiability and excitation entries above cover the ground between them.
