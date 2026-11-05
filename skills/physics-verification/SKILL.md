---
name: physics-verification
description: Design and report physical invariants, convergence studies, sampling uncertainty, and CPU or GPU correctness checks for physics research.
---

# Physics verification

Declare checks before execution: observable, units, reference quality, expected invariant, error norm, tolerances, refinement sequence, and stopping criteria. Separate model error, discretization/truncation error, iterative error, sampling error, and roundoff. Reuse `numerical-verification` for numerical accuracy and `cuda-computing` for device/timing checks.

| Model | Required evidence where applicable |
|---|---|
| Mechanics | Analytic limit, timestep convergence, relevant conserved quantities, constraint residuals |
| MD | Force checks, NVE refinement, restart continuity, sampling diagnostics, finite-size effects |
| Electronic structure | SCF outcome plus basis/cutoff/k-point convergence and force checks |
| Quantum dynamics | Normalization, trace/positivity, analytic small system, basis/time refinement |
| Tensor networks | Small exact reference, bond-dimension/truncation and finite-size studies |
| Transport | Channel count, clean-system reference, conservation/scattering diagnostics |
| Phonons | Force/displacement convergence, translational/acoustic diagnostics |

Use synthetic deterministic fixtures for acceptance. A package import or short trajectory is functional evidence, not a scientific result. Thermostats, driving, dissipation, and boundaries change which invariants apply. Stochastic checks require justified statistical criteria; do not impose deterministic pointwise trajectory agreement.

For GPU comparisons check actual backend/device identity and precision. Compare physical quantities against a CPU/reference result with declared tolerances. Synchronize timed work; separate compilation, warmup, transfers, kernels, and full-run time. Container wall time is not a GPU kernel time or proof of speedup.

Preserve inputs, executed source, environment locks, force-field/pseudopotential hashes and licenses, seeds, diagnostics, failed runs, observables, uncertainties, and limitations. Verification of stored hashes establishes integrity only. Overall acceptance fails if a required profile or scientific check fails.

Follow AGENTS.md; no automatic external services, account changes, or paid compute.
