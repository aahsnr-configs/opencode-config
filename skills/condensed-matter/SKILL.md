---
name: condensed-matter
description: Research crystalline materials, electronic bands, phonons, quantum transport, and correlated lattice models with convergence checks.
---

# Condensed matter

Choose the model class first: classical potential, continuum field, periodic electronic structure, tight binding, or correlated lattice Hamiltonian. Use LAMMPS/HOOMD-blue for suitable particle models, Quantum ESPRESSO for periodic electronic structure, Kwant for transport, and TeNPy for supported tensor-network models. Reuse existing PDE and sparse eigensolver environments for continuum or explicit matrix models.

Use ASE, pymatgen, spglib, and seekpath for structures, symmetry, and reciprocal paths. Record cell convention, coordinates, units, occupancy, periodicity, symmetry tolerance, reciprocal convention, and spin. A symmetry label depends on the declared tolerance.

For DFT record functional, pseudopotential source/hash/license, valence treatment, cutoff, k-point mesh, smearing, spin, charge, and convergence thresholds. Test cutoff/k-point/cell-size sensitivity for the requested observable. SCF convergence alone does not establish a converged material property. QE runs are CPU-based in this release.

Use Phonopy for finite-displacement workflows with recorded supercell, displacement amplitude, force calculator, and acoustic sum-rule treatment. Inspect force convergence and translational modes; an imaginary mode may require physical interpretation or further convergence checks.

For Kwant declare basis, hoppings, onsite terms, leads, boundary conditions, energy convention, and propagating channels. Test clean-chain transmission and scattering conservation before disorder studies.

For TeNPy compare small chains against exact diagonalization; track bond dimension, truncation error, sweeps, finite size, symmetries, and boundary conditions. State method applicability instead of assuming arbitrary two-dimensional strongly correlated systems are tractable.

Official references: [ASE](https://docs.ase-lib.org/), [Quantum ESPRESSO](https://www.quantum-espresso.org/documentation/), [Phonopy](https://phonopy.github.io/phonopy/interfaces.html), [Kwant](https://www.kwant-project.org/doc/), [TeNPy](https://tenpy.readthedocs.io/en/latest/).

Use `physics-research` and `physics-verification`; follow AGENTS.md and explicit MCP rules.
