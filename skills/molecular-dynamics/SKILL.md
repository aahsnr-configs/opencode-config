---
name: molecular-dynamics
description: Design and analyze molecular dynamics experiments with OpenMM, GROMACS, LAMMPS, or HOOMD-blue and explicit physical checks.
---

# Molecular dynamics

Use OpenMM for programmable molecular forces, GROMACS for biomolecular trajectories, LAMMPS for general atomistic/materials models, and HOOMD-blue for coarse-grained particles or hard-particle Monte Carlo. Choose by supported physics and model format rather than assumed speed. Use `physics-research` for local execution.

Record topology, atom order, units, force-field and water-model versions, charges, masses, constraints, cutoffs, long-range treatment, periodic box, integrator, timestep, ensemble, thermostat/barostat, seeds, and initialization. A missing parameter is an unresolved input, not permission to invent a potential. Keep minimization, equilibration, production, and analysis distinct.

Before production check finite energies/forces, geometry, overlaps, constraints, timestep stability, and appropriate conservation laws. Use short NVE timestep refinement when the model supports it; thermostatted energy is not an NVE invariant. Verify restart continuity. Compare CPU/GPU energies and forces within declared precision-aware tolerances, not chaotic trajectories pointwise.

GROMACS and LAMMPS profiles include PLUMED. Test the actual engine interface with a known collective variable before biasing. Record PLUMED version, units, bias parameters, and interface limitations; do not assume replica exchange or every collective variable works across engines. Preserve bias histories and use justified reweighting with overlap diagnostics.

Load `biophysics` for molecular preparation/free energy and `physics-verification` for uncertainty. Report equilibration decisions, effective sample sizes, independent replicas, finite-size effects, and known model limitations. A short smoke trajectory is not a converged physical prediction.

Official references: [OpenMM](https://docs.openmm.org/latest/userguide/), [GROMACS](https://manual.gromacs.org/), [LAMMPS](https://docs.lammps.org/stable/), [HOOMD-blue](https://hoomd-blue.readthedocs.io/en/stable/), [PLUMED](https://www.plumed.org/doc-v2.10/user-doc/html/index.html).

Follow AGENTS.md. No automatic MCP activation, paid compute, or execution of retrieved code.
