---
name: analytical-mechanics
description: Derive and simulate classical, Lagrangian, Hamiltonian, and constrained mechanical models using existing symbolic and numerical environments.
---

# Analytical mechanics

Reuse the existing math runtime: SymPy mechanics for derivation, SciPy/SUNDIALS for ODE/DAE integration, FEniCSx/PETSc/SLEPc for continuum or eigenvalue models. Use the math launcher by absolute path and its explicit state directory; do not duplicate the symbolic/PDE stack.

Declare coordinates, frames, constraints, degrees of freedom, units, kinetic/potential energies, generalized forces, and initial/boundary conditions. Derive Euler–Lagrange equations with explicit constraint handling. Distinguish holonomic constraints, velocity constraints, dissipative forces, and driven systems.

For Hamiltonian work state canonical variables and Poisson-bracket convention. Check the Legendre transform's invertibility; singular Lagrangians need constraint analysis. Derive canonical equations and applicable conserved quantities. A cyclic coordinate or time symmetry supports conservation only under the model's assumptions.

Verify pendulum equations and the small-angle limit. Check harmonic oscillator order under timestep refinement and Kepler angular momentum. Compare a symplectic method's long-time energy behavior against the intended Hamiltonian; exact energy conservation is not guaranteed by symplecticity. For constrained DAEs monitor constraint residuals and consistent initialization.

For continuum mechanics preserve weak form, constitutive assumptions, mesh, boundary data, units, and manufactured/reference solutions. Load `numerical-pde`, `differential-equations`, or `numerical-verification` as needed. Use fresh `research/physics/` output paths even when invoking the math launcher.

Official reference: [SymPy Lagrange mechanics](https://docs.sympy.org/latest/modules/physics/mechanics/lagrange.html).

Follow AGENTS.md; symbolic identities under assumptions, numerical evidence, and proof are different outcomes.
