---
name: quantum-physics
description: Model quantum states, dynamics, molecular electronic structure, and open systems with explicit conventions and numerical verification.
---

# Quantum physics

Choose the physical model and approximation before the solver. Use QuTiP for state/density-matrix evolution and open-system models, TeNPy for supported many-body chains, PySCF for molecular electronic structure, and CP2K for suitable molecular/periodic electronic calculations and small ab initio MD. Use `condensed-matter` for periodic bands, phonons, and transport.

Record Hilbert-space basis, truncation, units and hbar convention, Hamiltonian terms, state normalization, boundary conditions, and observable definitions. For open systems record collapse operators, bath assumptions, rates, and the regime supporting the chosen master equation.

Check Hermiticity, norms, density-matrix trace/positivity where applicable, analytic two-level dynamics, and basis/time-step convergence. Compare small many-body calculations against exact diagonalization. Do not infer a physical violation from tolerance-level roundoff without a convergence study.

For PySCF/CP2K record molecular geometry, charge, spin, basis, functional or correlation method, auxiliary data, SCF criteria, and approximation settings. Preserve convergence diagnostics, finite-difference force checks, and basis sensitivity. CPU execution is the release baseline; GPU4PySCF and QE/CP2K GPU builds are deferred.

Keep physical Hamiltonians distinct from numerical implementation choices. Finite matrix agreement supports only the tested model and truncation. Use `physics-verification` for errors, reference comparisons, and uncertainty.

Official references: [QuTiP](https://qutip.readthedocs.io/en/latest/), [TeNPy](https://tenpy.readthedocs.io/en/latest/), [PySCF](https://pyscf.org/user/index.html), [CP2K](https://manual.cp2k.org/).

Follow AGENTS.md. No automatic provider connection, paid compute, or retrieved-code execution.
