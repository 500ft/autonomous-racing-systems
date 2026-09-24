# 3. Cantilever mast dynamics, tip mass, and impact modal testing

Scope: the LiDAR mast (6061-T6 tube, 100 mm free length, 20 mm OD, 1.5 mm wall, 0.175 kg tip mass),
the hand-calc vs FEA gap, the ≥ 200 Hz modal guard, and the **draft, not frozen** tap test under
RR-S11/RR-S12. Grading scheme: [README](README.md).

> This is the section with the most direct payoff. It supplies (a) four cited mechanisms that explain
> the repo's 330.1 → 285.5 Hz gap as *expected physics rather than a modelling defect*, and (b) the
> ISO standard that would convert the draft tap-test procedure into a defensible frozen plan.

## Cantilever with a tip mass: the hand calculation

| Citation | Link | Why it matters here | Ab | Ev |
|---|---|---|---|---|
| Blevins, R. D. (2015). *Formulas for Dynamics, Acoustics and Vibration.* Wiley. ISBN 9781119038115. | [10.1002/9781119038122](https://doi.org/10.1002/9781119038122) | Modern, DOI-citable successor to the 1979 tables. Clamped-free λ₁ and the tip-mass-loaded variants: the defensible source for the 330.1 Hz hand calculation. | 3 | A |
| Blevins, R. D. (1979). *Formulas for Natural Frequency and Mode Shape.* Van Nostrand Reinhold; reprints Krieger 1984/1995, 2001. | ISBN 9780442207106 / 9780894648946 / 9781575241845 | The canonical table source usually cited. **No DOI and four printings exist — cite the reprint actually held**, do not copy an ISBN from elsewhere. | 3 | A |
| Rao, S. S. (2021). *Mechanical Vibrations*, 6th ed. Pearson. ISBN 9780134361307. | <https://www.pearson.com/en-us/subject-catalog/p/Rao-Mechanical-Vibrations-6th-Edition/P200000003425/9780134361307> | Ch. 7 carries Rayleigh and Dunkerley with worked examples; Ch. 10 covers vibration measurement. Textbook citation for the Rayleigh energy method behind 330.1 Hz. | 3 | A |
| Dunkerley, S. (1894). *On the whirling and vibration of shafts.* Phil. Trans. R. Soc. Lond. A 185, 279–360. | [10.1098/rsta.1894.0008](https://doi.org/10.1098/rsta.1894.0008) | Primary source for the **lower**-bound estimate. Rayleigh gives an upper bound for the problem it is actually applied to. **A bound only brackets the FE value if both describe the same problem** — same mass model, same boundary conditions, same kinematics. That equivalence is not yet established here (see the [modal audit](../docs/design/MODAL_MODEL_AUDIT.md)), so the bracketing argument is currently unavailable. | 2 | A |
| Laura, P. A. A.; Pombo, J. L.; Susemihl, E. A. (1974). *A note on the vibrations of a clamped-free beam with a mass at the free end.* J. Sound Vib. 37(2), 161–168. | [10.1016/S0022-460X(74)80325-1](https://doi.org/10.1016/S0022-460X(74)80325-1) | The classic closed form for exactly this configuration. A direct analytical check on the Rayleigh number for the 0.175 kg tip mass. | 3 | A |

## Why the FEA lands 13.5 % below the hand calculation

> **Superseded in part, 2026-09-24.** These entries correctly describe mechanisms that shift a
> cantilever's frequency. They are **not** an attribution of this repo's 330.1 → 285.5 Hz gap. A source
> audit found that root flexibility and tip-mass rotary inertia cannot act between those two particular
> models: both fix the root, and the FE deck carries a one-node translational mass. See the
> [modal model audit](../docs/design/MODAL_MODEL_AUDIT.md) and revised claim M2. The cause is unresolved.

| Citation | Link | Mechanism and relevance | Ab | Ev |
|---|---|---|---|---|
| **Perkins, K. A. R. (1966). *The effect of support flexibility on the natural frequencies of a uniform cantilever.* J. Sound Vib. 4(1), 1–8.** | [10.1016/0022-460X(66)90148-9](https://doi.org/10.1016/0022-460X(66)90148-9) | **Root flexibility — the most on-point single reference.** Classic derivation of how a finitely stiff root shifts cantilever frequencies down. The standard explanation for hand-calc-vs-FE and FE-vs-test gaps in clamped structures, and the direct justification for the repo's support-sleeve decision. | 3 | A |
| Laura, P. A. A.; Maurizi, M. J.; Pombo, J. L. (1975). *A note on the dynamic analysis of an elastically restrained-free beam with a mass at the free end.* J. Sound Vib. 41(4), 397–405. | [10.1016/S0022-460X(75)80104-0](https://doi.org/10.1016/S0022-460X(75)80104-0) | Combines **both** error sources at once: finite root rotational stiffness and a free-end mass. The best analytic tool for asking what root stiffness would explain a 13.5 % drop. Also the bridge to the static test (below). | 3 | B |
| Bhat, R. B.; Wagner, H. (1976). *Natural frequencies of a uniform cantilever with a tip mass slender in the axial direction.* J. Sound Vib. 45(2), 304–307. | [10.1016/0022-460X(76)90606-4](https://doi.org/10.1016/0022-460X(76)90606-4) | **Tip-mass rotary inertia and axial extent.** A UST-10LX plus bracket is not a point mass; its extent lowers f₁ below the lumped-point prediction. A 2012 comment/response exchange exists ([10.1016/j.jsv.2012.01.038](https://doi.org/10.1016/j.jsv.2012.01.038), [.037](https://doi.org/10.1016/j.jsv.2012.01.037)) — read both before relying on the formula. | 3 | B |
| To, C. W. S. (1982). *Vibration of a cantilever beam with a base excitation and tip mass.* J. Sound Vib. 83(4), 445–460. | [10.1016/S0022-460X(82)80100-4](https://doi.org/10.1016/S0022-460X(82)80100-4) | Tip-mass rotary inertia **plus base excitation** — the actual load case, the chassis shaking the mast root. Relevant to whether the 100 Hz control rate or motor band excites the mast. | 3 | B |
| Timoshenko, S. P. (1921). *On the correction for shear of the differential equation for transverse vibrations of prismatic bars.* Phil. Mag. 41(245), 744–746. | [10.1080/14786442108636264](https://doi.org/10.1080/14786442108636264) | **Shear deformation.** Primary source. This mast is stocky enough (L/r ≈ 15) that Euler-Bernoulli over-predicts stiffness. | 3 | A |
| Han, S. M.; Benaroya, H.; Wei, T. (1999). *Dynamics of transversely vibrating beams using four engineering theories.* J. Sound Vib. 225(5), 935–988. | [10.1006/jsvi.1999.2257](https://doi.org/10.1006/jsvi.1999.2257) | Definitive side-by-side of Euler-Bernoulli, Rayleigh, shear and Timoshenko models with slenderness thresholds and error magnitudes. Use it to **quantify** how much of the −13.5 % is shear and rotary inertia versus root effects. | 3 | A |
| Cowper, G. R. (1966). *The shear coefficient in Timoshenko's beam theory.* J. Appl. Mech. 33(2), 335–340. | [10.1115/1.3625046](https://doi.org/10.1115/1.3625046) | Supplies the shear coefficient by cross-section, including **thin-walled circular tubes**, whose value is materially lower than a solid rod's. The shear correction here is larger than slenderness alone suggests. | 2 | A |

A fourth mechanism, local shell or ovalisation flexibility at the tube-clamp interface, is inferable
from Han et al. and Perkins but is **not separately cited**: a 1D beam model cannot represent it at all.

## Experimental modal analysis: planning the tap test

| Citation | Link | Why it matters here | Ab | Ev |
|---|---|---|---|---|
| **ISO 7626-5:2019. *Mechanical vibration and shock — Experimental determination of mechanical mobility — Part 5: Measurements using impact excitation with an exciter which is not attached to the structure.*** | <https://www.iso.org/standard/68735.html> | **The standard that governs the draft tap test.** Freezing the plan against a numbered clause set is what turns the RR-S11 draft into a defensible frozen procedure under RR-S12. Supersedes the 1994 edition. | 3 | A |
| Ewins, D. J. (2009). *Modal Testing: Theory, Practice and Application*, 2nd ed. Wiley. ISBN 9780863802188. | <https://www.wiley.com/en-us/Modal+Testing%3A+Theory%2C+Practice+and+Application%2C+2nd+Edition-p-9780863802188> | The reference text: FRF estimators, excitation choice, curve fitting, and FE/test correlation. How to defend the 285.5 Hz model against a measurement. | 3 | A |
| Avitabile, P. (2017). *Modal Testing: A Practitioner's Guide.* Wiley. ISBN 9781119222897. | [10.1002/9781119222989](https://doi.org/10.1002/9781119222989) | Practitioner-facing companion; the right source for tap-test procedure, windowing and double-hit handling in a student-scale report. Ch. 1 is [10.1002/9781119222989.ch1](https://doi.org/10.1002/9781119222989.ch1). | 3 | A |
| Ahn, S. J.; Jeong, W. B.; Yoo, W. S. (2004). *Unbiased expression of FRF with exponential window function in impact hammer testing.* J. Sound Vib. 277(4–5), 931–941. | [10.1016/j.jsv.2003.09.022](https://doi.org/10.1016/j.jsv.2003.09.022) | The exponential-window pitfall: the window adds **artificial damping** and biases the FRF, and this gives the correction. A 285 Hz mode in a short block will need a window; the windowed damping must not be reported as real. | 3 | B |
| Cawley, P. (1986). *The accuracy of frequency response function measurements using FFT-based analyzers with transient excitation.* J. Vib. Acoust. 108(1), 44–49. | [10.1115/1.3269302](https://doi.org/10.1115/1.3269302) | Quantifies FRF error for hammer excitation: leakage, resolution, window interaction. Sets the minimum block length and Δf needed to resolve f₁ cleanly. | 3 | B |
| Schmidt, H. (1985). *Resolution bias errors in spectral density, frequency response and coherence function measurements, I.* J. Sound Vib. 101(3), 347–362. | [10.1016/S0022-460X(85)80135-8](https://doi.org/10.1016/S0022-460X(85)80135-8) | Why coherence drops and peaks flatten when Δf is coarse relative to the half-power bandwidth. Justifies a **numeric** frequency-resolution requirement rather than "coherence looked fine." | 2 | B |

## Accelerometer mass loading

The LIS3DH purchased for E4 is the sensor this applies to.

| Citation | Link | Why it matters here | Ab | Ev |
|---|---|---|---|---|
| **Yadav, A.; Singh, N. K. (2019). *Effects of accelerometer mass on natural frequency of a magnesium alloy cantilever beam.* Vibroengineering Procedia 29, 207–212.** | [10.21595/vp.2019.21114](https://doi.org/10.21595/vp.2019.21114) | Same question, **same geometry class** (cantilever, impact hammer). Shows the shift depends strongly on sensor **position**: mounting near the root costs far less frequency error than at the tip. Directly actionable. | 3 | B |
| Ren, J.; Wang, J.; Bi, S. (2017). *Correction of transducer mass effects from the measured FRFs in hammer impact testing.* Shock and Vibration 2017, 6857326. | [10.1155/2017/6857326](https://doi.org/10.1155/2017/6857326) | Mass-loading correction derived **for hammer impact testing** rather than shaker testing. The method to back the accelerometer's effect out if it must be mounted near the tip. | 3 | B |
| Drvárová, B.; Dekýš, V.; Pijáková, K. (2023). *Effect of accelerometer mass on the natural frequencies of the measured structure.* Transportation Research Procedia 74, 740–747. | [10.1016/j.trpro.2023.11.205](https://doi.org/10.1016/j.trpro.2023.11.205) | Recent focused experimental quantification of the shift. For the tap-test error budget. | 3 | B |

## Does mast vibration actually degrade the LiDAR?

The ≥ 200 Hz guard is currently justified structurally. These two make it a **detection-quality**
requirement as well.

| Citation | Link | Why it matters here | Ab | Ev |
|---|---|---|---|---|
| Schlager, B.; Goelles, T.; Behmer, M.; Muckenhuber, S.; Payer, J.; Watzenig, D. (2022). *Automotive lidar and vibration: resonance, inertial measurement unit, and effects on the point cloud.* IEEE OJ-ITS 3, 426–434. | [10.1109/OJITS.2022.3176471](https://doi.org/10.1109/OJITS.2022.3176471) | **Answers the question with data.** Shaker tests of an automotive lidar over roughly 6–2000 Hz showed randomly distributed point loss largely independent of frequency and acceleration level. Open access. | 3 | B |
| Periu, C.; Mohsenimanesh, A.; Laguë, C.; McLaughlin, N. B. (2013). *Isolation of vibrations transmitted to a LIDAR sensor mounted on an agricultural vehicle to improve obstacle detection.* Canadian Biosystems Engineering 55(1), 2.33–2.42. | [10.7451/cbe.2013.55.2.33](https://doi.org/10.7451/cbe.2013.55.2.33) | The closest published analogue: a lidar on a vibrating ground vehicle with mount design as the fix. Supports framing the 200 Hz criterion as a detection-quality requirement. | 3 | B |

## What this section changes in the test plan

1. **Accelerometer placement is a tradeoff to be quantified, not a rule.** Yadav & Singh show the
   frequency shift depends on sensor position, which argues against mounting at the tip. It does **not**
   establish "near the root" as correct: close to a fixed root the bending response is also small, so
   signal-to-noise falls. Choose the position from the expected mode shape, the measured noise floor,
   the added mass and cable effects, and the quantity being identified — and record the comparison.
   *Derived estimate, not quoted by any cited paper, and using an illustrative sensor mass rather than a
   weighed LIS3DH assembly:* a 5–10 g addition is roughly 3–6 % of the 175 g tip mass, which by
   √(1/(1+Δm/m)) scaling is several Hz at 285 Hz. Weigh the actual board, mount and cable before using
   any such figure.
2. **Set frequency resolution from Cawley and Schmidt**, and state Δf and the half-power bandwidth
   explicitly rather than inspecting coherence after the fact.
3. **If an exponential window is used, report corrected damping**, never the windowed value.
4. **Write the frozen procedure against ISO 7626-5:2019 clauses.**
5. **Strongest available cross-check:** use Laura et al. (1975) to fit a root rotational stiffness from
   the 4–20 N static deflection curve, then **predict** the modal frequency from it. That links the
   static compliance campaign and the tap test into one falsifiable claim, which neither test produces alone.

## Not verified, deliberately absent

- **Rayleigh, *The Theory of Sound*, Vol. 1, Dover ISBN 0486602929**: Open Library returns no record for
  that ISBN. A Dover reprint is confirmed at 9780486602936. Do not print a Vol. 1 ISBN unchecked.
- **Timoshenko & Young, *Vibration Problems in Engineering***: no edition, publisher or ISBN verified. Omit.
- **Avitabile, "Experimental modal analysis: a simple non-mathematical presentation," Sound and Vibration (2001)**:
  sources disagree on year and locator, not in Crossref. **Use the verified 2017 book chapter instead.**
- **Halvorsen & Brown, "Impulse technique for structural frequency response testing," Sound and Vibration (1977)**:
  not in Crossref, volume/pages unverifiable. Only a 1978 JASA meeting abstract is verifiable. Do not cite with invented pages.
- **Mondal, Ghuku & Saha (2018) on clamping torque vs cantilever response**: DOI resolves and the topic is
  a near-perfect match, but the publisher could not be vouched for. Verified-but-low-confidence: use for
  ideas, cite Perkins for the claim.
- **No literature found on vibration of sensor masts on 1/10-scale racing platforms specifically.** The two
  entries above are the nearest verified analogues, at full automotive and agricultural scale.
