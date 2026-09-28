# 01 — The engineering, from first principles

Every number here is derived, then checked against the repo's committed value. If you can reproduce this
page on a whiteboard you can defend any quantity in the mechanical lane.

Notation: `E` Young's modulus, `I` second moment of area, `L` length, `k` stiffness, `F` force,
`δ` deflection, `m` mass, `f₁` first natural frequency.

---

## 1. Section properties — why the annulus formula is exact

A hollow round tube, outside diameter `OD`, wall `t`, so inside diameter `ID = OD − 2t`.

The second moment of area about a diameter, for a solid circle of diameter `D`, is `πD⁴/64`. Because the
second moment is an integral of `y²` over area, and the bore is a concentric circle, you can **subtract**
the hole's contribution directly:

```
I = π/64 · (OD⁴ − ID⁴)
```

For the mast: `OD = 20`, `t = 1.5`, so `ID = 17` mm.

```
I = π/64 · (20⁴ − 17⁴) = π/64 · (160 000 − 83 521) = π/64 · 76 479 = 3754.154 mm⁴
```

Repo: `3754.1541 mm⁴` from `cad/fixture_feasibility.py::second_moment_mm4`. ✓

**Why this matters for an interview.** There is a common thin-wall approximation, `I ≈ πD³t/8`, which
would give `π·20³·1.5/8 = 4712 mm⁴` — 25 % high. The repo uses the exact form. An earlier audit note
speculated the thin-wall approximation might be the source of a modelling gap; checking the source showed
it was not, because the exact formula was already in use. **Knowing which approximation you did *not*
make is part of defending the number.**

---

## 2. Cantilever stiffness — where `3EI/L³` comes from

Euler–Bernoulli: for a beam, `EI · d²y/dx² = M(x)`. A cantilever fixed at `x = 0` with a transverse point
load `F` at the free end `x = L` has an internal moment `M(x) = −F(L − x)`.

Integrate twice with `y(0) = 0` and `y′(0) = 0` (built-in root: no displacement, no rotation):

```
EI · y″ = −F(L − x)
EI · y′ = −F(Lx − x²/2)
EI · y  = −F(Lx²/2 − x³/6)
```

At `x = L`: `y(L) = −FL³/(3EI)`. Magnitude of tip deflection `δ = FL³/(3EI)`, so

```
k = F/δ = 3EI/L³
```

For the mast, `E = 68 900 N/mm²` (6061-T6 handbook), `I = 3754.154 mm⁴`, `L = 100 mm`:

```
k = 3 · 68 900 · 3754.154 / 100³ = 775.984 N/mm
```

Repo: `775.9837 N/mm`. ✓ Compliance is the reciprocal, `1/k = 1.2887 µm/N`.

**The assumption you are making**, and must be able to name: a built-in root with zero rotation, no shear
deformation, no rotary inertia, and small deflections. Every one of those is violated to some degree in
the real thing. Sections 4 and 6 are about how much.

---

## 3. Rayleigh's method — and why it gives an upper bound

You want the first bending frequency of a tube carrying a tip mass. Exact solution needs the beam's
partial differential equation; Rayleigh gets you close with energy.

**The idea.** Assume a deflection shape. Equate peak kinetic energy to peak strain energy over a cycle.
If the assumed shape is not the true mode shape, you have effectively added a constraint to the system,
and constraining a structure can only **raise** its frequency. So

> Rayleigh's estimate is always ≥ the true first frequency. It is a rigorous upper bound.

Using the static deflection shape of a tip-loaded cantilever, the beam's distributed mass contributes an
equivalent tip mass of `33/140 ≈ 0.2357` of the beam mass — the repo uses `0.23`. So

```
m_eff = m_tip + 0.23 · m_beam
f₁ = (1/2π) · √(k / m_eff)
```

Mast beam mass is 23.5 g, tip mass 175 g, so `m_eff ≈ 0.175 + 0.23·0.0235 ≈ 0.1804 kg`, and with
`k = 775 984 N/m`:

```
f₁ = (1/2π)·√(775 984 / 0.1804) ≈ 330 Hz
```

Repo hand calculation: **330.1 Hz**. ✓

**The trap to avoid.** A bound only brackets another number if both describe *the same problem* — same
mass model, same boundary conditions, same kinematics. The repo originally argued the true frequency was
bracketed between this Rayleigh upper bound and a Dunkerley lower bound. That argument was **withdrawn**,
because the FE model turned out not to be the same problem (section 4). Do not resurrect it.

---

## 4. Why the FEA came out lower — and the part that was a modelling artifact

The FE model gave **285.5 Hz** against the hand calculation's 330.1 Hz: −13.5 %. For a long time the repo
attributed that to shear deformation, rotary inertia, tip-mass extent and root flexibility.

**Two of those attributions were wrong**, and finding out why is the best engineering story in the repo.

An audit of the actual solver deck found:

- **Both** models fix the root. The FE deck constrains all three translations at the root node set. So
  root flexibility cannot explain a difference *between these two models* — neither contains it.
- The deck carries a **one-node translational point mass**. So tip-mass rotary inertia is not in the
  model either.
- Worse: the tube is hollow, so there is no material node on its axis. The mass was attached to the
  **nearest existing node — about 8.5 mm off-axis on the inner wall**, with no coupling to the tip
  section.

That last one is a genuine defect, not just a mislabel. A controlled three-case comparison was run, one
mesh, one material, one root constraint, changing only the attachment:

| Case | Definition | f₁ |
|---|---|---|
| A | single node on the off-axis wall (historical) | 285.51 Hz |
| B | same position, rigidly coupled to the tip plane | 316.84 Hz |
| C | on the axis, identical coupling | 320.87 Hz |

- **A → B: +10.97 %** — the attachment model, position held fixed.
- **B → C: +1.27 %** — position, attachment model held fixed.

**The attachment model, not the eccentricity, was the dominant artifact** — about nine times the effect.
Comparing A against C alone gives +12.4 % and would have been misread as "the eccentricity effect" while
changing two things at once. This is why you always vary one factor at a time.

An independent check that the coupling does what it claims: the orthogonal bending pair splits by
**15.82 Hz** in case A and **0.004 Hz** in case C. A centred mass on an axisymmetric tube *must* give a
degenerate pair, and it does. That confirmation comes from a direction the frequencies themselves cannot
provide.

With the attachment corrected, the model sits **−2.79 %** from the hand calculation instead of −13.5 %.
The residual is the size shear and 3D-versus-beam kinematics would be expected to produce.

**Not adopted.** 320.87 Hz is not a new headline number, because a new coupling invalidates automatic
reuse of the old mesh-convergence evidence. That would need its own refinement study.

### The mechanisms that genuinely remain

- **Shear deformation.** Euler–Bernoulli assumes plane sections stay perpendicular to the axis. At this
  slenderness (`L/r ≈ 15`, where `r` is the radius of gyration) shear is not negligible, and Timoshenko
  beam theory predicts a lower frequency. The shear coefficient for a **thin-walled tube** is materially
  lower than for a solid rod, so the correction is larger than slenderness alone suggests.
- **3D versus 1D kinematics**, including local shell behaviour at the constrained root, which a beam
  model cannot represent at all.

---

## 5. The modal guard — and why its basis does not hold

The acceptance criterion was `f₁ ≥ 200 Hz`: clear the 100 Hz control update rate *and* "a plausible
low-hundreds-Hz motor/drivetrain excitation band" by a factor of 2. **This drove the entire redesign**
from a 120 mm × 16 mm tube (174.7 Hz, failed) to 100 mm × 20 mm.

The control-rate half is a real requirement. The motor half cites **no frequency anywhere in the repo** —
the word is "plausible". But the drivetrain numbers were already in the repo:

Motor speed at 10 m/s is 20 600 rpm. First-order shaft frequency is just revolutions per second:

```
f_shaft = 20 600 / 60 = 343.3 Hz
```

Compare that to the mast's 285.5 Hz first mode. **The excitation is above the mode, not below it.** Since
shaft frequency scales linearly with road speed, it passes *through* the mast resonance at

```
v = 10 · 285.5 / 343.3 = 8.32 m/s
```

which is inside the 10 m/s operating envelope. The 200 Hz guard itself is crossed at 5.83 m/s.

So the criterion assumed the band sat below the mode and had to be cleared upward; the drivetrain puts
first order above it, sweeping up through the resonance during acceleration.

**What this does not show.** That the mast is inadequate. Whether a swept-through resonance matters
depends on rotor unbalance, the motor-to-deck transmission path and damping — none of which is recorded.
This bounds frequencies only and makes **no amplitude claim**. What it establishes is that the
criterion's justification is absent.

---

## 6. The compliance measurement — and the error that hides from every gate

The planned physical test loads the mast tip at 4, 8, 12, 16, 20 N, two axes, three load/unload cycles,
and fits **compliance** as the slope of displacement against force.

### Why a slope, and why a difference

The observable is `(tip reading − fixture reading)` against measured force. Subtracting the fixture
reading removes rigid translation of the whole fixture. Fitting a slope rather than dividing at one point
uses all the data and makes the intercept absorb any zero offset.

Consequence worth knowing: **root quantization enters the budget twice**, once through each reading.

### The signal is tiny

At the FEA compliance of `0.001366884 mm/N`, full scale is

```
δ(20 N) = 20 × 0.001366884 = 0.0273 mm = 27.3 µm
```

and at the bottom of the range, using the hand compliance, `δ(4 N) = 4 × 1.2887 = 5.15 µm`.

Five micrometres. That is the number that makes this test hard.

### Quantization, and why √12

An indicator reading in steps of `q` has a rounding error uniformly distributed on `[−q/2, +q/2]`. The
variance of a uniform distribution of width `q` is `q²/12`, so the standard uncertainty is

```
u = q/√12 ≈ 0.289 q
```

At `q = 1 µm` that is 0.289 µm per reading. Two independent readings differenced give
`√2 × 0.289 = 0.409 µm`.

### Root rotation — the error no gate catches

If the root rotates by `θ`, the tip moves by `θ · L` **in addition** to the beam bending. At
`θ = 50 µrad` and `L = 100 mm`:

```
θ·L = 50e-6 × 100 mm = 5 µm
```

which is the **entire 4 N signal**. Worse, if the rotation is proportional to load — which it will be for
an elastic joint — it adds a constant amount to the *slope*, and a straight line plus a straight line is
still a straight line.

A simulated case makes the consequence concrete: an uncorrected 0.00025 mm/N root rotation produces a
**19.4 % slope error** while median R² is 0.9947 and relative expanded uncertainty is 3.3 %. **Both frozen
numerical gates pass and the answer is 19 % wrong.**

This is the single most important thing to understand about the measurement: **linearity and repeatability
cannot detect a load-proportional bias.** Root-motion observability is a correctness requirement on the
apparatus, not a refinement. The two root stations exist for this reason: spaced `s` apart with resolution
`q`, they observe rotation with uncertainty

```
u_θ = √2 · (q/√12) / s
```

At `q = 1 µm`, `s = 100 mm`: `u_θ = 4.08 µrad`, which at the 100 mm lever is 0.408 µm. A wider baseline
observes rotation better — which is why station spacing turns out to matter more than raw repeatability.

### Why the fixture must be ten times stiffer

The fixture sits in series with the specimen. Two springs in series share load, so the measured
compliance is the sum. If the fixture is `n` times stiffer than the specimen, it contributes `1/n` of the
specimen's compliance — a `1/n` fractional error before any correction. At `n = 10` that is 10 %, which is
why the screen is a **screen** and the fixture motion is also *subtracted* rather than merely bounded.

```
k_fixture ≥ 10 · k_specimen = 10 × 775.984 = 7759.84 N/mm per axis
```

Note what this does **not** constrain: rotation. A fixture can be enormously stiff in translation and
still rotate at the root.

---

## 7. Uncertainty — the two ideas that matter most

### Shared errors do not average away

Split every error by its **scope**:

- **Per reading** — readout noise, quantization, repeatability. Average `N` of them and the contribution
  falls as `1/√N`.
- **Shared across the campaign** — the force channel's calibration gain, one gravity value, the ambient
  environment. These are drawn **once**. Repeating readings does not reduce them at all.

A calibration gain error scales every force by the same factor, so it scales the fitted slope by that
factor. No number of cycles touches it. This is why a calibration *record* is requested rather than
estimated from repeats, and why the two axes of the campaign are not independent — one calibration serves
both, so you may not multiply per-axis pass probabilities.

### A coverage factor is not automatically 2

Expanded uncertainty `U = k · u`. The convenient `k = 2` is only right when the output distribution is
near-normal with many effective degrees of freedom. For a five-point fit it is not: `k` should come from
Student's *t* at the effective degrees of freedom. The repo's calibration tool reads a *t* table rather
than assuming 2 — and honestly records that its input is the *fit's* degrees of freedom, not a
Welch–Satterthwaite effective value per component. That distinction is worth being able to state.

### Errors in both variables

In the calibration, applied force carries mass and gravity uncertainty; counts carry noise. Ordinary
least squares assumes the x-values are exact. When they are not, the fitted slope is **attenuated toward
zero** by roughly `S_xx/(S_xx + N·σ_x²)`.

So the calibration uses an errors-in-variables fit. **But state the scope honestly**: attenuation depends
on the error model and its size, and at the ADC's expected noise the two estimators agree to within
0.1 %. The case for the better estimator is that nothing guarantees the noise stays small — not that
ordinary least squares is always wrong.

### Why R² is a weak gate

The frozen protocol marks a run inconclusive if R² < 0.99. Two problems:

1. The analytical-chemistry literature discourages the correlation coefficient as *the* calibration
   metric: a value near 1 is compatible with visible curvature.
2. It is not reliable even on its own terms. At an assumed 0.3 µm repeatability the **median** R² passes
   at 0.9925 while roughly **one simulated campaign in seven is rejected**, and about one two-axis
   campaign in four fails on at least one axis. A passing median is not campaign reliability.

The replacement is not simply another p-value: non-rejection of lack-of-fit does not prove adequacy when
power is low. It needs a practical tolerance for consequential departure, residual diagnostics, and a
declared detection power.

---

## 8. The vehicle lane — the one derivation that matters

### The single-track model and cornering stiffness

Collapse each axle to one wheel. At small slip angles, a tire's lateral force is roughly linear in slip
angle:

```
F_y = C_α · α
```

`C_α` is the **cornering stiffness**: the slope of the lateral-force curve near zero slip. The repo
identifies `C_Sf` and `C_Sr`, the front and rear values, by bounded nonlinear least squares against
simulator telemetry.

What you discard by using a single linear coefficient: the curve **saturates**, and `C_α` itself depends
on vertical load, so a single scalar is valid only near zero slip and near the load it was fitted at.

### Why 100 % VAF is a tautology, not a result

The identification recovers `C_Sf = 4.718` and `C_Sr = 5.4562` with relative errors around
5 × 10⁻¹⁰, and 100.000000000 % variance-accounted-for on a held-out rollout.

**Understand exactly why.** The data were generated by the same model structure the estimator fits. There
is no model error, no measurement noise, no unmodelled dynamics. So the estimator is being asked to
recover numbers that are exactly present in the data. Getting them back to 1e-10 shows the optimizer and
the plumbing are correct. It says **nothing** about a real tire.

The standard reference makes the general point: fitting a model to data generated by that same model
structure validates the estimator, not the model. That framing is your friend — it converts what looks
like an overclaim into evidence of judgement.

### The controller result

One track, fixed seeds, 100 Hz update rate:

| Controller | RMS cross-track error | Lap time |
|---|---|---|
| Pure pursuit | **0.158 m** | 38.04 s |
| MPC | 0.169 m | 37.86 s |
| LQR | 0.179 m | 38.06 s |

Pure pursuit wins on tracking. MPC edges lap time and reports a p95 solve of 1.33 ms.

**Why this is plausible rather than embarrassing.** On a nominal plant with no disturbance and no
constraint activity, there is nothing for the optimizer to buy you: the geometric law is already near the
achievable error, and the optimizer's cost function is a proxy you chose, not the metric being scored.
MPC's real value is explicit constraint satisfaction and a bounded runtime — which is exactly what the
repo claims for it, and nothing more.

**Where it gets challenged**, and you should raise it yourself: on real F1TENTH hardware at up to 11 m/s, a
published result has a model-aware pursuit controller beating plain geometric pure pursuit by roughly 4×
on lateral error. Your result is scoped to a nominal plant and a modest speed regime. The planned
mismatched-plant sweep — varying wheelbase, mass, friction and command delay — is the right next test,
because theory says a certainty-equivalent optimal controller degrades under model error while a simpler
law may not.
