# 5. Simulation V&V, bolted clamp, tolerancing, and materials

Scope: the CalculiX FEA acceptance chain (mesh convergence, ±15 % vs hand calc, root-singularity
exclusion), the split clamp and support sleeve on `cad/solidworks/`, the sightline tolerance stack, and
6061-T6 material basis. Grading scheme: [README](README.md).

> **Load-bearing ten**, if only a few are read: ASME V&V 10, Celik et al. (GCI recipe), Sinclair et al.
> 2019 and 2016 (the singularity pair), VDI 2230, ECSS threaded-fasteners handbook, Campos & Hall,
> DeRuntz & Hodge, EN 10204, and Sadowski & Rotter.

## Verification and validation doctrine

| Citation | Link | Why it matters here | Ab | Ev |
|---|---|---|---|---|
| **ASME V&V 10-2019 (R2025). *Standard for Verification and Validation in Computational Solid Mechanics.*** | [asme.org](https://www.asme.org/codes-standards/find-codes-standards/standard-for-verification-and-validation-in-computational-solid-mechanics) | The governing doctrine. Frames the mesh study as **solution verification** and the ±15 % hand-calc comparison as **validation against a reference solution**. Gives the report the vocabulary a reviewer expects. Note it is a "Standard"; the 2006 edition was a "Guide". | 3 | A |
| ASME V&V 10.1-2012 (R2022). *An Illustration of the Concepts of Verification and Validation in Computational Solid Mechanics.* | [asme.org](https://www.asme.org/codes-standards/find-codes-standards/an-illustration-of-the-concepts-of-verification-and-validation-in-computational-solid-mechanics) | The worked-example companion: a template for laying out a small V&V case exactly like this cantilever. | 3 | A |
| ASME VVUQ 1-2022. *Verification, Validation, and Uncertainty Quantification Terminology.* | [asme.org](https://www.asme.org/codes-standards/find-codes-standards/verification-validation-and-uncertainty-quantification-terminology-in-computational-modeling-and-simulation) | Harmonised definitions. Stops "verification" and "validation" being used loosely in the report. | 2 | A |
| ASME V&V 20-2009 (R2021). *…Computational Fluid Dynamics and Heat Transfer.* | [asme.org](https://www.asme.org/codes-standards/find-codes-standards/standard-for-verification-and-validation-in-computational-fluid-dynamics-and-heat-transfer) | Out of domain, but the source of the quantitative validation-uncertainty algebra (comparison error = model + numerical + input + data uncertainty). Cite for method, not scope. | 1 | A |
| NASA-STD-7009B w/ Change 1 (2024). *Standard for Models and Simulations.* | [standards.nasa.gov](https://standards.nasa.gov/standard/NASA/NASA-STD-7009) | Free and public, and requires acceptance criteria to be defined **up front** — institutional backing for declaring the ±15 % bound and the gauge region before running the model, which this repo does. | 2 | A |
| Oberkampf, W. L.; Roy, C. J. (2010). *Verification and Validation in Scientific Computing.* Cambridge. | [10.1017/CBO9780511760396](https://doi.org/10.1017/CBO9780511760396) | The standard monograph; solution-verification and discretization-error chapters are the textbook basis for what the convergence study claims. A 2025 2nd edition exists but could not be fully verified — cite this one. | 3 | B |
| Roache, P. J. (1998). *Verification and Validation in Computational Science and Engineering.* Hermosa. | ISBN 978-0-913478-08-0 | Book-length treatment of grid convergence, the origin of much of what V&V 10 formalised. | 2 | B |
| NAFEMS (2020). *Engineering Simulation Quality Management Standard*, ESQMS:01. | [nafems.org](https://www.nafems.org/publications/resource_center/esqms-01/) | ISO 9001 interpreted for simulation. Relevant only if claiming the analysis sits under a quality process. | 1 | B |

## Mesh convergence and discretization error

| Citation | Link | Why it matters here | Ab | Ev |
|---|---|---|---|---|
| **Celik, I. B.; Ghia, U.; Roache, P. J.; Freitas, C. J.; Coleman, H.; Raad, P. E. (2008). *Procedure for estimation and reporting of uncertainty due to discretization in CFD applications.* J. Fluids Eng. 130(7), 078001.** | [10.1115/1.2960953](https://doi.org/10.1115/1.2960953) | **The recipe**: three grids, compute the observed order, apply the Grid Convergence Index with a factor of safety. The repo's "under 1.5 % change at final refinement" is a **bare delta with no safety factor and no observed order** — this converts it into a defensible numerical-uncertainty band. | 3 | A |
| Roache, P. J. (1994). *Perspective: a method for uniform reporting of grid refinement studies.* J. Fluids Eng. 116(3), 405–413. | [10.1115/1.2910291](https://doi.org/10.1115/1.2910291) | Origin of the Grid Convergence Index. | 3 | A |
| Roache, P. J. (1997). *Quantification of uncertainty in computational fluid dynamics.* Annu. Rev. Fluid Mech. 29, 123–160. | [10.1146/annurev.fluid.29.1.123](https://doi.org/10.1146/annurev.fluid.29.1.123) | Review of Richardson extrapolation, observed order, and why a single refinement step is insufficient. | 2 | A |
| Roache, P. J.; Ghia, K. N.; White, F. M. (1986). *Editorial policy statement on the control of numerical accuracy.* J. Fluids Eng. 108(1), 2. | [ASME DL](https://asmedigitalcollection.asme.org/fluidsengineering/article/108/1/2/409997/Editorial-Policy-Statement-on-the-Control-of) | The first journal policy to refuse papers lacking systematic truncation-error testing. Precedent for treating a convergence study as mandatory. | 2 | A |

## The root singularity: justifying its exclusion

This repo already excludes the fixed-root peak von Mises stress in favour of a mid-span gauge region and
tip deflection. That choice has a published procedure behind it.

| Citation | Link | Why it matters here | Ab | Ev |
|---|---|---|---|---|
| **Sinclair, G. B.; Beisheim, J. R.; Kardak, A. A. (2019). *On the detection of stress singularities in finite element analysis.* J. Appl. Mech. 86(2), 021005.** | [10.1115/1.4041766](https://doi.org/10.1115/1.4041766) | **Strongest single citation for the acceptance scheme.** Formalises mesh refinement with **divergence** checks as the counterpart to convergence checks, validated on 265 FE stresses at 32 singularities. Turns "we ignored the root" into a published procedure. | 3 | A |
| **Sinclair, G. B.; Beisheim, J. R.; Roache, P. J. (2016). *Effective convergence checks for verifying finite element stresses at two-dimensional stress concentrations.* J. Verif. Valid. Uncertain. Quantif. 1(4), 041003.** | [10.1115/1.4034977](https://doi.org/10.1115/1.4034977) | The positive counterpart: how to verify stresses that **do** converge, with conservative error estimation against seven exact solutions. Justifies the mid-span gauge region as the quantity carrying the criterion. **Cite as a pair with the above.** | 3 | A |
| Williams, M. L. (1952). *Stress singularities resulting from various boundary conditions in angular corners of plates in extension.* J. Appl. Mech. 19(4), 526–528. | [10.1115/1.4010553](https://doi.org/10.1115/1.4010553) | The primary source. Eigenfunction expansion gives the singular exponent at a re-entrant corner: theoretical proof that **there is no finite converged peak stress to find** at the fixed root. | 3 | A |
| Sinclair, G. B. (2004). *Stress singularities in classical elasticity — I: removal, interpretation, and analysis.* Appl. Mech. Rev. 57(4), 251–298. | [10.1115/1.1762503](https://doi.org/10.1115/1.1762503) | Authoritative review of what to **do**: when a singularity is an artefact to remove (fillet, contact, plasticity) versus interpret. Supports excluding rather than reporting root stress. | 3 | A |
| Sinclair, G. B. (2004). *…— II: asymptotic identification.* Appl. Mech. Rev. 57(5), 385–439. | [10.1115/1.1767846](https://doi.org/10.1115/1.1767846) | Catalogue of exponents by geometry and boundary condition. Lets the report state the expected exponent at **this** clamped corner instead of asserting "it is singular". | 2 | A |
| Wood, J.; Olsson Robbie, M.; Hamilton, N. R.; Easton, D.; Zhang, Y. (2015). *Theoretical elastic stress singularities… much maligned and misunderstood.* NAFEMS World Congress. | [strathprints](https://strathprints.strath.ac.uk/51652/) | The practitioner-community voice: singularities are unavoidable idealisation artefacts and will always be the apparent peak-stress location. Conference paper, not peer reviewed. | 3 | C |

## Bolted joint and preload: the calculation not yet done

The repo models two M6 cross-bolts but has **no joint analysis**, and the plan explicitly forbids claiming
grip or yield acceptance without one.

| Citation | Link | Why it matters here | Ab | Ev |
|---|---|---|---|---|
| **VDI 2230 Blatt 1:2015-11. *Systematic calculation of highly stressed bolted joints — joints with one cylindrical bolt.*** | [vdi.de](https://www.vdi.de/en/home/vdi-standards/details/vdi-2230-blatt-1-systematic-calculation-of-highly-stressed-bolted-joints-joints-with-one-cylindrical-bolt) | The reference method for the two M6 cross-bolts: assembly preload with tightening-factor scatter, embedding loss, and a 13-step verification. **Do not cite a clause number** — see caveats. | 3 | A |
| **ECSS-E-HB-32-23A Rev.1 (2023). *Space engineering — Threaded fasteners handbook.*** | [PDF](https://ecss.nl/wp-content/uploads/2023/02/ECSS-E-HB-32-23A-Rev.1(6February2023).pdf) | **Free and detailed.** §9.2 gives the slip margin from **minimum** preload — the number that actually governs a two-bolt friction clamp. Best single practical source for this clamp. | 3 | B |
| RCSC (2020). *Specification for Structural Joints Using High-Strength Bolts.* | [PDF](https://www.boltcouncil.org/files/2020RCSCSpecification.pdf) | Free. Gives slip resistance in closed form with friction coefficient by surface class: the algebra for two bolts times preload times friction times faying surfaces. Civil domain — transplant the form, substitute a machined aluminium-on-aluminium coefficient. | 2 | A |
| Bickford, J. H. (2008). *Introduction to the Design and Behavior of Bolted Joints: Non-Gasketed Joints*, 4th ed. CRC. | [10.1201/9780849381874](https://doi.org/10.1201/9780849381874) | Preload scatter, torque-tension uncertainty, embedment and relaxation. In short, **why a seating torque does not give the preload you think it does**. | 3 | B |
| ISO 16047:2005 + Amd 1:2012. *Fasteners — torque/clamp force testing.* | [iso.org](https://www.iso.org/standard/27788.html) | The standard method to **measure** torque versus clamp force for the actual bolt, coating and thread. The honest way to close the gap between an assumed torque coefficient and real preload on a one-off clamp. | 3 | A |
| ISO 898-1:2013. *Mechanical properties of fasteners made of carbon steel and alloy steel — Part 1.* | [iso.org](https://www.iso.org/standard/60610.html) | Fixes the proof stress and yield of the chosen M6 property class: the input to the preload calculation. | 2 | A |
| Budynas, R. G.; Nisbett, J. K. (2020). *Shigley's Mechanical Engineering Design*, 11th ed. McGraw Hill. | [McGraw Hill](https://www.mheducation.com/highered/product/shigleys-mechanical-engineering-design-nisbett.html) | Undergraduate-level preload and torque-coefficient treatment and bolt-versus-member stiffness. Its bolted-joint shear section is **bearing/shear, not friction-grip slip** — do not use it for the clamp's slip check. | 2 | B |

## Split clamp, thin-wall crushing, and the support sleeve

The repo added an internal support sleeve because clamping on a 1.5 mm wall is unvalidated and a crushed
root would locally change the second moment of area. That reasoning has mechanics behind it.

| Citation | Link | Why it matters here | Ab | Ev |
|---|---|---|---|---|
| **Campos, U. A.; Hall, D. E. (2019). *Simplified Lamé's equations to determine contact pressure and hoop stress in thin-walled press-fits.* Thin-Walled Structures 138, 199–207.** | [10.1016/j.tws.2019.02.008](https://doi.org/10.1016/j.tws.2019.02.008) | Addresses exactly where classical thick-wall Lamé breaks down for thin walls. This tube is in that regime: **the peer-reviewed justification for not trusting a textbook clamp-pressure formula on the bare tube, and hence for the sleeve.** | 3 | A |
| **DeRuntz, J. A.; Hodge, P. G. (1963). *Crushing of a tube between rigid plates.* J. Appl. Mech. 30(3), 391–395.** | [10.1115/1.3636567](https://doi.org/10.1115/1.3636567) | Canonical plastic-collapse analysis of a thin tube squeezed between flat platens — mechanically the same load case as two clamp halves closing. **Gives the collapse-load scale the seating torque must stay below.** | 3 | A |
| Brazier, L. G. (1927). *On the flexure of thin cylindrical shells and other "thin" sections.* Proc. R. Soc. A 116(773), 104–114. | [10.1098/rspa.1927.0125](https://doi.org/10.1098/rspa.1927.0125) | Ovalization-driven loss of bending stiffness. The repo's stated concern — a crushed root locally changing I — **is** the Brazier mechanism. | 2 | A |
| Wierzbicki, T.; Suh, M. S. (1988). *Indentation of tubes under combined loading.* Int. J. Mech. Sci. 30(3–4), 229–248. | [10.1016/0020-7403(88)90057-4](https://doi.org/10.1016/0020-7403(88)90057-4) | Local denting under a radial indenter **combined with** bending moment: clamp radial load plus tip-mass moment at the same root section. Supports treating crush and bending as interacting, not separate checks. | 2 | A |
| DIN 7190-1:2017-02. *Interference fits — Part 1: calculation and design rules for cylindrical self-locking pressfits.* | [DIN Media](https://www.dinmedia.de/en/standard/din-7190-1/248945061) | Joint pressure to transmissible torque and axial force. A split clamp plus internal sleeve is geometrically a pressfit, and the sleeve changes the diameter ratio the standard uses. | 2 | A |
| Spura, C.; Fleischer, B.; Wittel, H.; Jannasch, D. (2023). *Roloff/Matek Maschinenelemente*, 26th ed. Springer Vieweg. | [10.1007/978-3-658-40914-2](https://doi.org/10.1007/978-3-658-40914-2) | German machine-elements treatment of clamp connections with worked examples: the closest textbook source to "two cross-bolts on a split hub, what torque and axial hold". | 3 | B |
| BS EN 74-1:2022+A1:2025. *Couplers… for use in falsework and scaffolds — couplers for tubes.* | [en-standard.eu](https://www.en-standard.eu/bs-en-74-1-2022-a1-2025-couplers-spigot-pins-and-baseplates-for-use-in-falsework-and-scaffolds-couplers-for-tubes-requirements-and-test-procedures/) | The only adopted standard found governing bolted friction clamps on thin-walled tube. It qualifies them by **slip and distortion test at a specified torque**, not by closed-form crush calculation — precedent that this case is test-validated rather than calculated. | 2 | A |
| Budynas, R. G.; Sadegh, A. M. (2020). *Roark's Formulas for Stress and Strain*, 9th ed. McGraw Hill. | [McGraw Hill](https://www.mheducation.com/highered/mhp/product/roark-s-formulas-stress-strain-9e.html) | Source of the closed-form cantilever cases behind the ±15 % reference, **and** circular-ring diametral-compression cases for a cheap first check on whether seating torque crushes the wall. | 3 | B |

## Element choice for a thin-walled tube

| Citation | Link | Why it matters here | Ab | Ev |
|---|---|---|---|---|
| **Sadowski, A. J.; Rotter, J. M. (2013). *Solid or shell finite elements to model thick cylindrical tubes and shells under global bending.* Int. J. Mech. Sci. 74, 143–153.** | [10.1016/j.ijmecsci.2013.05.008](https://doi.org/10.1016/j.ijmecsci.2013.05.008) | Closest match to this exact question, and it **cuts both ways**: this tube's radius-to-thickness ratio sits below their thin-shell zone, which **supports the solid-element choice** — but equally means any thin-walled approximation inside the hand calculation deserves a check **before it is trusted as the ±15 % reference**. | 3 | A |
| Cifuentes, A. O.; Kalbag, A. (1992). *A performance study of tetrahedral and hexahedral elements in 3-D finite element structural analysis.* Finite Elem. Anal. Des. 12(3–4), 313–318. | [10.1016/0168-874X(92)90040-J](https://doi.org/10.1016/0168-874X(92)90040-J) | Quadratic tets and hexes are equivalent in accuracy and CPU across bending, shear, torsion and axial cases. Independent support that quadratic tets on a 1.5 mm wall are not a compromise. | 3 | A |
| Schneider, T.; Hu, Y.; Gao, X.; Dumas, J.; Zorin, D.; Panozzo, D. (2022). *A large-scale comparison of tetrahedral and hexahedral elements…* ACM TOG 41(3). | [10.1145/3508372](https://doi.org/10.1145/3508372) | Thousands of models: linear tets poor, **quadratic tets match or beat hexes**. Closes the "you should have used hexes" objection with recent data. | 2 | A |
| Benzley, S. E.; Perry, E.; Merkley, K.; Clark, B.; Sjaardama, G. (1995). *A comparison of all hexagonal and all tetrahedral finite element meshes…* 4th Int. Meshing Roundtable. | [PDF](https://coreform.com/papers/hex_tet_comparison.pdf) | The canonical tet-vs-hex bending study on a fixed-end bar, the same problem class as this cantilever. Justifies **quadratic**, not linear, tets. Page range unverified. | 3 | B |
| Cook, R. D.; Malkus, D. S.; Plesha, M. E.; Witt, R. J. (2001). *Concepts and Applications of Finite Element Analysis*, 4th ed. Wiley. | [Wiley](https://www.wiley.com/en-us/Concepts+and+Applications+of+Finite+Element+Analysis,+4th+Edition-p-9780471356059) | Textbook anchor for modelling-error taxonomy, element selection, locking and stress recovery. The year is **2001**, often miscited as 2002. | 2 | B |
| Bathe, K.-J. (2014). *Finite Element Procedures*, 2nd ed. ISBN 978-0-9790049-5-7. | ISBN record | Theory-level backing for energy-norm convergence and locking in bending-dominated thin structures: the formal reason pointwise stress at a singular point need not converge even when displacements do. | 2 | B |

## Tolerance stack-up and GD&T

| Citation | Link | Why it matters here | Ab | Ev |
|---|---|---|---|---|
| ASME Y14.5-2018 (R2024). *Dimensioning and Tolerancing.* | [asme.org](https://www.asme.org/codes-standards/find-codes-standards/y14-5-dimensioning-tolerancing) | Governs how clamp and mast drawings must state datums and orientation tolerances. **The 1.284° / 0.458° / 0.354° tilt budget is meaningless unless contributing features are toleranced to a defined datum reference frame** — and this repo has no drawings yet. | 3 | A |
| ISO 1101:2017. *GPS — geometrical tolerancing…* | [iso.org](https://www.iso.org/standard/66777.html) | The ISO counterpart. **Pick one system and say which**: mixing Y14.5 and ISO GPS defaults silently changes what a tolerance means. | 3 | A |
| Fischer, B. R. (2011). *Mechanical Tolerance Stackup and Analysis*, 2nd ed. CRC. | [Routledge](https://www.routledge.com/Mechanical-Tolerance-Stackup-and-Analysis-Second-Edition/Fischer/p/book/9781439815724) | The practitioner reference for worst-case versus RSS versus statistical stacks, including converting GD&T callouts into contributors. The method book behind what this repo already did. | 3 | B |
| Chase, K. W.; Parkinson, A. R. (1991). *A survey of research in the application of tolerance analysis to the design of mechanical assemblies.* Research in Engineering Design 3(1), 23–37. | [10.1007/BF01580066](https://doi.org/10.1007/BF01580066) | Peer-reviewed framing of worst-case versus statistical methods. Use it to justify **why worst case was the right gate for a blind assembly**. | 3 | A |
| ISO 2768-1:1989. *General tolerances — Part 1.* | [iso.org](https://www.iso.org/standard/7748.html) | Sets the default tolerances that silently feed the stack on every untoleranced machined dimension. **If the drawing block cites it, those values are already in the budget whether or not they were counted.** Part 2 was replaced by ISO 22081:2021. | 2 | A |

## 6061-T6 material basis

| Citation | Link | Why it matters here | Ab | Ev |
|---|---|---|---|---|
| **EN 10204:2004. *Metallic products — types of inspection documents.*** | [CEN catalogue](https://standards.iteh.ai/catalog/standards/cen/541961b2-83a5-4190-a21e-97d523a891e0/en-10204-2004) | **This is the "handbook value is not a mill certificate" citation.** A Type 3.1 certificate reports tests on **your** material by an inspector independent of manufacturing. Handbook values are population typicals; ASTM specs are guaranteed minima; only this documents what was actually bought. | 3 | A |
| MMPDS-2026, *Metallic Materials Properties Development and Standardization Handbook, Vol. I.* | [mmpds.org](https://www.mmpds.org/) | The only source of **statistically based** design allowables (A- and B-basis) for 6061-T6 by product form and thickness. The citable source if a real margin statement is ever needed. Paywalled. | 3 | A |
| ASM International (1990). *ASM Handbook, Vol. 2: Properties and Selection: Nonferrous Alloys…* | [10.31399/asm.hb.v02.9781627081627](https://doi.org/10.31399/asm.hb.v02.9781627081627) | The standard citable handbook for modulus, density and typical mechanical properties. **Typical values, not guaranteed minima** — which is exactly why the repo labels them `model_assumption`. | 3 | B |
| ASTM B210/B210M-19a. *…Aluminum-Alloy Drawn Seamless Tubes.* | [ASTM](https://store.astm.org/b0210_b0210m-19a.html) | Guaranteed **minimum** tensile and yield by alloy, temper and wall. The likely product form for 20 mm OD × 1.5 mm wall. | 3 | A |
| ASTM B221-21. *…Extruded Bars, Rods, Wire, Profiles, and Tubes.* | [ASTM](https://store.astm.org/b0221-21.html) | Same role if the tube is extruded rather than drawn. **Pick whichever matches the actual stock and say so.** | 3 | A |
| The Aluminum Association (2020). *Aluminum Design Manual.* | [aluminum.org](https://www.aluminum.org/aluminum-design-manual-2020) | Consensus design-side values for 6061-T6 plus structural design rules. | 2 | B |
| MatWeb, "Aluminum 6061-T6" datasheet. | [asm.matweb.com](https://asm.matweb.com/search/SpecificMaterial.asp?bassnum=ma6061t6) | Widely cited aggregator page with **no traceable provenance and no statistical basis**. Acceptable only as an indicative footnote; **never the authority for a margin.** Page would not load during verification and no number was read from it. | 2 | D |

## What this section changes

1. **The mesh study is a bare delta.** "Under 1.5 % at final refinement" has no observed order of
   convergence and no factor of safety. Celik et al. gives the three-grid recipe that turns it into a
   numerical-uncertainty band.
2. **The singularity exclusion now has a citation.** Sinclair 2019 plus 2016 map one-to-one onto the
   divergence-at-root and convergence-at-gauge scheme already in use.
3. **The validation reference is the least-scrutinised link.** Sadowski & Rotter imply the thin-walled
   assumption inside the hand calculation should be checked before it carries the ±15 % criterion.
4. **The clamp bolt calculation is still absent**, and VDI 2230 plus the free ECSS handbook define what it
   must contain. Seating torque is not preload.
5. **The tolerance budget needs drawings with a datum reference frame** before its numbers mean anything.

## Not verified, deliberately absent

- **No clause numbers are quoted from VDI 2230, ISO 898-1, ISO 16047, ISO 1101, ISO 2768, ASME Y14.5, MMPDS
  or the ASTM specs.** All paywalled; designation, title, edition and scope verified from official or mirror
  listings only. In particular the claim that VDI 2230 covers frictional transmission of transverse load
  **could not be verified** — use the free ECSS or RCSC sources for slip algebra.
- **`iso.org` returns HTTP 403 to automated fetch**; ISO items were confirmed through catalogue listings plus
  independent mirrors. Re-check in a browser before publication.
- **Oberkampf & Roy 2nd edition (2025)**: title change, ISBN and DOI came from search listings only; Cambridge
  returned errors. The 1st edition is fully verified — cite that unless the 2nd can be confirmed.
- **Bickford**: cite by DOI; two ISBNs circulate and the edition/publisher line comes from retailer records.
- **Benzley et al. page range** widely quoted as 179–191, but the verified PDF carries no page numbers. Omitted.
- **NAFEMS singularity guidance**: the older modelling guides are archived by NAFEMS with an explicit note that
  they no longer represent best practice. No current NAFEMS publication specifically on re-entrant-corner
  singularities was found.
- **ASME BPVC VIII-2 Annex 5-A stress linearization**: real but paywalled and arguably out of scope for a
  cantilever tube rather than a pressure boundary. Use ASME V&V 10 instead.
- **No standard or handbook mandates a minimum wall thickness or an internal sleeve when clamping thin-walled
  tube.** Searches returned vendor pages and forum practice only. **Argue the sleeve from mechanics, and validate
  it by a seating-torque and slip test — do not present it as a code requirement.**
- **No peer-reviewed paper on split-clamp torque capacity from bolt preload** was located; only vendor
  calculators, which are not citable. Roloff/Matek is the best available.
- **ISO 2768 "Edition 2, 2026"** is claimed by a commercial blog only. **Unverified.** The 1989 edition is confirmed current.
