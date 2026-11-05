---
name: biophysics
description: Prepare and analyze biomolecular simulations, conformational observables, and free-energy calculations with explicit molecular assumptions.
---

# Biophysics

Use existing life sciences skills to resolve identifiers, sequences, structures, ligands, and source provenance. Distinguish experimental structures from predictions. Preserve accession/version, chain selection, missing regions, mutations, cofactors, alternate conformations, and experimental conditions.

Use the preparation profile for OpenFF Toolkit and RDKit. AmberTools is not included; workflows that require its charge or topology tools must report that dependency as unavailable. Declare protonation/tautomer states, stereochemistry, residue treatment, charge method, solvent/ions, force-field versions, and water model. Verify atom mappings, formal/net charge, topology consistency, and complete parameters. Never silently substitute a force field, charge method, or commercial toolkit.

Use `molecular-dynamics` for simulation setup and validation. Analyze copied trajectories with MDAnalysis; handle periodic wrapping, molecular reconstruction, alignment, selections, and units explicitly. Define RMSD/RMSF, contacts, distances, correlation functions, or experimental observables before inspecting outcomes.

For free energy use pymbar with documented thermodynamic states, reduced potentials, equilibration removal, statistical inefficiency, overlap, effective samples, and uncertainty. Poor overlap or inadequate independent samples blocks a reliable estimate. Preserve failed windows and independent replicas; uncertainty must reflect correlation.

Separate simulation observables from biological or clinical claims. State force-field bias, sampling limits, finite-size effects, and experimental comparison conditions. Use `physics-verification` for checks and reproducibility.

Official references: [OpenFF Toolkit](https://docs.openforcefield.org/projects/toolkit/en/stable/), [Amber](https://ambermd.org/), [MDAnalysis](https://www.mdanalysis.org/documentation/), [pymbar timeseries](https://pymbar.readthedocs.io/en/latest/timeseries.html).

Follow AGENTS.md; this skill grants no external job, assay, account, or MCP authorization.
