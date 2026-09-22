# 4. Measurement uncertainty, force calibration, and displacement metrology

Scope: the E1–E3 acquisition and calibration software, the 5 kg load cell, and the static compliance
campaign that must demonstrate relative expanded uncertainty U95 ≤ 10 % on a fitted compliance slope.
Grading scheme: [README](README.md).

> **This section contains three findings that contradict the repo's current frozen protocol.** They are
> collected under "What this section changes" at the end. They are not applied anywhere: the protocol in
> [`docs/specs/mast-physical-validation/design.md`](../docs/specs/mast-physical-validation/design.md) is
> frozen and amending it is a prospective, owner-reviewed act.

## The uncertainty framework

| Citation | Link | Why it matters here | Ab | Ev |
|---|---|---|---|---|
| **JCGM 100:2008. *Evaluation of measurement data — Guide to the expression of uncertainty in measurement* (GUM).** | [10.59161/JCGM100-2008E](https://doi.org/10.59161/JCGM100-2008E) | Defines U95, combined standard uncertainty, coverage factor, Type A/B evaluation and the law of propagation. The repo's "U95 ≤ 10 %" gate is only meaningful stated per GUM. **Annex G** is the k=2 vs Student-t and effective-degrees-of-freedom treatment a 5-point fit needs. | 3 | A |
| JCGM 101:2008. *Supplement 1 — Propagation of distributions using a Monte Carlo method.* | [10.59161/JCGM101-2008](https://doi.org/10.59161/JCGM101-2008) | The compliance slope is a nonlinear function of correlated fitted parameters plus a rotation correction, so first-order propagation may misstate U. Monte Carlo is the sanctioned alternative and is trivial to add to the existing pipeline. | 3 | A |
| JCGM 100:2008/Amd.1:2026. *Amendment 1: Nonlinearity in measurement models.* | [10.59161/PPDI3267](https://doi.org/10.59161/PPDI3267) | Governs when linear propagation is inadequate. Relevant because the Abbe/rotation correction is a product of two uncertain quantities. | 2 | A |
| ISO/IEC Guide 98-3:2008. *Uncertainty of measurement — Part 3 (GUM:1995).* | <https://www.iso.org/standard/50461.html> | The ISO-adopted citable form. Cite alongside JCGM 100 if a formally adopted standard is required. Paywalled; JCGM 100 is the free identical text. | 2 | A |
| Taylor, B. N.; Kuyatt, C. E. (1994). *NIST Technical Note 1297: Guidelines for Evaluating and Expressing the Uncertainty of NIST Measurement Results.* | [PDF](https://nvlpubs.nist.gov/nistpubs/legacy/tn/nbstechnicalnote1297.pdf) | Short, free, and the pragmatic house rule for **reporting**: default k=2, with Appendix B on the t-based alternative for small degrees of freedom. Use it for the wording of the U95 statement. | 3 | A |
| **EA-4/02 M:2022. *Evaluation of the Uncertainty of Measurement in Calibration.*** | [PDF](https://european-accreditation.org/wp-content/uploads/2018/10/EA-4-02.pdf) | Free, accreditation-mandatory GUM implementation. Its §5 is the practical rule: **report k=2 only when the output distribution is near-normal and effective degrees of freedom are large; otherwise take k from the t-distribution** — the realistic case for a 5-point fit. | 3 | A |

## Force calibration standards

| Citation | Link | Why it matters here | Ab | Ev |
|---|---|---|---|---|
| **ASTM E74-18(2026). *Standard Practices for Calibration and Verification for Force-Measuring Instruments.*** | <https://store.astm.org/e0074-18e01.html> | The North-American governing practice for calibrating an elastic force-measuring instrument: load-point number and spacing, replicate runs, least-squares calibration equation, and a **lower limit factor that sets the smallest force the device may be used at**. Directly constrains the 4 N point. Paywalled. | 3 | A |
| ISO 376:2011. *Metallic materials — Calibration of force-proving instruments used for the verification of uniaxial testing machines.* | <https://www.iso.org/standard/44661.html> | International counterpart: classification from reproducibility, repeatability, interpolation, zero and reversibility errors — it names and bounds precisely the load-cell error terms in the budget. Annex C adds an uncertainty procedure. Paywalled. | 3 | A |
| **OIML R 60-1:2021. *Metrological regulation for load cells — Part 1.*** | [PDF](https://www.oiml.org/en/files/pdf_r/r060-1-e21.pdf) | **Free**, and the cleanest formal definitions of every error-budget term: creep, minimum dead load output return, hysteresis error, non-linearity, repeatability, and the two temperature effects. **Use its vocabulary verbatim in the error budget.** | 3 | A |
| Maybank, L.; Knott, A.; Elkington, D. (1999). *Guide to the Uncertainty of Force Measurement.* NPL Report CMAM 24. | [PDF](https://eprintspublications.npl.co.uk/1091/1/cmam24.pdf) | A worked, free, national-metrology-institute uncertainty budget for force transducers specifically. The closest existing template for the 5 kg cell budget. | 3 | A |
| *Guide to the Measurement of Force* (1998). Institute of Measurement and Control / NPL. ISBN 0 904457 28 1. | [PDF](https://www.instmc.org/_userfiles/pages/files/npl%20gpg/guide_to_the_measurement_of_force.pdf) | Free practical guide to cell selection, mounting and **parasitic loading** — directly relevant to hanging reference masses without side-load and off-axis moment errors. | 2 | B |

## Strain-gauge bridge error sources

| Citation | Link | Why it matters here | Ab | Ev |
|---|---|---|---|---|
| Micro-Measurements (Vishay). *Errors Due to Wheatstone Bridge Nonlinearity.* Tech Note TN-507-1. | [PDF](https://intertechnology.com/Vishay/pdfs/TechNotes_TechTips/TN-507.pdf) | Quantifies intrinsic unbalanced-bridge nonlinearity (roughly 0.1 % at 1000 µε). Shows how much of the cell's specified nonlinearity is circuit rather than element, and that **at these low strains it is negligible against ADC noise**. Companions TN-504 and TN-509 cover thermal output and transverse sensitivity. | 2 | B |
| Hoffmann, K. (1989). *An Introduction to Measurements using Strain Gages.* HBM, Darmstadt. | [WorldCat](https://search.worldcat.org/title/896982817) | Standard treatment of the four-wire full bridge, excitation, lead-wire effects and the physical origins of creep, hysteresis and thermal output. Justifies **why** each term is in the budget rather than just listing it. No DOI. | 2 | B |
| Ştefănescu, D. M. (2011). *Handbook of Force Transducers: Principles and Components.* Springer. | [10.1007/978-3-642-18296-9](https://doi.org/10.1007/978-3-642-18296-9) | Reference-depth coverage of strain-gauged elastic elements and metrological characteristics. Background for the 1 kg vs 5 kg cell choice over a 4–20 N range. | 1 | A |

## Fitting a slope when both variables carry uncertainty

The repo fits compliance as displacement per newton. **Both** axes carry uncertainty: applied force from
mass, g and tare; displacement from indicator resolution and root rotation.

| Citation | Link | Why it matters here | Ab | Ev |
|---|---|---|---|---|
| **York, D. (1966). *Least-squares fitting of a straight line.* Can. J. Phys. 44(5), 1079–1086.** | [10.1139/p66-090](https://doi.org/10.1139/p66-090) | The originating errors-in-variables solution. **Ordinary least squares biases the compliance slope low** when x carries error, which is exactly this case. | 3 | A |
| **York, D.; Evensen, N. M.; López Martínez, M.; De Basabe Delgado, J. (2004). *Unified equations for the slope, intercept, and standard errors of the best straight line.* Am. J. Phys. 72(3), 367–375.** | [10.1119/1.1632486](https://doi.org/10.1119/1.1632486) | The implementable version: closed-form **standard errors** on slope and intercept under correlated errors in both variables. This is the equation set that produces u(compliance) before the coverage factor is applied. | 3 | A |
| Cantrell, C. A. (2008). *Review of methods for linear least-squares fitting of data…* Atmos. Chem. Phys. 8, 5477–5487. | [10.5194/acp-8-5477-2008](https://doi.org/10.5194/acp-8-5477-2008) | Open-access side-by-side of OLS, weighted LS, York and other bivariate fits with guidance on which to use when. The fastest way to justify the fitting-method choice to a reviewer. | 3 | A |
| Fuller, W. A. (1987). *Measurement Error Models.* Wiley. | [10.1002/9780470316665](https://doi.org/10.1002/9780470316665) | Canonical monograph. Cite for the formal attenuation result and for variance estimators of the errors-in-variables slope. | 2 | A |
| Linnet, K. (1993). *Evaluation of regression procedures for methods comparison studies.* Clin. Chem. 39(3), 424–432. | [10.1093/clinchem/39.3.424](https://doi.org/10.1093/clinchem/39.3.424) | Establishes **when the extra machinery actually changes the answer**, and how sample size affects slope-SE reliability. Relevant because there are only five load points. | 2 | A |

## R² is not a calibration quality metric

| Citation | Link | Why it matters here | Ab | Ev |
|---|---|---|---|---|
| **Analytical Methods Committee (1994, rev. 2005). *Is my calibration linear?* Analyst 119(11), 2363–2366 / AMC Technical Brief No. 3.** | [10.1039/AN9941902363](https://doi.org/10.1039/AN9941902363) · [Brief PDF](https://www.rsc.org/images/calibration-linear-technical-brief-3_tcm18-214846.pdf) | **Direct authority against the repo's own gate.** States that r, and hence R², "is open to misinterpretation … and is to be discouraged"; a value near 1 can arise from points clustered about a visibly curved line. Recommends **residual-variance decomposition into lack-of-fit versus pure error**, which requires replicates at each load point. | 3 | A |
| Asuero, A. G.; Sayago, A.; González, A. G. (2006). *The correlation coefficient: an overview.* Crit. Rev. Anal. Chem. 36(1), 41–59. | [10.1080/10408340500526766](https://doi.org/10.1080/10408340500526766) | Peer-reviewed companion: why R² is neither a test of linearity nor a calibration-quality metric, and what the residual and prediction-interval alternatives are. | 2 | A |
| NIST/SEMATECH *e-Handbook of Statistical Methods*, §2.3.6–2.3.7. | [10.18434/M32189](https://doi.org/10.18434/M32189) · [handbook](https://www.itl.nist.gov/div898/handbook/) | Free worked treatment of propagating error through a fitted linear calibration to the uncertainty of a calibrated value, with control limits built from the **residual standard deviation and slope** rather than R². | 3 | A |
| ISO 11095:1996. *Linear calibration using reference materials.* | <https://www.iso.org/standard/1060.html> | Standardised procedure for estimating a linear calibration function from reference standards, checking the linearity assumption and maintaining statistical control. Paywalled. | 2 | A |

## ADC resolution: why 24 bits are not 24 useful bits

| Citation | Link | Why it matters here | Ab | Ev |
|---|---|---|---|---|
| Kester, W. *MT-004: The Good, the Bad, and the Ugly Aspects of ADC Input Noise.* Analog Devices. | [PDF](https://www.analog.com/media/en/training-seminars/tutorials/MT-004.pdf) | The canonical explanation: input-referred noise produces code-transition noise, and the usable figures are **noise-free code resolution** and **effective resolution**, both well below the nominal bit count. Governs how many NAU7802 counts are real at 4 N. | 3 | B |
| Analog Devices. *AN-2506: Precision Weigh Scale Design Using the AD7192 24-Bit Sigma-Delta ADC with Internal PGA.* | <https://www.analog.com/en/resources/app-notes/an-2506.html> | Weigh-scale-specific worked example: the design target is **noise-free counts**, set by PGA gain, output data rate and bridge excitation. Maps onto the NAU7802 plus 5 kg cell configuration and indicates what gain and rate to log at. | 3 | B |
| Nuvoton. *NAU7802: 24-Bit Dual-Channel ADC for Bridge Sensors* (datasheet). | <https://www.nuvoton.com/products/smart-home-audio/audio-converters/precision-adc-series/nau7802sgi/> | Primary source for the actual purchased part. **The quantisation and noise line item must come from this datasheet's table at the chosen gain and output rate**, not from the nominal 24 bits. | 3 | B |

## Displacement metrology at the micrometre level

Predicted specimen displacement at 20 N is about 27 µm, so this is the binding regime.

| Citation | Link | Why it matters here | Ab | Ev |
|---|---|---|---|---|
| **Flack, D. R.; Hannaford, J. (2006). *Fundamental Good Practice in Dimensional Metrology.* NPL Measurement Good Practice Guide No. 80.** | [PDF](https://eprintspublications.npl.co.uk/3360/1/mgpg80.pdf) | Free NMI guide covering traceability and dimensional error sources including the **Abbe principle** — the formal name for the repo's 50 µrad × 100 mm ≈ 5 µm problem. Cite it to justify measuring and correcting root rotation rather than ignoring it. | 3 | A |
| Haitjema, H. (2020). *The calibration of displacement sensors.* Sensors 20(3), 584. | [10.3390/s20030584](https://doi.org/10.3390/s20030584) | Open-access review of calibrating sub-100 µm displacement sensors against laser interferometry, with associated uncertainty levels. **Exactly this regime**, and the reference if indicators are upgraded to LVDT or capacitive probes. | 3 | A |
| ASME B89.1.10M-2001 (R2021). *Dial Indicators (for Linear Measurement).* | <https://www.asme.org/codes-standards/find-codes-standards/dial-indicators-(for-linear-measurement)> | Defines performance requirements and test procedures for dial indicators. What lets a **traceable uncertainty** be claimed rather than quoting display resolution — critical when total travel is about 27 µm. Paywalled. | 3 | A |
| ASTM E2309/E2309M-20. *Standard Practices for Verification of Displacement Measuring Systems and Devices Used in Material Testing Machines.* | <https://store.astm.org/e2309_e2309m-20.html> | Procedures and traceability requirements for verifying a displacement-measuring system: the framework for calibrating the tip and root indicators before the compliance run. Paywalled. | 3 | A |

## What this section changes

Three findings conflict with the current frozen protocol. Each needs a prospective, owner-reviewed
amendment; none is applied here.

1. **The `R² < 0.99` inconclusive gate rests on a metric the analytical-chemistry literature explicitly
   discourages for calibration.** A high R² is compatible with visible curvature. The cited replacement is
   lack-of-fit versus pure-error decomposition, **which requires replicates at each of the 4/8/12/16/20 N
   points** — a change to the test matrix, not just to the arithmetic.
2. **Ordinary least squares is the wrong estimator here and biases compliance low.** Both axes carry
   uncertainty, so York's errors-in-variables equations are the right basis, and they also supply the
   slope standard error the U95 gate needs.
3. **A k=2 coverage factor is not automatically right for a five-point fit.** EA-4/02 §5 requires
   effective degrees of freedom and a t-based factor unless the output is near-normal with large ν.
4. **The 4 N point may fall below the cell's usable floor.** ASTM E74's lower limit factor sets the
   smallest force an instrument may be used at; check the 5 kg cell against it before assuming the bottom
   of the range is calibratable.
5. **The NAU7802 noise budget must come from the datasheet at the chosen gain and rate**, not from "24-bit".

## Not verified, deliberately absent

- **No clause numbers are quoted from ASTM E74, ISO 376, ISO 11095, ASME B89.1.10M or ASTM E2309.** All are
  paywalled; only designation, title, year and scope were verified from official landing pages. **Do not cite
  clause numbers from any of them without buying the document.**
- **ASTM E74 current designation string**: the reapproval appears as E74-18(2026) in an ANSI listing, but the
  ASTM page for the reapproval returned HTTP 403. Confirm before printing it.
- **Analog Devices MT-004 and AN-2506 full text** could not be fetched; title, number and subject confirmed
  from the indexed URL and an independent mirror. Graded B until someone opens the PDF.
- **The NAU7802 "up to 23-bit ENOB" figure** came from indexed datasheet text, not a fetched PDF. Verify the
  ENOB against gain and output rate directly; the usable figure at gain 128 will be well below 23.
- **ISO 376 currency**: no revision found, but iso.org returned 403 so the status line could not be read first-hand.
- **No standard governs cantilever compliance testing at this scale, and no published uncertainty budget for a
  sub-30 µm static deflection test was found.** That gap is real: this test plan must be justified by composing
  the GUM, EA-4/02, the NIST handbook and the dimensional-metrology guides rather than by citing one document.
